# Cleanup list for the final submission commit (prepared — nothing removed yet)

Rule (Garmit): the final state keeps the implementation, its inputs, tests, `README.md`, `DESIGN.md`, the coding-agent disclosure (`AI_DECLARATION.md`) and the generated evaluation report. Plans, specs, briefs, checkpoints and agent instructions are removed from the final tree (they stay in Git history; no history rewrite).

**Timing: do not edit anything in `src/`, `config/` or `policy/` while the batch is running.** `scripts/run-batch.sh` starts a new process per request, so edits would change the remaining requests. Do the cleanup after `submission/` is built. Before and after: `ruff check src tests`, `pytest -q`, `adgen demo`.

## 1. Remove

| Path | What it is |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Agent working brief and pointer |
| `docs/context/` (7 files) | Original context bank and requirements given to the agents |
| `docs/design/` (7 files) | Specs v0.1–v0.4 and implementation handoff (superseded by `DESIGN.md`) |
| `docs/generation-implementation-plan.md` | Earlier agent's generation plan |
| `docs/batch-v1-plan.md` | Batch run plan |
| `docs/implementation-status.md` | Agent checkpoint log |
| `examples/` (2 files) | Early example requests, superseded by `data/requests/batch-v1/` |
| `data/requests/batch-v1-unused/` (11 files) | Requests parked when the batch was reduced; never run |
| `docs/cleanup-candidates.md` | This list (remove last) |

## 2. Use as source material, then remove

| Path | Carry into |
|---|---|
| `docs/decisions.md`, `docs/agent-collaboration.md` | `AI_DECLARATION.md`. The organizers require explaining **how the agents were directed**. The current 8-line file is too thin to replace these logs. It should summarize: who did what (Claude: scope/specs, evaluator, ranking, report, README; the other agent: generation implementation; Codex: `DESIGN.md` and reviews), the instructions given, the human decisions that changed the design (Exact/Extract, LLM planner with general guardrails, no local budget cap, local-only evaluator models, same-object product fidelity, relaxed regional guardrails, no human labels, smaller batch), and mistakes caught and fixed (judge-prompt answer leak, nondeterministic image hashing, pilot false rejects, an unreviewed `git add -A` of images). **Correct the current claim that Claude "implemented the system"**: generation was implemented by another agent |
| `docs/generation-runbook.md` | Already covered by `README.md`, except offline replay (`adgen export-fixtures RUN_ID --destination DIR`, then `adgen generate --request R --fixtures DIR`). Add one README line if wanted |

## 3. Move (tests depend on it)

`data/live-runs/2026-09-26-rayban-au-summer-extract/` is an early live run that the tests read. Move **only** the five files the tests use to `tests/fixtures/rayban-live/`: `text-plan.json`, `product-profile.json`, `resolved-context.json`, `candidates/c1/image.png`, `candidates/c2/image.png`. Then:

- update `LIVE` in `tests/test_eval_text.py`;
- update the `source` text in `tests/fixtures/rayban_live_evidence.json`, which mentions the old path;
- delete the rest of the folder (README, `calls.json`, plans, prompts, `request.json`, `summary.json`).

## 4. Small edits after the batch (comments and READMEs only, no behaviour change)

| Location | Change |
|---|---|
| `src/adgen/eval/__init__.py` docstring, `pyproject.toml` `[eval]` comment, `config/evaluator.toml` line 1 | Drop `docs/design/05` references |
| `config/evaluator.toml` lines 2 and 15, `policy/guardrails.yaml` line 2, `src/adgen/config.py` line 51 | Drop implementation-history comments ("v2: …; v3: pilot fixes", "pilot: real bottle scored 0.49", "v2 (2026-09-26, Garmit)"). **Keep the version strings themselves** (`evaluator/3`, `generation/2`, `guardrails/2`); they are recorded in the runs. TOML/YAML comments are not part of any config hash |
| `src/adgen/pipeline.py` lines 19–21 | Optional: drop the legacy `"ValueError"`/`"ValidationError"` resume codes and their comment. No test depends on them |
| `data/products/README.md` limitation about 40 MP | Stale (the limit is 50 MP in code); delete the bullet |
| `.gitignore` `outputs/` | Unused rule |
| `DESIGN.md` header ("Design draft · reviewed against commit …") and §7 | Finalize with the batch results |

Leave as they are: `"Country-level pilot approximation"` (`src/adgen/context.py`) and `"pilot capacity"` (`src/adgen/text.py`). They are runtime strings: the first is part of every recorded context and prompt, so changing it alters reproducibility of the submitted runs.

## 5. Keep

| Path | Why |
|---|---|
| `README.md`, `DESIGN.md`, `AI_DECLARATION.md` (after expansion) | Submission documents |
| `src/`, `tests/` (incl. `tests/fixtures/`), `pyproject.toml`, `requirements.lock`, `.github/workflows/`, `.env.example`, `.gitignore` | Implementation, tests, CI, setup |
| `config/`, `policy/`, `scripts/run-batch.sh` | Configuration and batch runner |
| `data/products/` (photos and provenance README), `data/requests/batch-v1/` (9 requests) | Inputs of the submitted results |
| `submission/` | Generated evaluation report bundle (to be built) |

## 6. Local only (gitignored) — delete locally after `submission/` is committed

`runs/` (all of it, **after** the report is built: dev `state.db`, artifacts, demos, smoke runs, recordings, ad-hoc requests, `smoke_vision.py`, `pilot-report/`, and finally `batch-v1/`), `work/`, `src/*.egg-info/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.DS_Store`, optionally `.venv/`. Keep `.env` local only; rotate keys after the event if desired.
