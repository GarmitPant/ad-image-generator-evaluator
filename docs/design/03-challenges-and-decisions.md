# Challenges, proposed decisions, and next experiments

2026-09-26 · Proposals for discussion, not an approved architecture freeze.

## 1. Major challenges

| Priority | Challenge | Why the obvious approach fails | Proposed control | Smallest useful experiment |
|---|---|---|---|---|
| P0 | Product identity | A realistic replacement can resemble the category but change logo, packaging or shape | Original reference always supplied; reviewed features; crop/attribute checks; no unseen-angle demands | Distinctive bottle and mug; compare genuine output with same-category wrong product |
| P0 | Exact text | Generative rendering can miss a symbol; OCR can also misread correct text | Freeze copy; simple type treatment; spatial OCR; strict vs diagnostic metrics; one bounded edit | Headline with `%`, currency, mixed case and punctuation; one-character negatives |
| P0 | Useful context without stereotypes | A country is not a single climate; generic “winter” can add implausible snow | Explicit local scene assumptions and compatible cue inventory | Same product/headline, AU winter vs a northern winter profile; human review of both |
| P0 | Planner overreach | A helpful language model may invent claims, rewrite copy or add unrealistic props | Structured IDs, immutable constraints, semantic validation, labelled template fallback | Planner responses with altered headline, unknown cue, missing required cue |
| P0 | Trustworthy quality gates | Judge scores can reward intent rather than visible evidence; learned checks have errors | Shared contract, independent evidence, `unknown`, calibration and human labels | Genuine pass/fail images judged blind, not only fabricated JSON fixtures |
| P1 | Edits damage good regions | Headline repair may alter the product or background | Immutable parents and full reevaluation | Compare parent/child across all dimensions; reject repair with new identity error |
| P1 | Runtime budget and reliability | “2–3 candidates + 2 retries” expands unexpectedly; timeouts may still bill | Three total image dispatches, explicit costs, no invisible SDK retries | Fake timeout/duplicate-resume paths with dispatch counters |
| P1 | Experimental validity | Selecting only successes or judging enriched prompts with bespoke rubrics inflates wins | Freeze paired requests/rubrics and retain failures; blind arm labels | Equal-budget raw/enriched pilot with same required context criteria |
| P1 | Six-hour execution risk | Detector/OCR installation can consume the event | First-hour compatibility checks, one backend per task, small pilot | Time one full pipeline run on the actual machine |

## 2. Proposed changes to the inherited design

| ID | Decision | Alternative | Reason / status |
|---|---|---|---|
| D01 | Preserve exact headline; reject invalid whitespace rather than silently normalize | Strip/collapse in input validator | Fixes contradiction with verbatim requirement; proposed |
| D02 | One analyzer call per product, separate planner call per request, same text/vision model | Unconstrained prompt concatenation or separate vendor per step | Incorporates Garmit's staged-model proposal without unnecessary integrations |
| D03 | No copywriter for required ad text | Model creates new advertising copy | User-supplied copy is binding; typography planning is allowed |
| D04 | Two candidates plus one edit, three image dispatches total | N candidates plus independently bounded repair retries | One unambiguous cost/termination bound; proposed |
| D05 | Strict square native output in v1 | Several ratios followed by resize | Avoids ambiguity about whether organizer cap applies before or after postprocessing |
| D06 | Outcome reliability and image verdict are separate | Treat every failure as `failed` or exclude uncertainty without totals | Preserves diagnostic meaning; prevents inflated acceptance metrics |
| D07 | First fully passing candidate by fixed index | Geometric mean of OCR/DINO/context scores | Those scores are not calibrated on a common scale; aesthetic ranking deferred |
| D08 | No label-free product identity guarantee | DINO cosine threshold alone | Embeddings may forgive brand swaps and tiny label errors |
| D09 | Locale-scoped context profiles | Country-wide hemisphere/climate assumptions | Country is the input; scene locale is a disclosed creative assumption |
| D10 | Reference/background text distinguished from headline | Global “no other text” | Otherwise correct packaging labels are removed or falsely penalized |
| D11 | Disable overlays and product compositing initially | Fallback overlay silently rescues a result | Organizer interpretation unresolved; model rendering should be measured honestly |
| D12 | Shared inputs, distinct generation brief and evaluation contract | Judge sees full generation/repair conversation | Reduces intent leakage and keeps evaluator independent of generator explanations |
| D13 | Freeze regression fixtures, but separately collect live model judgments | Replay alone described as proof the judge is correct | Replay proves implementation stability, not model validity |
| D14 | Proposed targets stay proposals until a pilot | Adjust targets after results without a change record | Avoids moving the goalposts |

These changes are presented for Garmit's review. No statement in this document asserts his approval. The latest explicit instruction requesting staged planning is recorded as the source of D02.

## 3. Resolve in this order

### First: product preservation strategy

Recommended v1: end-to-end reference-conditioned generation. It satisfies the named image-model requirement directly and avoids segmentation/compositing engineering. Restrict transformations to what can be verified from a single reference.

Alternative: preserve original product pixels as a cutout, generate background, then composite. This gives stronger control of product appearance but creates edge, occlusion, shadow, lighting and rule-interpretation problems. It is a separate pipeline mode and separate experiment, not an automatic fallback. Revisit only if the pilot shows identity drift is the dominant failure.

### Second: text preparation and fidelity

Separate creative intent from binding copy. The current input contains binding copy only; therefore the planner designs its treatment. Next specify OCR region grouping, strict matching, readability, extra text and label exclusions. A numeric similarity threshold cannot replace the verbatim requirement.

### Third: market/season enrichment

Review 4–6 market/season profiles for the first twenty requests; the full eight-market enum does not require all 32 combinations to be implemented today. Include northern/southern and mild/tropical season interpretations. Do not use “wrong country” as a known-negative label when the visible scene could plausibly occur in both countries. Negatives need observable contradictions to the declared scene contract, with human confirmation.

### Fourth: evaluator calibration

Design the complete product/text/context rubric, reliability rules and thresholds after seeing pilot outputs. Use pilot products/requests for tuning and a separately identified held-out set for reporting. If the same product appears in both, report that the holdout is by request, not evidence of unseen-product generalization.

Actual recorded judge responses on real positive/negative images are needed. Handwritten synthetic responses test branching only. Constructed negatives may accidentally damage multiple dimensions; have the human label all dimensions instead of assuming isolation.

### Fifth: repair utility

Only add repairs once a single-generation-plus-evaluation path is stable. Measure attempted repairs, rescued requests and regressions; never report only successful edits. Defer iterative agentic repair, SAM, extra embedding models and overlays.

## 4. Guarantees we can and cannot make

We can enforce input schemas, immutable contracts, byte-level artifact lineage, decoded output dimensions, finite dispatch counts and code-based selection. We cannot guarantee that a stochastic image model draws the correct product or that a learned evaluator always notices a defect. “Quality assurance” here means measured gates with explicit uncertainty, bounded repair, and refusal to label unverified output as passing.

## 5. Operational context and open items

- Approximately six hours remain, as reported by Garmit.
- Billing is not set up; Garmit can enable it. Budget approval is still needed before inference, not before design.
- Product photos will be sourced by Garmit. Prefer 4–5 clear single-product photos with differing silhouettes and at least two readable labels; retain source/provenance.
- Garmit created `GarmitPant/ad-image-generator-evaluator`; this pack and the original context have been transferred there. Architecture proposals remain pending discussion.
- Organizer permission for overlay/compositing and non-square resizing remains unresolved; disabled defaults avoid making these blocking questions now.
