# Cleanup candidates (flagged only — nothing removed)

Survey of 2026-09-26, made while batch v1 was running. **Nothing listed here has been deleted or changed.** Before removing anything, run `pytest -q` and `adgen demo`. Items marked **keep** are load-bearing for tests, CI or the submission and are listed so nobody removes them by mistake.

## A. Tracked in git — candidates for removal or rewrite

| Path | What it is | Why flagged | Safe to remove? |
|---|---|---|---|
| `examples/heineken-exact.json`, `examples/bottle-extract.json` | Early example requests from the generation-only phase | Superseded by `data/requests/batch-v1/` | Yes, after updating the references in `README.md` and `docs/generation-runbook.md`. No test or CI step uses them |
| `docs/generation-implementation-plan.md` | Earlier agent's review and plan for generation v0.1 | Historical. Describes a generation-only scope ("no evaluator", "generated_unscored") | Yes, or move to `docs/history/`. It is linked from `README.md`, `docs/generation-runbook.md` and `docs/implementation-status.md`, so update those links |
| `docs/generation-runbook.md` | Operating guide titled "Generation v0.1" | Outdated sections (§1 says there are no evaluator modules). §7 (evaluation) is current | Rewrite as one current runbook rather than delete |
| `docs/implementation-status.md` | Working checkpoint log (tickets, EV1–EV6, batch status) | Long and full of intermediate states; useful for handoff, noisy for judges | Condense to a final status, or keep as process evidence |
| `docs/cleanup-candidates.md` | This file | Only needed until cleanup is done | Yes, after cleanup |
| Banners in `docs/design/01`, `04`, `06` | "Implementation checkpoint: generation-only v0.1 … evaluation remains future" | Stale: evaluation is implemented | Edit the banners; keep the documents |
| `docs/design/01` §3 S12 and `06` `export_path` | Say exports go to `outputs/<request_id>/<run_id>/` | Implementation exports to `runs/exports/<run_id>/` (and `submission/` via `adgen report`) | Fix the text |
| `docs/design/05` §8 (report and dataset parts) | Human-label confusion counts, dev/held-out split, kappa | Human labelling dropped (2026-09-26 decision) | Mark as not done or future work; keep the method description |
| `.gitignore` entry `outputs/` | Ignore rule for a folder the code never creates | Harmless leftover | Yes |
| `docs/design/04-implementation-handoff.md` | Ticket plan for the implementing agent | Historical process document | Keep for agent disclosure, or move to `docs/history/` |
| `CLAUDE.md` | One-line pointer to `AGENTS.md` | Only useful to coding agents | Optional |

## B. Legacy code paths (tracked) — removable but low value; do **not** remove casually

| Location | What | Note |
|---|---|---|
| `src/adgen/pipeline.py` `INVALID_PLAN_CODES` legacy entries `"ValueError"`, `"ValidationError"` | Lets runs created before the refactor resume | Pre-v2 runs can no longer be resumed anyway (version bump), so they could be dropped. No test depends on them |
| `src/adgen/state/migrations/002_*.sql`, `tests/test_state.py::test_version_one_database_is_migrated_in_place` | Upgrade path for databases created before the budget-cap removal | **Keep.** Squashing migrations would break existing databases, including the batch-v1 database if it was created before a squash |
| Generation-only path: `--skip-evaluation`, `export` stage, status `generated_unscored` | Generation without evaluation | **Keep.** Used by tests, by `adgen evaluate` (to score older runs) and as a fallback |

## C. Keep — load-bearing (listed to prevent accidental removal)

| Path | Why it must stay |
|---|---|
| `data/live-runs/2026-09-26-rayban-au-summer-extract/` | Pre-v2 live run, but `tests/test_eval_text.py` and `tests/test_eval_candidate.py` read its text plan, context, product profile and images |
| `tests/fixtures/rayban_live_evidence.json` | Genuine recorded OCR and detection evidence used by the evaluator tests |
| `src/adgen/demo.py` (SyntheticProvider, demo vision) | CI runs `adgen demo`; tests use the synthetic provider |
| `requirements.lock`, `.github/workflows/offline-checks.yml` | CI |
| `config/`, `policy/`, `scripts/run-batch.sh`, `data/requests/batch-v1/`, `data/products/` | Pipeline inputs and the batch |
| `docs/context/` (including the obsolete `AGENT_BRIEF.md`) | Original requirements supplied to the agents, needed for the coding-agent disclosure |
| `docs/decisions.md`, `docs/agent-collaboration.md` | Required disclosure trail |

## D. Local only (gitignored) — never submitted, safe to delete locally after the batch

**Do not touch `runs/batch-v1/` until the report is built and committed.**

| Path | What |
|---|---|
| `runs/state.db`, `runs/artifacts/`, `runs/locks/`, `runs/exports/` | Development database and artifacts: synthetic demos, the pre-v2 live Ray-Ban run, and a dry-run of its evaluation |
| `runs/demo/`, `runs/final-demo/`, `runs/offline-reference-smoke/` | Synthetic smoke and demo runs |
| `runs/recordings/0d425b20…/` | Replay fixtures of the pre-v2 live run; cannot replay after the normalization fix, so no longer useful |
| `runs/requests/rayban-extract.json`, `runs/requests/heineken-in-summer-exact.json` | Ad-hoc live requests (superseded by batch-v1 requests 01 and 02) |
| `runs/smoke_vision.py` | One-off model smoke script (superseded by `LocalVision` and its tests) |
| `work/install.log`, `work/offline-reference-smoke.json` | Earlier agent's install log and smoke summary |
| `src/ad_image_generator_evaluator.egg-info/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.DS_Store` | Build and cache files |
| `.venv/` (1.8 GB) | Local environment; recreate from `requirements.lock` + `[eval]` |
| `.env` | **Your API keys.** Never commit; delete or rotate after the hackathon if desired |

## E. Doc drift to fix during the final write-up (not deletions)

- `README.md` still links `docs/generation-implementation-plan.md` and `examples/`. Its "What is implemented" section should mention evaluation, ranking and the report consistently.
- `docs/design/05` names PP-OCRv5 in places other than the evaluator-model table.
- `docs/design/02` model table: the judge is `gpt-6-sol`, local models are pinned; check that it matches `config/evaluator.toml`.
