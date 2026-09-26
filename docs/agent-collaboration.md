# Agent collaboration log

## 2026-09-26 — Design v0.1

- Human instruction: read the seven g2-ad-imagegen context files; research and create detailed system specs for another coding agent; begin with generation; keep chat concise and UI secondary.
- Work performed: source review; official model-documentation research; generation contracts, model roles, challenge register and staged implementation handoff.
- Human steering: about six hours left, no configured billing/budget, product photos forthcoming; proposed separate model tasks for input interpretation, ad planning and text preparation before rendering.
- Design response: separate reference-analysis and structured ad-planning calls; preserve binding ad copy; compile the validated plan into image instructions in code.
- Validation: document-local links and Markdown fence balance checked. No implementation tests, paid inference, model benchmarks or evaluator calibration performed.
- Status: draft architecture, not approved empirical results.

## 2026-09-26 — Repository preparation

- Human instruction: supplied newly created `GarmitPant/ad-image-generator-evaluator` repository for this project.
- Work performed: cloned the empty repository; copied all seven historical context files and five design documents; updated repository references; wrote reconciled agent instructions, root README, ignore rules and decision/collaboration logs.
- Human changes: repository selection is confirmed; no new architecture or budget approvals were received.
- Validation: original context integrity and documentation links checked before committing; no application code exists yet.
- Next: continue generation-design review and authorize an implementation slice separately; enable Gemini billing and source product photos before live testing.


## 2026-09-26 — Evaluation-first scope and text semantics, v0.2

- Human instruction: this repository is for implementation too; judges emphasize automated evaluation methods and criteria; generation only needs to function. Freeform input is copy/content, from which relevant parts may be selected, with some text preserved verbatim; evaluate input vs selected/rendered text.
- Clarification received: Garmit explicitly selected Exact/Extract modes with optional protected phrases.
- Work performed: introduced the evaluation/text-contract spec; separated source-selection fidelity from image-rendering fidelity; replaced generation-first handoff with evaluator-first tickets; simplified proposed generation to one image; reconciled root instructions, model roles and decision register.
- Validation: documentation references, current-contract consistency and preserved historical-context integrity checked. No application code, paid inference or empirical accuracy claims added.
- Design status: explicit priorities/modes confirmed; proposed limits, model choices, matching/calibration details remain subject to pilot evidence. Budget remains unapproved.

## 2026-09-26 — Reference product images added (Claude Code)

- Human instruction: pull `~/Downloads/Reference Images` into the workspace and repo; commits must be authored by Garmit, not Claude Code.
- Work performed: copied six originals byte-for-byte to `data/products/` (SHA-256 verified against source); recorded Unsplash provenance from download metadata, per-image evaluation roles, trademark limitation, and that `heineken-3.jpg` (~42.2 MP) exceeds the proposed 40 MP input limit.
- Validation: hash equality with source files; visual inspection of downscaled previews. No code, paid inference or design changes.
- Next: Garmit to supply pending design changes before implementation begins.

## 2026-09-26 — Generation design v0.3 (Claude Code)

- Human instructions: Claude Code is the implementing agent and keeps checkpoints. OpenAI API for text models, Gemini for image generation; no Anthropic implementation now. Start with the generation pipeline. Add an LLM planner. Replace the per geography×season registry with general anti-stereotype guardrails and predefined enums (8 countries accepted). One replan, then generate and flag in evals. SQLite state store as an architectural requirement, set up locally with instructions. Planner gets text roles and lengths only. Commit placeholder keys only.
- Agent proposals accepted by Garmit: 8-country list, roles+lengths planner input, SQLite, stage map S1–S9.
- Work performed: rewrote 01 (v0.3 pipeline, sub-agents, guardrails, prompt compiler), added 06 (state-store schema/rules), rewrote 02 (OpenAI/Gemini roles, `gpt-6-sol` proposal from OpenAI's model catalog, spend arithmetic), rewrote 04 tickets (G0–G9 then E0–E5), updated 05 context-adherence criteria so the evaluator does not grade against the planner's own cues, extended 03/decisions, added `.env.example` and docs/implementation-status.md.
- Validation: cross-document consistency and link checks. No code, tests or paid inference yet.
