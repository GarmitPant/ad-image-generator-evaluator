# Cleanup list for the final submission commit (prepared — nothing removed yet)

Rule (Garmit, 2026-09-26): the final submission keeps the **implementation, its inputs, tests and the generated evaluation report**. Anything that existed to plan, specify or steer the agents is removed: plans, specs, briefs, checkpoints and agent instructions. The coding-agent disclosure moves into the submission write-up.

Before and after cleanup, run `ruff check src tests`, `pytest -q` and `adgen demo`. Do not touch `runs/batch-v1/` until `submission/` is built and committed.

## 1. Remove: agent steering, plans and specs

| Path | What it is |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Agent working brief and pointer |
| `docs/context/` (7 files, including `AGENT_BRIEF.md`) | Original context bank and requirements supplied to the agents |
| `docs/design/` (7 files: README, 01–06) | Design specs v0.1–v0.4 and the implementation handoff |
| `docs/generation-implementation-plan.md` | Earlier agent's review and plan |
| `docs/batch-v1-plan.md` | Batch run plan |
| `docs/implementation-status.md` | Agent checkpoint log |
| `docs/cleanup-candidates.md` | This list (remove last) |
| `examples/heineken-exact.json`, `examples/bottle-extract.json` | Early example requests, superseded by `data/requests/batch-v1/` |

## 2. Fold into the write-up, then remove

| Path | What to carry over first |
|---|---|
| `docs/generation-runbook.md` | Setup, models download, `generate` / `evaluate` / `report` / replay usage → README |
| `docs/decisions.md`, `docs/agent-collaboration.md` | **The organizers require a coding-agent disclosure** (how the agent was directed, via the requirements supplied or summarized traces). Summarize the key instructions, human changes and decisions into the write-up's disclosure section **before** deleting these |

## 3. Fix dangling references before deleting (small edits, no behaviour change)

| Location | Currently points to |
|---|---|
| `src/adgen/eval/__init__.py` (docstring) | `docs/design/05` |
| `config/evaluator.toml` line 1 (comment) | `docs/design/05 §8` |
| `pyproject.toml` `[eval]` comment | `docs/design/05` |
| `data/products/README.md` limitation about 40 MP | `docs/design/01`; the limit is now 50 MP in code, so the note is stale |
| `README.md` "Design and next phase" section and other links | `docs/design/*`, `docs/generation-implementation-plan.md`, `docs/implementation-status.md`, `docs/generation-runbook.md`, `examples/`, `docs/context/`, `AGENTS.md` |
| `.gitignore` | `outputs/` rule for a folder the code never creates |

None of the code, tests, CI, scripts or generated report reads these documents; only comments and READMEs link to them.

## 4. Legacy code (optional; low value)

| Location | Note |
|---|---|
| `src/adgen/pipeline.py` `INVALID_PLAN_CODES` entries `"ValueError"`, `"ValidationError"` | Resume compatibility for pre-refactor runs, which can no longer resume (version bump). No test depends on them. Safe to drop |
| Migrations `002`/`003` and the v1→v2 migration test | **Keep**; squashing would break existing databases, including batch-v1 |
| `--skip-evaluation`, `export` stage, `generated_unscored` | **Keep**; used by tests and `adgen evaluate` |

## 5. Keep: the submission

| Path | Why |
|---|---|
| `src/`, `tests/`, `pyproject.toml`, `requirements.lock`, `.github/workflows/`, `.env.example`, `.gitignore` | Implementation, tests, CI, setup |
| `config/`, `policy/`, `scripts/run-batch.sh` | Pipeline configuration and batch runner |
| `data/products/` (with its provenance README), `data/requests/batch-v1/` | Inputs |
| `submission/` (after `adgen report`) | Generated evaluation report bundle |
| `README.md` (rewritten) + the write-up | Entry point, design and implementation narrative, disclosure |
| `data/live-runs/2026-09-26-rayban-au-summer-extract/` and `tests/fixtures/rayban_live_evidence.json` | **Tests read these** (text plan, context, product profile, candidate images and recorded OCR/detection). Option: move the live-run files under `tests/fixtures/` and update the `LIVE` path in `tests/test_eval_text.py`, so `data/` holds only inputs. That is a move, not a delete |

## 6. Local only (gitignored) — delete locally after the report is committed

`runs/state.db`, `runs/artifacts/`, `runs/locks/`, `runs/exports/`, `runs/demo/`, `runs/final-demo/`, `runs/offline-reference-smoke/`, `runs/recordings/`, `runs/requests/`, `runs/smoke_vision.py`, `work/`, `src/*.egg-info/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.DS_Store`. Optionally `.venv/` (1.8 GB). `.env` holds your keys: never commit it, and rotate the keys after the event if desired.

## Note on Git history

Removing files in the final commit hides them from the submitted tree, but they remain in earlier commits on GitHub. If they must not be visible at all, the history would have to be rewritten (a force-push). That is a separate decision, not part of this cleanup.
