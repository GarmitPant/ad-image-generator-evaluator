# Challenges and decision history

Version 0.4 · 2026-09-26

## 1. Confirmed changes

- This repository holds implementation and design.
- Evaluation engineering is the main judged deliverable; generation is implemented first (v0.3).
- Freeform text is source content, not look-and-feel instructions.
- User selects Exact or Extract mode; optional protected phrases remain unchanged.
- Text evaluation must cover both selection from source and actual rendering.

These requirements come from Garmit's latest messages. Model IDs, extraction implementation, numeric thresholds and spending envelope remain proposals.

## 2. Current major challenges

| Priority | Challenge | Failure mode | Control / evidence |
|---|---|---|---|
| P0 | Selection meaning | Extracted substring drops “not,” “up to,” conditions or product identity | Structural span checks plus independent semantic content evaluation; human-labelled alternatives |
| P0 | Rendering fidelity | Correct plan, wrong digit/symbol/case or illegible text | Blind OCR, spatial one-to-one matching, exact/CER/WER evidence and readability labels |
| P0 | Circular evaluation | Selector defines what matters and evaluator only checks the selector's own target | Independently supplied source obligations/human labels; keep source→plan and plan→image checks separate |
| P0 | Product identity | Similar category passes embedding test despite wrong brand | Original-reference comparison, attribute/label evidence and same-category negatives |
| P0 | Ambiguous geography | A plausible scene occurs in many countries | Evaluate declared observable cues, not confident country guessing; permit unknown |
| P0 | Learned-check errors | OCR/detector/judge mistake becomes an overconfident pass/fail | Typed uncertainty, cross-checks where useful, human calibration and coverage reporting |
| P0 | Test validity | Synthetic JSON fixtures are mistaken for evidence of judge quality | Real labelled images and recorded observations plus separate unit/replay tests |
| P1 | Content/style separation | Copy mentioning “winter” overrides structured summer scene | Never use raw source as creative instructions; selected strings are literal display content |
| P1 | Selection variability | Several extractions are valid, one gold string rejects alternatives | Label required facts/qualifiers and acceptable omission rather than one exact output |
| P1 | Small sample / tuning leakage | Thresholds tuned on held-out data or failures excluded | Freeze dev decisions; retain all attempts, report counts and split limitations |
| P1 | Event time | Generation work displaces evaluation | One image per request; bounded planner/guardrail calls; probe OCR/weights early; defer repairs/UI |
| P0 | Stereotyped geography | Planner encodes places through people, dress, flags or wildlife | General guardrail policy, code lexicons plus reviewer, one replan, flag carried into evaluation |
| P1 | Planner self-grading | Evaluator checks the planner's own cues | Context predicates come from resolved context and policy, not from CreativePlan |

## 3. Decision register

| ID | Current decision / proposal | Status |
|---|---|---|
| D01 | Whole-input preservation applies to Exact; Extract permits selected spans | v0.1 blanket rule superseded by user-confirmed modes |
| D02 | Separate content preparation and rendering responsibilities; aesthetic planner optional | Separation retained; "planner optional" superseded by D17 |
| D03 | Exact uses code; Extract selects relevant source-backed content | Modes confirmed; extractive-only implementation proposed |
| D04 | One image call and no automatic repair initially | Image-count part superseded by D24; no-repair retained |
| D05 | Strict square ≤1024 baseline | Retained proposed technical policy |
| D06 | Reliability separate from quality verdict; unknown is not pass | Retained |
| D07 | No initial ranking; accept only fully passing singleton output | Superseded by D24/D25; "approve only a passing output" retained |
| D08 | Product identity needs more than embedding similarity | Retained |
| D09 | Locale-scoped scene profiles; source prose has no style authority | Scene-profile part superseded by D18; "source prose has no style authority" retained |
| D10 | Product-label text separated spatially from ad copy | Retained; role/multiplicity checks needed |
| D11 | Overlay/compositing deferred | Retained |
| D12 | Evaluate source→copy and copy→render independently | Expanded to prevent selection errors being hidden by accurate rendering |
| D13 | Replay is regression evidence; human labels validate judge behaviour | Retained |
| D14 | Freeze thresholds before holdout; targets are not results | Retained |
| D15 | Shared repository for implementation and design | Confirmed by Garmit |
| D16 | Evaluation methods, criteria and evidence receive engineering priority | Confirmed by Garmit; no numeric judging weights supplied |
| D17 | LLM creative planner (S5) designs scene/layout; sees text roles + lengths only | Confirmed by Garmit (v0.3); supersedes the "planner optional" part of D02 |
| D18 | Geography/season enums + per-country facts row; general guardrails instead of per-pair registry | Confirmed by Garmit; supersedes D09's locale-scoped scene profiles |
| D19 | Guardrails: code checks + LLM reviewer; one replan; then generate and flag `rejected_after_replan` | Confirmed by Garmit |
| D20 | SQLite state store for stage state, artifacts, calls, events | Confirmed architectural requirement; schema proposed in document 06 |
| D21 | OpenAI for LLM stages; Gemini for images; no Anthropic code now | Confirmed by Garmit; model IDs proposed |
| D22 | Generation implemented before evaluator | Confirmed by Garmit; evaluation emphasis unchanged |
| D23 | Repository commits placeholder `.env.example` only; users supply keys | Confirmed by Garmit |
| D24 | 3 candidates per request (configurable 1–4), one creative plan per candidate | Confirmed by Garmit (v0.4) |
| D25 | Evaluate every candidate; rank in code (verdict tier → failed checks → score → guardrail → index); present best, approved only if pass; keep all | Proposed ranking rule; flow confirmed by Garmit |
| D26 | Per-dimension scores (0–1) and unweighted overall score for ranking only; verdicts gate | Proposed; uncalibrated |
| D27 | Guardrails simplified: static predefined policy file, global rules + optional country notes, keyword check + approve/reject reviewer; no web lookup | Confirmed by Garmit; supersedes v0.3 per-rule evidence review |
| D28 | 1–3 reference images per product | Confirmed by Garmit |
| D29 | Save all candidate images; export winner + summary to `outputs/` | Confirmed by Garmit |
| D30 | Evaluator vision models local only (PaddleOCR, Grounding DINO tiny, DINOv2 small) behind swappable interfaces; hosted later if needed | Confirmed by Garmit |
| D31 | Batched evaluation after the single-request generate→evaluate→select flow works | Confirmed by Garmit |

Prior rationale is preserved in Git history. The root decision register records human direction; do not infer collective architecture approval from repository setup.

## 4. Next design sequence

1. Review the source→copy / copy→render contract and test cases in document 05; Exact/Extract mode choice is already confirmed.
2. Specify operational OCR block grouping, matching, legibility and abstention rules using the actual pilot outputs.
3. Freeze product-identity attributes and context predicates with positives and targeted negatives.
4. Calibrate thresholds and judge decisions on development labels, then report held-out results.
5. Only then consider improved generation, repair or UI.

The evaluator can enforce schema/lineage/offsets/dimensions/policy composition exactly. It cannot guarantee perfect interpretation of pixels or semantics. Quality claims must match observed evidence, not architectural ambition.

## 5. Operational status

At the last operational update billing and product photos were pending and no API spend was approved. The earlier approximately six-hour estimate is historical, not a fresh remaining-time estimate. Repo is GarmitPant/ad-image-generator-evaluator. Initial v0.1 design was published at be35572; current updates supersede its generation-first assumptions.
