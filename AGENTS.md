# Agent working brief

## Scope and authority

Garmit owns scope and architecture. This repository is for the G2 ad image generation/evaluation hackathon. Another agent handles implementation; this design collaboration develops research, specifications and plans. Do not begin implementation merely because documentation has been copied here.

Read `README.md`, `docs/context/01-problem-statement.md`, and the documents under `docs/design/` before work. Organizer requirements and Garmit's latest explicit instructions take precedence. `docs/context/` is an immutable historical context bank. Its `AGENT_BRIEF.md` and design sketches contain superseded proposals; do not apply them over the corrections in `docs/design/`.

Current design v0.1 remains proposed except where Garmit's explicit instructions establish a requirement. Do not record a proposal as approved. Authorized implementation tasks can follow their named spec; document consequential deviations and raise unresolved decisions without blocking independent work.

## Confirmed direction

- Python; strong typing for geography and season.
- Separate product-reference analysis, ad planning and image rendering responsibilities. Different tasks may share a model ID.
- Required ad text stays verbatim; planning changes typography and placement, not its content.
- Image generation uses an organizer-allowed Gemini 3.1 Flash Image or Flash-Lite Image model; generated outputs must have long edge ≤1024 px.
- Evaluate at least context adherence, product fidelity and text fidelity, with automated evidence of passing and failing cases.
- UI is secondary. Keep library/CLI interfaces reusable by a later UI.
- Concise chat; meticulous specs, plans and technical validation.

## Proposed implementation safeguards

When implementing the current generation design, preserve these contracts unless Garmit changes them:

- Validate model plans and compile prompts in code. Do not silently rewrite inputs.
- Use two candidates and at most one repair with three total image dispatches, including retries.
- Keep reference artifacts, plans, generated parents and edited children immutable and hash-linked.
- Distinguish evaluation reliability (`ok|degraded|failed`) from image verdict (`pass|fail|unknown`). Missing evaluation never means passing.
- Compose acceptance in code. Do not let a model invent an overall passing score.
- Reevaluate every dimension after an edit. Never overwrite evidence with an edited image.
- Never claim OCR/detection/embeddings are infallible or that a generated preview has passed an unimplemented evaluator.
- Keep tests offline by default. Actual recorded model responses support regression tests; synthetic responses prove control flow only.
- Paid inference requires a concrete estimate and Garmit's authorization; no API budget has yet been approved. Keep a cost ledger including failed/uncertain calls. Do not silently retry billable calls.
- Keep credentials in a gitignored `.env` or process environment; never print or commit secrets. Preserve provider provenance markings.
- Record human labels, threshold-tuning split, unknowns, failure counts and measured results honestly.

## Milestones and records

Use `docs/design/04-implementation-handoff.md` for ticket boundaries and acceptance tests. After each milestone append the actual user instruction, work performed, validation, human changes, and unresolved issues to `docs/agent-collaboration.md`. Record accepted/rejected decisions in `docs/decisions.md`, linking the source instruction. Never claim tests or API probes ran when they did not.
