# Evaluation architecture and source-to-image text contract

Version 0.3 · 2026-09-26 · User-confirmed priorities, proposed technical contracts. v0.3 updates the generation-side references to match document 01 v0.3 (LLM planner, general guardrails, OpenAI LLM stages, state store)

## 1. Scope and authority

Garmit's latest clarification establishes three requirements:

1. This repository contains both design and implementation; a separate coding agent implements here.
2. The hackathon assessment emphasizes engineering of automated evaluation: methods, criteria and evidence. Generation needs to function; optimizing its beauty or success rate is secondary.
3. Freeform input supplies textual content, not visual art direction. Select relevant content from it, preserve some content verbatim, and evaluate source content against the selected copy and text actually rendered in the image.

These supersede the earlier blanket rule that the entire input must always be rendered unchanged. The original organizer wording is preserved in `docs/context/`; record the revised product interpretation accurately rather than editing that historical source. An Exact policy supports the original whole-input requirement. Garmit explicitly selected Exact/Extract modes with optional protected phrases in this conversation. This mode mechanism is confirmed; detailed limits and schemas remain technical proposals.

This document is the primary evaluator contract. Model choices and numeric quality thresholds remain proposals until measured. No percentage weights for hackathon judging were supplied; do not invent them or confuse judging emphasis with weights inside the image-quality verdict.

## 2. Minimal system

```text
Product image ──► normalize + optional cached product profile ──────────┐
Geography + season ──► resolved context ──► planner + guardrails ───┤
Source text + text policy ──► content selector ──► TextPlan ───────────┤
                                                                    ▼
                                           deterministic prompt compiler
                                                                    ▼
                                                one Gemini image generation
                                                                    ▼
                                            final image + immutable manifest
                                                                    ▼
                      standalone evaluator (also accepts external fixture images)
                 ┌──────────────────┬───────────────────┬────────────────────┐
                 │ source→copy      │ reference→product │ scene requirements │
                 │ copy→render      │ presence/identity │ visible adherence  │
                 └──────────────────┴───────────────────┴────────────────────┘
                                                                    ▼
                               typed evidence + code-composed verdict + report
```

The selector uses the OpenAI structured client (proposed `gpt-6-sol`). It has no tools and cannot change scene context or reference facts. The creative planner (document 01 §3 S5) designs the scene from the product profile and resolved context, and sees only text roles and lengths, never the copy. Guardrail status (`approved`, `approved_after_replan`, `rejected_after_replan`) is read from the state store and reported by the evaluator.

Evaluation is a library/CLI boundary, not a hidden helper inside generation. The same evaluator must run on generated outputs, curated genuine outputs, mutated images and replay fixtures without calling generation. This makes its behavior independently testable.

## 3. Source and plan contracts

### TextInput

```text
schema_version: text-input/2
source_text: original Unicode string, 1–2000 code points
policy: exact | extract              # user-confirmed explicit mechanism
protected_spans: [{start, end}]      # optional in extract mode
```

Persist the input exactly before doing any normalization. Permit multiline source prose, unlike v0.1's short-headline-only input. Reject null/unsafe control input with a specific error; treat line breaks as source structure, not silently discarded content. Do not derive scene/style instructions from this field, even if it contains imperatives or appearance words.

Require an explicit policy for new requests. A compatibility adapter may map legacy v1 `ad_text` requests to `exact`, recording the conversion. Do not silently switch an oversized Exact request into Extract. Garmit confirmed this explicit mode selection; UI presentation remains out of scope.

Offsets are zero-based Unicode code-point offsets with half-open `[start,end)` semantics into the stored, unnormalized `source_text` (Python slicing semantics). Validate nonempty ranges, bounds and exact substring equality. A TypeScript client must translate UTF-16 indices or send selected strings for server-side resolution. Never compare offsets computed over a normalized string with the original.

A CLI or later UI may accept protected phrases as strings. Resolve them to source spans before creating the contract; reject a phrase absent from the source. Proposed simple rule: protect all exact occurrences by default, recording the resolved spans, and allow explicit occurrence selection when provided. Do not require a human to calculate Unicode offsets. Overlapping protected spans are coalesced for coverage while retaining the original phrase references.

### SourceContract

