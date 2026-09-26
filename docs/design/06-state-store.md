# State store

Version 0.1 · 2026-09-26 · Architectural requirement confirmed by Garmit; schema details proposed

## 1. Purpose

A single local store records the state of every pipeline run:
- which stage is running or finished;
- what each stage consumed and produced;
- every model call and its cost.

It enables:
- **Checks between stages:** a stage runs only when its declared inputs exist and their hashes match.
- **Resume:** stages that already succeeded with identical inputs are skipped. Uncertain paid calls are never re-sent automatically.
- **Audit and evaluation:** the evaluator and reports read lineage from the store instead of reconstructing it.
- **Observability (stretch goal):** runs, stages and model calls map to traces and spans without schema changes.

## 2. Technology and setup

- **SQLite** through Python's standard-library `sqlite3`. Nothing to install and no server.
- **Default path:** `runs/state.db` (gitignored), overridable with `ADGEN_STATE_DB`.
- **Automatic setup:** the pipeline creates the file and applies the schema on first use. `adgen state init` does this explicitly.
- **Settings:** WAL journal mode, `foreign_keys=ON`, a single writer process. The per-run lock is the `run.lock_owner` column plus SQLite transactions.
- **Migrations:** `schema_version` table and numbered SQL migrations in `src/adgen/state/migrations/`. The applied version is checked at start-up; an unknown newer version refuses to run.
- **Inspection:** `adgen state show <run_id>` prints stages, artifacts, calls and cost. The file can also be opened with any SQLite browser.

README setup for another user: clone → install dependencies → copy `.env.example` to `.env` and add their own keys → run the pipeline. The database is created automatically.

## 3. Schema

```sql
CREATE TABLE schema_version (
  version      INTEGER PRIMARY KEY,
  applied_at   TEXT NOT NULL                      -- ISO-8601 UTC
);

CREATE TABLE run (
  run_id            TEXT PRIMARY KEY,             -- ULID
  request_id        TEXT NOT NULL,                -- human label, not identity
  request_sha256    TEXT NOT NULL,                -- canonical AdRequest JSON
  pipeline_version  TEXT NOT NULL,
  config_sha256     TEXT NOT NULL,                -- models, efforts, timeouts, template/policy versions
  mode              TEXT NOT NULL CHECK (mode IN ('live','replay')),
  status            TEXT NOT NULL CHECK (status IN
                      ('pending','running','succeeded','failed','blocked')),
  current_stage     TEXT,
  terminal_reason   TEXT,                         -- e.g. invalid_text_plan, provider_failed, generated_unscored
  guardrail_status  TEXT CHECK (guardrail_status IN
                      ('approved','approved_after_replan','rejected_after_replan')),
  budget_cap_usd    REAL NOT NULL,
  cost_est_usd      REAL NOT NULL DEFAULT 0,
  cost_unknown      INTEGER NOT NULL DEFAULT 0,   -- 1 if any call outcome is unknown
  lock_owner        TEXT,
  created_at        TEXT NOT NULL,
  updated_at        TEXT NOT NULL
);

CREATE TABLE stage_execution (
  exec_id           TEXT PRIMARY KEY,
  run_id            TEXT NOT NULL REFERENCES run(run_id),
  stage             TEXT NOT NULL CHECK (stage IN
                      ('intake','product_analysis','copy_selection','context_resolution',
                       'creative_planning','plan_guardrails','prompt_compilation',
                       'image_generation','output_gate')),
  attempt           INTEGER NOT NULL,             -- creative_planning / plan_guardrails: 1 or 2
  status            TEXT NOT NULL CHECK (status IN
                      ('pending','running','succeeded','failed','skipped','blocked')),
  input_hashes      TEXT NOT NULL,                -- JSON {artifact_kind: sha256}
  input_fingerprint TEXT NOT NULL,                -- sha256 of stage + input_hashes + stage config
  reused_from       TEXT REFERENCES stage_execution(exec_id),  -- cache/resume hit
  error_code        TEXT,
  error_detail      TEXT,                         -- never contains credentials
  started_at        TEXT,
  ended_at          TEXT,
  UNIQUE (run_id, stage, attempt)
);

CREATE TABLE artifact (
  artifact_id       TEXT PRIMARY KEY,             -- sha256 of bytes
  kind              TEXT NOT NULL CHECK (kind IN
                      ('request','reference_original','reference_rendition','product_profile',
                       'source_contract','text_plan','resolved_context','creative_plan',
                       'guardrail_review','prompt','image','provider_receipt')),
  schema_version    TEXT,
  path              TEXT NOT NULL,                -- relative to repo/runs root
  bytes             INTEGER NOT NULL,
  provenance        TEXT NOT NULL CHECK (provenance IN
                      ('code','model','human_supplied','external')),
  created_at        TEXT NOT NULL
);

CREATE TABLE stage_artifact (                     -- lineage: which exec read/wrote which artifact
  exec_id           TEXT NOT NULL REFERENCES stage_execution(exec_id),
  artifact_id       TEXT NOT NULL REFERENCES artifact(artifact_id),
  direction         TEXT NOT NULL CHECK (direction IN ('input','output')),
  PRIMARY KEY (exec_id, artifact_id, direction)
);

CREATE TABLE model_call (
  call_id             TEXT PRIMARY KEY,
  exec_id             TEXT NOT NULL REFERENCES stage_execution(exec_id),
  provider            TEXT NOT NULL CHECK (provider IN ('openai','google','replay')),
  model_requested     TEXT NOT NULL,
  model_returned      TEXT,
  purpose             TEXT NOT NULL,              -- product_analysis, extract, plan, review, image
  prompt_sha256       TEXT NOT NULL,
  request_path        TEXT NOT NULL,              -- recorded request (no credentials)
  response_path       TEXT,
  status              TEXT NOT NULL CHECK (status IN
                        ('dispatched','succeeded','failed','refused','unknown')),
  provider_request_id TEXT,
  sdk_version         TEXT,
  dispatched_at       TEXT NOT NULL,              -- written BEFORE the network send
  completed_at        TEXT,
  latency_ms          INTEGER,
  input_tokens        INTEGER,
  output_tokens       INTEGER,
  reasoning_tokens    INTEGER,
  image_count         INTEGER,
  est_cost_usd        REAL,
  error_code          TEXT
);

CREATE TABLE event (                              -- append-only
  seq          INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id       TEXT NOT NULL REFERENCES run(run_id),
  exec_id      TEXT REFERENCES stage_execution(exec_id),
  ts           TEXT NOT NULL,
  type         TEXT NOT NULL,                     -- run_started, stage_started, stage_succeeded,
                                                  -- stage_failed, call_dispatched, call_completed,
                                                  -- guardrail_rejected, replan_started, budget_blocked, ...
  payload      TEXT NOT NULL                      -- JSON; schema per type; no secrets
);

CREATE INDEX idx_exec_run      ON stage_execution(run_id, stage);
CREATE INDEX idx_exec_fp       ON stage_execution(input_fingerprint, status);
CREATE INDEX idx_call_exec     ON model_call(exec_id);
CREATE INDEX idx_event_run     ON event(run_id, seq);
```

