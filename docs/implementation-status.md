# Implementation status

Checkpoint maintained by the implementing agent. Current human instruction: finish generation first, without UI or evaluator; **offline implementation only**. Update this record with each subsequent milestone.

## Current checkpoint

| Field | Value |
|---|---|
| Design | v0.4, with generation-only implementation corrections documented in the review/runbook |
| Implementation | Generation v0.1; G0–G8 implemented and verified offline |
| Local verification | 90 tests passed; Ruff check + format passed; demo/replay/export exercised; Python 3.13.3/macOS. Pre-change commit 4049341 also reproduced green on a clean clone with Python 3.11 (CI steps) |
| Reference smoke runs | Three-reference Heineken Exact: 3 synthetic candidates; single-reference bottle Extract: 2 synthetic candidates; all saved |
| Provider evidence | Real SDK serialization/deserialization through mocked HTTP transports; no provider network inference |
| Paid usage this checkpoint | $0; no live calls; credentials not required or supplied to tests |
| Live readiness | Adapters wired; G9 account/model compatibility and real image output still unverified |
| Deferred | UI; all image evaluation, scores, selection and batch evaluation |
| Spend control | Local budget cap removed (migration 002); limits are set on provider accounts; ledger keeps usage and report-only cost estimates |
| Live evidence | First live run 2026-09-26 (Garmit's keys): 1 reference, Extract, 2 candidates, AU summer — all 8 calls completed, both images 1024×1024, ~$0.19 estimated. Curated in `data/live-runs/2026-09-26-rayban-au-summer-extract/` |
| Next step | G9 remainder: 3 candidates and a multi-reference Exact request; then Garmit's human labels; then evaluator E0 |

Implementation and operating details: [generation runbook](generation-runbook.md). Design review and rationale: [implementation plan](generation-implementation-plan.md).

## Evaluator build plan (active — resume here)

Human instruction (2026-09-26): implement evaluation, connect it to generation, rank candidates, and produce a reproducible submission bundle (`submission/`: report.md, results.csv, results.json, contact-sheet.html, images/, evidence/, requests.jsonl) with a small human-labelled subset. Keep this checkpoint current so another agent can continue.

Specs: docs/design/05 §5–7 (text, product = same-object P1–P6, context, composition, scores, ranking), 01 §3 S10–S12, 06. Product fidelity does **not** score position or orientation (D32).

| Step | Deliverable | Status |
|---|---|---|
| EV1 | Vision backends + evidence recording + `config/evaluator.toml` + `[eval]` extra | **done** — LocalVision verified on real images (OCR ~6 s, detect ~2.5 s, embed <0.3 s after load). PaddleOCR 3.7 defaults to PP-OCRv6; pinned explicitly |
| EV2 | Text evaluation (`eval/text_eval.py`, `eval/compose.py`, `eval/judge.py` selection schema) | **done** — tests on genuine recorded OCR/detection of live c1 (pass) and c2 (duplicate caught) in `tests/fixtures/rayban_live_evidence.json`. Deferred: blind judge fallback reader when OCR is uncertain (returns unknown instead) |
| EV3 | Visual judge + candidate evaluator (`eval/judge.py`, `eval/evaluator.py`, `compose.rank`) | **done** — one judge call per candidate (refs + ad, blind to copy); P1 needs detector+judge agreement; judge outage → unknown/degraded; GR-TEXT image rule skipped (covered by rendering) |
| EV4 | Pipeline integration | **done** — stages `selection_evaluation`, `reference_evidence` (cached), per-candidate `evaluation`, selection table + `export_evaluated` (so generation-only runs can be evaluated later via `adgen evaluate --run-id` without regenerating). Migration 003. CLI evaluates by default (`--skip-evaluation`); live requires `[eval]` models; replay uses `fixtures/vision/`; demo is replayable with evaluation. Candidate status: `evaluated` / `evaluation_failed` (image kept) |
| EV5 | `adgen report` submission bundle (`eval/report.py`) | **done** — report.md (computed tables + method/criteria/limitations text), results.csv/json (one row per candidate incl. failures/unknowns, models, versions, dims, latency, cost), contact-sheet.html, images/, evidence/, requests.jsonl; human-label agreement from `data/labels.csv` (format in `data/LABELS.md`); synthetic runs excluded unless `--include-synthetic` |
| EV6 | Docs/runbook; live evaluation of the curated Ray-Ban run (paid judge call, needs Garmit's go) | pending |

## Tickets

| Ticket | Status | Evidence |
|---|---|---|
| G0 Scaffold | Complete offline | `pyproject.toml`, pinned pip snapshot, configuration, CLI, README, offline CI workflow |
| G1 State store | Complete for generation | Migration 001; content-addressed artifacts; lineage; lock/cost/crash/resume tests; evaluation tables deliberately deferred |
| G2 Contracts/enums | Complete | Closed Pydantic request/provider schemas; span and geometry checks |
| G3 Intake/context | Complete | Multi-reference decode/normalize/hash, 50 MP ceiling; all 32 country/season combinations tested |
| G4 Providers/replay | Complete offline | OpenAI/Gemini adapters; SDK mock transports; no retries; exact-match fixtures and receipt export |
| G5 Copy selection | Complete offline | Exact in code; Extract source spans; protection/capacity/omission checks; no semantic fidelity claim |
| G6 Product analysis | Complete offline | All references, canonical order/set cache, original lineage preserved |
| G7 Planner/guardrails | Complete offline | Copy isolated; zone validation; approve/replan-approve/reject-render/invalid-stop paths |
| G8 Orchestration/generation/export | Complete offline | Candidate isolation; one image call each; square/size gate; all PNGs saved; unscored summary and state snapshot |
| G9 Live compatibility | Partially verified | Single-reference Extract with 2 candidates succeeded live (models, structured output, Gemini 1:1/1K settings accepted). Multi-reference and Exact paths not yet run live |
| E0–E2 Evaluators | Not started | Explicitly outside this turn's scope |
| G10 Evaluation + selection | Not started | Generation-only export exists; no winner or scores |
| E3–E5 Labels/batches/report | Not started | Depends on later evaluator implementation |

## Evidence details

`pytest -q`: **89 passed**. Coverage includes SDK request shape and no-retry behavior, response refusal/no-image/multiple-image handling, omission/protected-span failures, 42 MP image normalization, EXIF/ICC/alpha, both guardrail replan outcomes, invalid plan recovery, per-candidate failure isolation, changed-input/config refusal, artifact corruption, shared-stage uniqueness, mutual exclusion, report-only cost estimates, v1→v2 schema migration, dispatch-before-network, receipt reuse after interruption, unknown-call non-resend and secret-safe exception recording.

The two repository-photo smoke runs used **SyntheticProvider**, not visual analysis or Gemini. Local run IDs were `c699c241ae1149d5afa2c418218bac1e` (Heineken) and `84182641d87f4f048212dea51c3d9781` (bottle), in the gitignored `runs/offline-reference-smoke/state.db`. These are local verification artifacts, not portable benchmark evidence. The normal demo generates its own portable synthetic fixtures on demand. CI has been configured, but remote CI completion is not claimed here.

## Checkpoint history

- 2026-09-26 — Design v0.3 committed; implementation not started.
- 2026-09-26 — Design v0.4 committed; implementation not started.
- 2026-09-26 — Garmit requested review and generation implementation, then explicitly selected offline-only work. G0–G8 implemented in this checkpoint with tests and runbook. No evaluator or UI added.
- 2026-09-26 — Local budget cap removed at Garmit's direction (Claude Code): migration 002, no `--budget-usd`, no reservations; `--allow-paid`, dispatch-before-send, unknown-never-resent and usage-based report-only cost kept. 89 tests pass.
- 2026-09-26 — First live run (Ray-Ban, AU summer, Extract, 2 candidates) succeeded; curated into `data/live-runs/` with empty human-label template. c2 shows a naturally occurring duplicated-text rendering failure.
- 2026-09-26 — Fixed nondeterministic reference normalization (af75a71). Behaviour-preserving refactor of pipeline/CLI/zones verified by identical content-addressed run signature; 90 tests pass.
