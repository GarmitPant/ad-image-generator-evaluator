# Agent working brief

## Scope and authority

This repository contains both design and implementation for Garmit's G2 hackathon project. Another coding agent implements here; this design collaboration handles research/specification. Do the work authorized by the current user instruction; documentation changes alone do not authorize paid inference or unrequested application implementation.

Read README.md, docs/design/05-evaluation-and-text-contract.md, docs/design/01-generation-pipeline.md and docs/design/04-implementation-handoff.md. Garmit's latest clarification takes precedence over earlier design assumptions. docs/context/ is a historical context bank, including its obsolete AGENT_BRIEF.md; never copy that over this file.

## Confirmed direction

- Automated evaluation is the primary engineering deliverable: defensible methods, criteria, evidence, calibration, offline tests and honest results. Generation only needs to function.
- Python; geography and season strongly typed. Use organizer-allowed Gemini image generation; published generated images have long edge ≤1024 px.
- Freeform text is content to display, not instructions about scene or style.
- User selects Exact or Extract mode. Exact preserves all input content. Extract selects relevant spans; optional protected phrases stay unchanged. Freeze selected copy before rendering.
- Evaluate source-to-selected-copy fidelity AND selected-copy-to-image rendering fidelity. Rendering correct text from an unfaithful selection is not a passing result.
- Product fidelity and geography/season adherence remain required evaluation dimensions.
- UI, aesthetic optimization, multi-candidate selection and repairs are secondary.
- Concise chat; detailed technical artifacts. The repository supports implementation as well as design.

## Current proposed safeguards

- Functional baseline: one source selection call when Extract is used, optional cached reference analysis, deterministic scene/layout compilation, one image call. Exact selection is code. Do not add separate creative planning just for architectural complexity.
- Initial extraction is source-span based; semantic checks catch misleading omissions even if every chosen word occurs in the input. No unsupported paraphrase.
- Validate schemas and span references in code. Keep source, policy, protected spans, plan, reference, image and evaluator versions immutable and hashed.
- A source/plan selector cannot define its own passing criteria after seeing results. Human gold requirements are independently labelled.
- Run OCR/blind transcription without supplying expected text. Match text blocks spatially and one-to-one; record missing, altered, unexpected and illegible content.
- Compose verdicts in code. Keep evaluation reliability separate from pass/fail/unknown quality. Learned measurements are fallible; missing evidence never means pass.
- Keep generation and standalone evaluation decoupled. Replay must never fall through to paid providers.
- Genuine recorded responses and real labelled images test evaluator behaviour; synthetic fixtures test control flow only.
- Paid inference requires an authorized concrete estimate and ledger. No API budget is approved yet. No hidden billable retries.
- No secrets in logs/commits; use gitignored environment configuration. Preserve provider provenance markings.
- Report counts, abstentions, tuning splits, human intervention and failures. Do not invent model superiority, calibration or test results.

## Records

Append actual milestones and human revisions to docs/agent-collaboration.md. Record accepted/rejected/superseded decisions in docs/decisions.md. Model choices, numerical thresholds and capacity limits are proposals until evidence or user direction establishes them.