Artifact payload schemas (ProductProfile, TextPlan, CreativePlan, and so on) are Pydantic models with explicit `schema_version`. The store holds hashes and paths; the content lives in the files.

## 4. Rules

1. **Transitions** are written in one transaction with their event: `pending → running → succeeded | failed | blocked`. A stage starts only if every upstream stage it depends on has `succeeded`, or was legitimately `skipped` (for example, extract selection in Exact mode), and the recorded input hashes match the current artifacts.
2. **Resume and cache:** before running, look up a `succeeded` execution with the same `input_fingerprint`. If one exists, create an execution with `reused_from` set and no model call. Product analysis uses this across runs, giving one call per unique reference.
3. **Paid-call safety:** insert `model_call(status='dispatched')` and commit before sending. After a crash, any `dispatched` call with no completion becomes `unknown`, and the run gets `cost_unknown = 1`. The call is not re-sent automatically; a human decides.
4. **Budget:** before each dispatch, check `cost_est_usd` plus the estimated cost of the next call against `budget_cap_usd`. If it would exceed the cap, the run is `blocked` with `budget_blocked`. Estimates come from configured price tables and are labelled as estimates.
5. **Guardrail outcome:** `run.guardrail_status` is set by the plan_guardrails stage and is always carried into the evaluator output.
6. **Replay mode:** `provider='replay'` calls read recorded responses keyed by prompt hash and model. A missing recording fails the stage and never reaches the network.
7. **No secrets:** requests are recorded after credentials are removed. A test scans the database and artifacts for key patterns.
8. **Git:** `runs/` (including `state.db`) is gitignored. Curated demo or golden runs are exported to `data/` as files plus a JSON dump of their store rows.

## 5. Observability mapping (stretch goal)

| Store | OpenTelemetry |
|---|---|
| run | trace (`run_id` → trace attribute), root span |
| stage_execution | child span per stage attempt; status and error_code |
| model_call | child span with GenAI semantic attributes: system, request/response model, token usage |
| event | span events |

An exporter can read the store after a run, or hook the same write path. Neither requires schema changes.