Freeze before image generation:

- Source hash, policy, explicitly protected span IDs and copy-length/layout limits.
- Any explicitly declared `must_include` groups and `inseparable_groups` linking an offer/claim to a qualifier. Human annotations in the evaluation dataset can supply these.
- Source interpretation provenance: user-declared, human-labelled, or model-inferred.
- Model-inferred required content is a hypothesis, not ground truth or a self-issued exemption. Retain it for audit; independently evaluate it.

Do not require users to annotate every sentence for baseline operation. In extract mode without extra annotations, a source-to-copy semantic judge checks omission/relevance/qualifier preservation and can abstain. For the labelled benchmark, annotate salient content independently before viewing selector outputs, enabling a real test of this judge.

### TextPlan

```text
schema_version: text-plan/2
source_sha256: string
source_contract_sha256: string
selection_method: full_input | model_extract | human_supplied
selector_model_and_prompt_version: nullable metadata
blocks:
  - block_id: stable ID
    role: product_name | tagline | offer | qualifier | supporting_text
    source_span: {start, end}
    exact_text: source_text[start:end]
    order: integer
    render_requirement: exact
    proposed_layout_zone: template zone ID
omitted_spans: [{start, end, reason_code}]
warnings: typed list
plan_sha256: string
```

Initial extraction is **extractive**, not paraphrasing: each block is a contiguous source substring. Multiple blocks are allowed. A selector cannot splice arbitrary words into a new sentence or change numbers, product names, currency, case or punctuation. This is a scoped starting point, not a claim that extractive copying alone preserves meaning.

Proposed rendering budget: ≤4 text blocks, ≤120 visible non-whitespace code points total, ≤20 words for the initial English OCR profile. These are pilot defaults, not organizer rules. Count/validate in code. If mandatory copy exceeds capacity, return `copy_capacity_exceeded`; do not truncate or drop a qualifier. Source length and rendering capacity are different constraints.

In Exact mode, content is the full input with its order preserved. Layout may wrap at whitespace boundaries under the declared whitespace-equivalence policy; do not remove visible characters. Original source lines can map to separate blocks. If the input cannot fit, ask for revised content or a supported format; generation is not dispatched.

In Extract mode, preserve all explicit protected spans, including repeated occurrences distinguished by offsets. They must be contained in selected blocks and appear with required multiplicity. Do not infer that a comma-separated input is visual direction. A selected product name or tagline becomes binding renderer input even when the original prose was much longer.

`omitted_spans` cover the complement of selected source spans; compute this partition in code rather than trusting a model's coverage arithmetic. Explanations are advisory. Codes can include `background_prose`, `redundant`, `lower_relevance`, `unsupported_to_select`, and `capacity_conflict`. A capacity-conflict omission of required content is a failed plan, not a valid shortcut.

### Validation before paid image generation

Reject unknown keys, invalid offsets, altered substring text, duplicate block IDs, overlapping/repeated content inconsistent with the policy, protected-span omissions, impossible mandatory groups, and capacity overflow. Validate that the source/contract hashes match. A schema-valid plan is not automatically semantically faithful; structural and semantic checks remain distinct.

Do not silently fall back to “first 120 characters” when selection fails. Return `invalid_text_plan` with diagnostics. A separately recorded human-selected plan is supported for progress and is reported as human intervention, not automated selection success.

## 4. Isolating text from visual art direction

The generation compiler has independent fields:

- Visual scene: typed geography, season, resolved context, validated CreativePlan and product reference.
- Copy to render: frozen TextPlan blocks with exact strings and simple placement guidance.

Do not send raw freeform prose as creative instructions. Give the image model only selected render strings, clearly labelled as literal copy, plus the independent scene plan. A line such as “Winter savings” is rendered as text; it does not override a structured summer scene. An explicit input conflict may be reported separately without silently rewriting either input.

The source-to-copy evaluator receives original prose, policy, protected spans, declared content groups and selected blocks. The render evaluator receives expected blocks only **after** blind image transcription. Neither consumes the generator's explanation or the selector's rationale as evidence of correctness.

## 5. Text evaluation: two required verdicts

### A. Source → selected copy: content fidelity

Question: did the pipeline select appropriate, source-supported content without omitting required details or changing meaning?

