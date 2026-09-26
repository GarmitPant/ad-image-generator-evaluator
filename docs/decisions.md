# Decision register

## Confirmed user direction

| Date | Direction | Source |
|---|---|---|
| 2026-09-26 | Design/research here; implementation through another agent; Python; UI later | User instruction and original context |
| 2026-09-26 | Use separate tasks to understand product/context and plan before image generation | User proposal in the design conversation |
| 2026-09-26 | Use `GarmitPant/ad-image-generator-evaluator` as the separate project repository | User supplied the newly created repository |

## Proposed architecture

See [the proposal register](design/03-challenges-and-decisions.md), D01–D14. These have not been collectively approved by Garmit. Model choices, retry policy, evaluator internals and the proposed $15 envelope remain proposals; no paid inference is authorized by this file.

Future entries must record the decision, status, reason, alternative, and actual authorizing instruction. Do not replace historical entries; add superseding decisions.


## 2026-09-26 — Superseding user clarification

| Decision | Status and reason | Supersedes |
|---|---|---|
| This repo holds implementation too | Confirmed explicitly by Garmit | Any wording implying a design-only repository |
| Automated evaluation methods/criteria are the main judged engineering work | Confirmed by Garmit; no percentage weights supplied | Generation-first priority |
| Source text supplies content, not ad look/feel | Confirmed by Garmit | Any use of freeform copy as visual art direction |
| Exact and Extract modes, with optional protected phrases | User explicitly selected the recommended option | Blanket entire-input-verbatim rule |
| Evaluate original input against selected and rendered text | Confirmed direction; split into two proposed evaluator stages | OCR-only text fidelity |

Proposed consequences: one-image baseline; defer repairs/aesthetic planning; use source-span-backed extraction and independent semantic selection checks. See design/05-evaluation-and-text-contract.md. Numeric limits, component thresholds/model choices and spend remain unapproved technical proposals.


## 2026-09-26 — Generation design v0.3 (Garmit, via Claude Code session)

| Decision | Status and reason | Supersedes / alternative considered |
|---|---|---|
| Implement generation pipeline before evaluator | Confirmed by Garmit | v0.2 evaluator-first ticket order; evaluation remains the main judged deliverable |
| Add LLM creative planner (S5) | Confirmed; richer, context-tailored scenes than a fixed template | v0.2 fixed code template |
| Planner sees text roles + lengths, not copy | Confirmed; keeps freeform text from steering visual direction | Alternative: pass copy for thematic fit (rejected) |
| Geography = 8-country enum (US, GB, DE, JP, IN, AU, BR, AE) with one facts row each; season enum | Confirmed; per-pair registry judged infeasible to extend | v0.2 reviewed per (country, season) scene profiles |
| General guardrails (stereotype, tokenism, religion, season, people, alcohol, extra text) | Confirmed; country-agnostic so new geographies are one row | Per-pair must_not/avoid lists |
| Guardrail enforcement: code checks + LLM reviewer; one replan; if still rejected, generate and flag `rejected_after_replan` for evals | Confirmed | Alternative: block the run (rejected) |
| SQLite state store for stages/artifacts/calls/events; observability later | Confirmed architectural requirement; must run locally with README setup | Files-only run directory |
| OpenAI for LLM stages, Gemini for images; no Anthropic code now (Claude possibly a future backup) | Confirmed | v0.2 Gemini 3.8 Flash analysis + Claude judge |
| Only `.env.example` placeholders committed; users supply own keys | Confirmed | — |
| Reference input limit raised to 50 MP | Proposed (heineken-3.jpg ≈ 42.2 MP) | 40 MP |
| `gpt-6-sol` for all OpenAI stages | Proposed; verify in compatibility probe | `gpt-6-luna` if recorded cases show parity |
| Credits: ~$10 Gemini + ~$10 OpenAI | Recommendation to Garmit; purchase and spend approval pending | — |
