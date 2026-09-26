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