| Check | Method | Pass semantics |
|---|---|---|
| Span integrity | Code verifies offsets and exact source substrings | Every selected block supported |
| Exact policy coverage | Ordered source/block alignment | All visible input characters retained under declared whitespace policy |
| Protected coverage | Code checks inclusion/multiplicity | Every protected occurrence retained |
| Declared dependency groups | Code checks all required group members | Claim is not separated from mandatory qualifier |
| Salient content coverage | Human gold labels for benchmark; atomic source-to-copy judge for runtime | Essential content retained; omitted background prose is allowed |
| Meaning preservation | Judge examines original source and selected copy | No misleading omission, lost negation, changed attribution or implied broader offer |
| Relevance | Judge assesses selected vs omitted source content | Copy concerns the supplied product/offer; selection of only generic filler fails |

The semantic judge returns `yes|no|unknown` per atomic question with exact evidence quotes and source offsets where applicable. Code checks that evidence actually occurs in the source/selected text. This verifies grounding of the quote, **not the truth of the judge's inference**. No model-supplied overall verdict or uncalibrated numeric confidence is used as acceptance.

Avoid judging against a reference extraction as the only correct answer: multiple selections can be valid. Human labels specify required facts, allowed omission and forbidden implication, then label each candidate plan. For an annotated dataset, use required-group coverage rather than full-source character recall. On unannotated live inputs, keep semantic coverage as judged evidence and disclose uncertainty.

### B. Selected copy → image: rendering fidelity

Question: does the image visibly contain the selected text accurately and legibly?

1. Run OCR without passing expected text to the OCR/transcription model. Save recognized strings, polygons and engine confidence. A second VLM transcription, if used, must be blind to source/expected copy too.
2. Group OCR lines into spatial blocks with deterministic ordering. Preserve case, punctuation, digits and symbols. Normalize only explicitly permitted whitespace/reflow; retain raw transcript for diagnosis.
3. Match expected blocks to observed blocks with **one-to-one** assignment. One visible occurrence cannot satisfy two required instances. Support multiple lines inside one spatial block; prohibit constructing a match from unrelated words across the image.
4. Use layout zones as search hints, not proof that absent text exists. Required ad copy on a packaging label does not automatically satisfy a requested headline block. Distinguish headline/body areas from product-label regions and unrelated background signage.
5. Compute exact visible-text equality, character edit rate, word edit rate, missing blocks, duplicate/unexpected blocks and symbol errors. CER/WER are diagnostic; a one-character change can still be a decisive failure.
6. Assess readability at the delivered image resolution: clipping, overlap, occlusion, contrast and size. OCR confidence alone does not certify legibility. Specify/validate this criterion against human labels during the pilot.
7. If OCR uncertainty is material, use an independent blind reader once or return unknown. Two agreeing learned readers can still be wrong; human-labelled calibration is mandatory.

Definitions per expected block E and observed aligned block O:

`CER = Levenshtein(E,O) / max(1,len(E))`; it may exceed 1 with many insertions. Do not silently clip it and then call it error rate. WER is the equivalent operation over tokens. Report strict exact-match rate separately from whitespace-equivalent match. Never casefold or normalize currency/percent signs for an exact verdict.

Unexpected product-label text is evaluated under product fidelity, not automatically counted as invented ad copy. A detected string appearing elsewhere in the source is still unexpected if it was not selected for this image, unless the contract explicitly permits it. Evidence must identify the region and rule, not only aggregate token counts.

### C. Composing text verdicts

`text.pass = selection_content.pass AND rendering.pass`.

Retain each stage's status and failed checks. Correct pixels cannot rescue an unfaithful extraction; faithful extraction cannot rescue a misspelling. When extraction omits irrelevant prose validly, do not compute whole-source OCR mismatch and call it a rendering failure.

If TextPlan is missing for an externally supplied image, Exact mode can derive full-input expected copy. Extract mode requires an explicitly supplied plan or human-labelled expected content; otherwise rendering-to-plan is unknown. Do not reverse-engineer a plan from the visible output and then congratulate it for matching itself. Source-to-image semantic assessment may still be reported separately.

## 6. Other evaluator dimensions

### Product fidelity

