# Generation implementation checkpoint plan

2026-09-26 — reviewed v0.3/v0.4 changes through commit 457be92.

## Review

The revised design is implementable: 1–3 references, shared Exact/Extract TextPlan, one OpenAI creative plan per candidate, a static keyword policy plus reviewer, one bounded replan, Gemini rendering, and SQLite lineage. Keep those decisions. Evaluation, ranking, best-image export and UI are explicitly out of scope for this implementation turn.

Corrections required at implementation:

- SQLite UNIQUE with nullable candidate_index does not prevent duplicate shared-stage rows. Use candidate_index=0 for request-level stages, positive indices for candidates.
- A generation-only run can succeed with generated_unscored and all saved candidates; no fabricated winner, score, evaluation table or evaluator dependency.
- Cached multi-reference analysis must canonicalize the actual input order as well as its hash key; retain original declared order for generation.
- A keyword scan must ignore the plan's avoid/rationale fields, or prohibitions such as “avoid snow” would reject every plan.
- “No raw source in prompt” means no unselected source/metadata as instructions. In Exact mode, the selected literal string necessarily equals the source.
- Persist provider receipts before parsing; a schema rejection is not a lost/unknown paid call. Missing transport outcomes remain unknown and are never automatically resent.
- Hash/schema validation includes persisted artifacts on resume; changed files cannot silently reuse prior work.

## Work order

1. G0: package/configuration, isolated environment, CLI skeleton.
2. G1: generation-only SQLite migration, artifacts/lineage, locks, costs, resume.
3. G2/G3/G5: typed contracts, image intake, all 32 context combinations, Exact/Extract validation.
4. G4/G6/G7: OpenAI structured-output and replay boundary, product analysis, planner/reviewer with bounded replan.
5. G8: Gemini adapter, output gate, N-candidate orchestration, CLI/export and synthetic offline demo.
6. Verify meaningful offline failure paths and SDK request/response parsing. Update README and checkpoints; commit/push.

## Authorization and evidence

Garmit explicitly requested offline implementation only. No paid/provider inference calls are permitted in this turn. Dependencies may be installed; SDK boundaries are tested with injected transports. Synthetic fixtures prove mechanics, not model quality. G9 live compatibility remains unverified, with future explicit live mode and budget required.

## Completion checkpoint

G0–G8 implemented and verified offline: 88 tests, Ruff, CLI demo/replay/export, and synthetic runs using the supplied three-reference Heineken and single-reference bottle examples. Detailed interfaces, recorded deviations and limitations are in [the generation runbook](generation-runbook.md). G9 remains deferred by explicit user instruction. Evaluation and UI have no implementation in this checkpoint.
