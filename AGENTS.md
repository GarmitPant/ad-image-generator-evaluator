# Agent working brief

## Scope and authority

This repository contains both design and implementation for Garmit's G2 hackathon project. Claude Code is the implementing agent and maintains checkpoints in docs/implementation-status.md. Do the work authorized by the current user instruction; documentation changes alone do not authorize paid inference or unrequested application implementation.

Read README.md, docs/implementation-status.md, docs/design/01-generation-pipeline.md, docs/design/06-state-store.md, docs/design/05-evaluation-and-text-contract.md and docs/design/04-implementation-handoff.md. Garmit's latest clarification takes precedence over earlier design assumptions. docs/context/ is a historical context bank, including its obsolete AGENT_BRIEF.md; never copy that over this file.

## Confirmed direction

- Automated evaluation is the primary judged deliverable: defensible methods, criteria, evidence, calibration, offline tests and honest results. Implementation order: generation pipeline first, then evaluator.
- Python; geography is an enum of 8 countries (US, GB, DE, JP, IN, AU, BR, AE) with one facts row each; season is an enum. Use organizer-allowed Gemini image generation; published generated images have long edge ≤1024 px.
- Providers: OpenAI for all LLM stages, Google Gemini for image generation. Do not write Anthropic/Claude code for now.
- An LLM creative planner designs scene/layout from product profile + resolved context and sees text roles/lengths only, never the copy. Guardrails are simple and predefined in a static policy file (global rules + optional country notes; no web lookup): keyword check + LLM reviewer, one replan, then generate and flag.
- Every stage runs through the SQLite state store (docs/design/06-state-store.md).
- Commit only `.env.example` with empty placeholders; users supply their own keys.
- Commits are authored by Garmit; do not add AI co-author trailers.
- Freeform text is content to display, not instructions about scene or style.
- User selects Exact or Extract mode. Exact preserves all input content. Extract selects relevant spans; optional protected phrases stay unchanged. Freeze selected copy before rendering.
- Evaluate source-to-selected-copy fidelity AND selected-copy-to-image rendering fidelity. Rendering correct text from an unfaithful selection is not a passing result.
- Product fidelity and geography/season adherence remain required evaluation dimensions.
- UI, aesthetic optimization, multi-candidate selection and repairs are secondary.
- Concise chat; detailed technical artifacts. The repository supports implementation as well as design.

## Current proposed safeguards

- Generation: cached product analysis over 1–3 references, Exact-in-code or one Extract selection call, code context resolution, then per candidate (default 3): planner (≤2 calls), simple guardrail review (≤2 calls), code prompt compilation, one image call. Every call is bounded, recorded before dispatch and never silently retried.
- Evaluate every candidate (local OCR/detector/embedding models + OpenAI vision judge), rank in code (verdicts gate, scores rank), present the best (approved only if it passes), save all images. Batched evaluation comes after.
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