Use the original reference, not merely a generated ProductProfile. Grounding DINO localizes candidate products; DINOv2 crop similarity is one identity signal. Report detector confidence, boxes, duplicate hypotheses, crop preprocessing and embedding values. A no-detection event is not conclusive proof of no product; use human calibration and optional independent visual evidence.

Require an explicit attribute rubric: silhouette/proportions, key color/material, distinctive components, visible branding/label, count and main-subject visibility. Distinguish admissible viewpoint/lighting differences from altered identity. If labels are unreadable in the reference, do not invent a required transcription. If a mandatory identifying feature is unobservable in the output, return unknown/fail according to its predeclared visibility rule.

Same-category wrong-brand products are essential negatives. Global similarity alone is insufficient. Masked color difference is optional and must not fail legitimate lighting changes without calibration. No universal DINO or color threshold is asserted in this document.

### Context adherence

Use atomic, observable predicates derived from the **resolved context and the general guardrail policy**: season/climate consistency (band × season contradiction table), absence of guardrail violations (stereotype, tokenism, religious decoration, age-restricted-product rules), and a plausible non-contradictory setting for the country. Do not derive pass criteria from the planner's own `context_cues`. That would let the generator define its own test. Planner cues may be checked as a separate diagnostic ("plan realization"). Separate required checks, forbidden contradictions, optional embellishments and ambiguous observations. Generic scenery can be plausible in several countries; do not claim precise geographic identification from weak cues. Report runs flagged `rejected_after_replan` separately, with their guardrail check results.

The judge answers each predicate with `yes|no|unknown`, region description and short evidence. Question dependencies prevent assigning correct color/season to an absent object. Required checks and their composition are defined in a versioned rubric, not generated after viewing the image. Raw freeform text is not a scene-style target.

### Technical gates

Decode image, inspect dimensions/aspect and detect invalid/empty output before expensive image judgments. Blankness heuristics require care with minimalist ads; low variance alone is not a universal rejection. Record a testable technical failure separately from uncertain semantic quality.

## 7. Evaluation record and composition

```text
EvalRecord:
  evaluation_id, schema_version
  input_hashes: source, policy, plan, reference, final_image, context
  versions: rubric, thresholds, preprocessing, models, prompts, SDKs
  gates: check results
  text_selection: DimensionResult
  text_rendering: DimensionResult
  product: DimensionResult
  context: DimensionResult
  overall_verdict: pass | fail | unknown
  execution_status: ok | degraded | failed
  errors, cost, latency, artifact_paths

DimensionResult:
  verdict: pass | fail | unknown
  observations: typed raw evidence
  required_checks: [{id, verdict, evidence_refs, threshold_ref?}]
  diagnostics: named values with units and definitions
```

Code composes required checks: any reliable required failure establishes fail; otherwise any unresolved required check establishes unknown; all required checks passing establishes pass. Preserve failed checks even if some other subsystem crashes. `execution_status` independently describes whether evidence collection succeeded reliably.

No weighted average may let a good background cancel wrong copy or a different product. Optional research scores remain diagnostic. The judges' emphasis on eval engineering does not imply invented numeric weights among text/product/context.

## 8. Evidence that the evaluator works

Separate four test layers:

1. **Pure unit tests:** string/offset math, assignment/multiplicity, schema validation, rubric truth tables, unknown propagation, threshold boundaries, cache invalidation.
2. **Offline integration/replay:** actual stored OCR/detector/judge observations and real image fixtures reproduce decisions; missing fixtures fail without network. Synthetic responses exercise failures but are labelled synthetic.
3. **Behavioural evaluation:** human-labelled real images/plans, positives and targeted negatives; measure confusion matrices and abstention per dimension, not just overall pass rate.
4. **Metamorphic checks:** benign layout/font/view changes should preserve labels; one-character/brand/season changes should alter only the intended verdict where possible. Humans inspect side effects of mutations.

### Dataset and split

Prepare ~4–6 development requests separately from the approximately twenty output images required for submission. Pilot outputs tune prompts, thresholds and criteria; freeze them before the held-out report. Twenty requests are a small demonstration, not a statistically robust benchmark. If products repeat across splits, call the holdout a request holdout, not product generalization.

