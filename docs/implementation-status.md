# Implementation status

Checkpoint maintained by the implementing agent. Current human instruction: finish generation first, without UI or evaluator; **offline implementation only**. Update this record with each subsequent milestone.

## Current checkpoint

| Field | Value |
|---|---|
| Design | v0.4, with generation-only implementation corrections documented in the review/runbook |
| Implementation | Generation v0.1; G0–G8 implemented and verified offline |
| Local verification | 88 tests passed; Ruff passed; editable install and CLI demo/replay/export exercised; Python 3.13.3/macOS |
| Reference smoke runs | Three-reference Heineken Exact: 3 synthetic candidates; single-reference bottle Extract: 2 synthetic candidates; all saved |
| Provider evidence | Real SDK serialization/deserialization through mocked HTTP transports; no provider network inference |
| Paid usage this checkpoint | $0; no live calls; credentials not required or supplied to tests |
| Live readiness | Adapters wired; G9 account/model compatibility and real image output still unverified |
| Deferred | UI; all image evaluation, scores, selection and batch evaluation |
| Next step | Review this generation checkpoint; when expressly authorized, run a small recorded live compatibility probe with a concrete budget |

Implementation and operating details: [generation runbook](generation-runbook.md). Design review and rationale: [implementation plan](generation-implementation-plan.md).

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
| G9 Live compatibility | Deferred by explicit human instruction | No spend approved; no real model-quality, latency or compatibility observations |
| E0–E2 Evaluators | Not started | Explicitly outside this turn's scope |
| G10 Evaluation + selection | Not started | Generation-only export exists; no winner or scores |
| E3–E5 Labels/batches/report | Not started | Depends on later evaluator implementation |

## Evidence details

`pytest -q`: **88 passed**. Coverage includes SDK request shape and no-retry behavior, response refusal/no-image/multiple-image handling, omission/protected-span failures, 42 MP image normalization, EXIF/ICC/alpha, both guardrail replan outcomes, invalid plan recovery, per-candidate failure isolation, changed-input/config refusal, artifact corruption, shared-stage uniqueness, mutual exclusion, budget reservation, dispatch-before-network, receipt reuse after interruption, unknown-call non-resend and secret-safe exception recording.

The two repository-photo smoke runs used **SyntheticProvider**, not visual analysis or Gemini. Local run IDs were `c699c241ae1149d5afa2c418218bac1e` (Heineken) and `84182641d87f4f048212dea51c3d9781` (bottle), in the gitignored `runs/offline-reference-smoke/state.db`. These are local verification artifacts, not portable benchmark evidence. The normal demo generates its own portable synthetic fixtures on demand. CI has been configured, but remote CI completion is not claimed here.

## Checkpoint history

- 2026-09-26 — Design v0.3 committed; implementation not started.
- 2026-09-26 — Design v0.4 committed; implementation not started.
- 2026-09-26 — Garmit requested review and generation implementation, then explicitly selected offline-only work. G0–G8 implemented in this checkpoint with tests and runbook. No evaluator or UI added.