Cover Exact and Extract policies; product names; taglines; numbers/currency; long prose with irrelevant sentences; repeated terms; negation/qualifiers; readable product labels; northern/southern and mild-weather season profiles. Include actual generation failures, not just images manually made bad. Preserve all attempted requests and selection failures so the dataset is not curated to only easy successes.

Label raw image quality first, blind to machine scores and generator identity. Label source→plan separately. For extraction, record acceptable alternatives rather than one exact gold string. Keep label instructions, annotator identity/count and disagreement/adjudication notes. With one annotator, state single-rater limitations; do not invent inter-rater agreement.

### Minimum text negative matrix

| Case | Expected stage verdict | Why |
|---|---|---|
| Relevant short tagline extracted from longer prose; faithfully rendered | Both pass | Full prose is not required in Extract |
| Protected product name omitted; remaining words correctly rendered | Selection fail, rendering may pass | Wrong selected content |
| Source “Up to 20% off selected items”; selection “20% off” | Selection fail or unknown pending rubric evidence, never structural-pass alone | Loss of qualifier can change offer meaning |
| Source “Not waterproof”; selection “waterproof” | Selection fail | Exact substring alone is not faithfulness |
| Correct plan; image changes 20% to 30% | Rendering fail | Numeric substitution |
| Required two occurrences; only one visible | Rendering fail | Multiplicity violation |
| Same copy, changed font/line wrapping with clear readability | Rendering pass | Allowed visual variation |
| Correct-looking OCR match only inside tiny product label | Headline rendering fail/unknown | Wrong region/role and potential illegibility |
| Extra invented discount or CTA | Rendering fail | Unplanned ad copy |
| OCR readers disagree on a symbol | Unknown/degraded unless resolved | Avoid treating measurement error as certainty |
| Full-source text preserved in Exact mode but important word clipped | Rendering fail | Semantic content exists in plan, not readable output |

For the qualifier test, the final pilot rubric must freeze an unambiguous expected label for the actual fixture; the table's conditional wording is a design caution, not permission for a regression test to accept arbitrary outputs.

### Report

- For each dimension: TP/FP/TN/FN against human labels, precision/recall for failure detection, false-accept/false-reject counts, abstentions and evaluation coverage. Declare which class is positive; proposed positive = defective/failing.
- Report Cohen's kappa only where defined/useful; state undefined cases and label imbalance. Counts matter more than one aggregate score.
- Report separately: source-selection acceptance, plan-render exact match, end-to-end text acceptance, product and context acceptance.
- End-to-end yield denominator is all requested cases; conditional reliability metrics include only defined evidence and show excluded counts beside them. Do not present success-conditioned numbers as whole-pipeline quality.
- Freeze thresholds and show the dev distributions that motivated them. If a threshold changes after holdout inspection, mark the holdout contaminated and report exploratory results rather than pretend it remained held-out.
- Repeat a small fixed judge subset with genuine independent calls; report verdict flip counts and abstention changes. Cached replay is not a stability measurement.
- State per-stage latency/cost and pipeline failures. No target percentage is claimed achieved before results exist.

## 9. Reproducibility and evaluator failure cases

Cache by source text/policy/protected spans, TextPlan, reference image, output image, context/rubric, model/config, prompt/schema, preprocessing and threshold hashes. Judge repeats add replicate ID. A changed extraction must invalidate text-render matching even when the image bytes are unchanged.

Schema-invalid or truncated judge responses produce typed errors. No silent prose-to-JSON repair changes the judgment. Missing OCR, unavailable weights or missing replay fixtures do not receive zero-error defaults. Record dependencies and weight revisions; offline tests must not require hidden downloads.

Spend is bounded by a run-wide ledger and explicit approved limits. One source-semantic judge call plus one visual context/product call can be a provisional layout for cost control; retain separate prompts/evidence and calibrate each responsibility. Blind transcription, when needed, is a separate call with no expected-text leakage. No inference has been authorized by this specification.

## 10. Implementation priority

First deliver a functional single-image generator and immutable source/TextPlan/image artifacts. Then spend the majority of engineering effort on the evaluator, real fixtures, human labels, failure tests and a defensible report. Add candidate selection, repairs, additional model comparisons or UI only after the core evaluation evidence is complete.
