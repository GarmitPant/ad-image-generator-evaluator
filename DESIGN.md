# Ad generation with evidence-based evaluation

**Design and batch findings · generation/2 · evaluator/3**

This document explains the engineering choices. A deliberate architectural decision is to make execution state and evidence traceable: every candidate and judgment should be inspectable through the inputs, model calls and artifacts that produced it. The [evaluation report](submission/report.md) supplies measured results, the [contact sheet](submission/contact-sheet.html) shows the images, and the [README](README.md) covers setup and commands.

## 1. Problem and success criteria

Generate a product advertisement for a country and season, preserve the supplied product and selected copy, then explain whether each output meets those requirements. The central challenge is judging correctness: an attractive image can still change a product, duplicate a headline or omit a condition from an offer.

Success has three distinct meanings:

- **System completion:** generate, evaluate and save each attempted candidate, with failures recorded.
- **Ad acceptance:** every required evaluation check passes. Uncertainty is explicitly reported.
- **Evaluator accuracy:** agreement with human judgments. This has **not** been measured; automated acceptance rates are not accuracy scores.

## 2. Architecture

```text
Product references + country + season + Exact/Extract copy
    ↓
Normalize references → freeze copy → resolve context → analyze product
    ↓
For each candidate: plan → review/replan once → Gemini image
    ↓
Local OCR + product detection + embeddings + LLM judge
    ↓
Code composes verdicts → ranks candidates → exports images and evidence
```

**The state store underpins the entire flow.** Each stage records its inputs, execution status and outputs in SQLite, with artifacts stored as hashed files. This makes the pipeline inspectable and recoverable at stage boundaries. Evaluation can run on saved generations, so evaluator changes do not require new image-generation calls.

## 3. Decisions and rationale

| Decision | Why it matters |
|---|---|
| SQLite as the shared execution record | Generation, evaluation and reporting use one persistent record of what ran and what it produced. Transactions, foreign keys and local locking support consistency without a separate database service. |
| Explicit artifact lineage | Connect each output and judgment to its inputs, versions and evidence, so failures can be investigated and evaluator changes compared on the same images. |
| Separate copy selection from visual planning | User text is content to render, not instructions for the scene. The planner sees copy roles and lengths, never its wording. |
| Exact or source-span Extract | Exact retains the input; Extract chooses original substrings with protected phrases. This prevents paraphrasing, but a separate semantic check must catch misleading omissions. |
| Shared analysis, separate candidate plans | Analyze all product references once, then produce distinct compositions without repeating shared work. |
| Country facts plus hemisphere-aware seasons | Avoid maintaining a scene template for every country–season pair. This remains a country-level approximation. |
| Hybrid evaluator | Local models provide text, boxes and similarity; an **LLM-as-judge** (a multimodal OpenAI model that sees the reference photos and the ad) answers narrow semantic and visual questions. Neither alone provides reliable evidence for every requirement. |
| Verdicts before scores | A visually similar product cannot compensate for incorrect text. Scores rank candidates only after their verdict tier and failed-check count. |
| CLI, local state and report bundle | Prioritize reproducible runs and inspectable evidence within the hackathon deadline. A UI is unnecessary for inspecting saved results. |

OpenAI `gpt-6-sol` handles analysis, extraction and planning, and serves as the LLM judge. Gemini `gemini-3.1-flash-image` renders square images. Local evaluation uses PaddleOCR PP-OCRv6, Grounding DINO tiny and DINOv2 small. These are task assignments, not a claim that comparative testing proved the models best.

## 4. How evaluation works

| Dimension | Evidence and decision |
|---|---|
| Text selection (input → copy) | Code validates exact spans, protected content and capacity. For Extract, the LLM judge checks meaning, relevance and essential omissions. Negative semantic judgments require a quote from the source. |
| Text rendering (copy → image) | OCR reads without seeing expected copy. Code groups nearby lines and matches expected blocks to disjoint observed lines. It checks missing, altered, duplicated and extra ad text, with character/word error diagnostics and a legibility proxy. |
| Product | Detection provides candidate product regions. The LLM judge checks count, type, shape, colours and materials, distinctive parts and visible branding against all references. Position and viewing angle are not identity requirements. |
| Context | Narrow LLM-judge questions check seasonal consistency, country plausibility and image-level policy violations. Country recognisability is diagnostic rather than a required pass condition. |

Text matching tolerates whitespace reflow while retaining a strict comparison diagnostic. Text inside detected product regions is treated as product labeling rather than extra ad copy. This is a practical heuristic, not perfect text-region classification.

DINOv2 similarity compares product crops with references. It remains an uncalibrated diagnostic and tie-breaker, not a hard identity threshold. Product-count acceptance currently requires the LLM judge to count exactly one and the detector to find at least one; this is corroboration, not strict agreement on the exact count.

Each required check returns **PASS, FAIL or UNSURE**. A failed required check fails the candidate; otherwise unresolved required checks prevent a pass. Infrastructure failure is recorded separately. OCR unavailability becomes UNSURE, although unmatched expected text becomes FAIL; an OCR detection miss can therefore cause a false rejection.

Ranking order is: verdict → fewer failed checks → score → country recognisability → product similarity → plan guardrail status → candidate index. `best.png` means highest-ranked available candidate; `approved` is true only when the selected candidate passes overall. Scores are heuristics, not probabilities.

## 5. Guardrails and iteration

Current policy permits regional architecture, materials, food settings and background landmarks. It prohibits caricatures of people, flags/national emblems and religious imagery, with additional people, alcohol, season and text rules. This replaces an earlier policy that suppressed too much regional character.

Before generation, keyword checks and a model reviewer inspect the plan. One replan is allowed. A second rejected but valid plan is still generated and flagged; image evaluation then checks the actual output. Plan approval alone is never image approval.

The pilot exposed evaluator failures, not generation failures: all six pilot ads were correct, but three were falsely rejected. Overlapping OCR boxes split a headline, wrapped copy exceeded the line-matching limit, and bottle-label text was mistaken for extra ad copy. A revised evaluator adjusted line grouping, wrapping and label exclusion, and the three cases became regression fixtures. The pilot images were then re-scored without regeneration. These changes demonstrate debugging against evidence; they do not establish evaluator accuracy.

## 6. State store, traceability and recovery

**Persistence is part of the pipeline design, not just logging added at the end.** Generation is stochastic and evaluation is fallible. A final image and score alone cannot explain whether a problem came from copy selection, planning, rendering or the evaluator. The state store preserves the intermediate evidence needed to investigate that distinction.

SQLite holds run, stage, candidate, model-call, evaluation and selection records. Larger artifacts live in content-addressed files; their SHA-256 identifiers connect them to the stages that consumed or produced them. This separates execution metadata from image and evidence storage while retaining an explicit chain:

```text
Request + references → selected copy + plan + prompt → candidate image
Candidate image + evaluator configuration → evidence + verdict → ranking
```

| Deliberate mechanism | Engineering benefit |
|---|---|
| Stage input fingerprints and artifact hash checks | Reuse completed work only when its recorded inputs/configuration match; detect changed or corrupted artifacts. |
| Recorded model requests, receipts, usage and returned model IDs | Inspect what was asked, what was returned and the estimated cost of that execution. |
| Versioned evaluation stages | Re-score identical saved images with a revised evaluator while retaining earlier evaluation records. This was used for the pilot corrections. |
| Recorded responses and offline replay | Reproduce downstream behavior for regression tests without another stochastic or paid provider call. |
| Per-candidate state and evidence exports | Keep successful images when another candidate fails, and connect report verdicts to detailed evidence. |

Provider dispatch is committed before sending. If a call's outcome is uncertain after interruption, it is not automatically resent; SDK retries are disabled. Local locks protect concurrent execution of the same run. This is stage-level recovery, not a distributed queue or an exactly-once guarantee. Cost estimates are report-only; spending controls remain on provider accounts.

Traceability makes decisions explainable and experiments repeatable on recorded evidence. It does **not** make the evaluator's judgments correct or guarantee identical images from a fresh generation call.

## 7. Batch results and what they demonstrate

The saved submission contains **9 live requests and 27 generated, evaluated images**, with no synthetic runs. It covers all eight countries and four seasons, five Exact and four Extract requests, and one-, two- and three-reference inputs. All candidates used `generation/2` and `evaluator/3`; all 27 evaluations recorded execution status `ok`.

| Automated outcome | PASS | FAIL | UNSURE |
|---|---:|---:|---:|
| Text selection | 27 | 0 | 0 |
| Text rendering | 25 | 2 | 0 |
| Product | 22 | 1 | 4 |
| Context | 26 | 1 | 0 |
| **Overall** | **20** | **3** | **4** |

**Eight of nine requests had an approved winner.** Country recognisability, a separate diagnostic, returned 23 PASS, 3 FAIL and 1 UNSURE. Text-selection results are shared across a request's candidates: 27 candidate-level passes do not represent 27 independent copy-selection tests.

Three evidence-linked examples illustrate the design:

- **An approved result:** [Australian sunglasses, candidate 2](submission/evidence/b1-02-sunglasses-au-summer-extract__db9d6da9-c2.md) passed every required check. Its evidence card connects the verdict to expected/read copy, product checks and scene judgments.
- **A high score cannot erase a failure:** [German bottle, candidate 2](submission/evidence/b1-04-bottle-de-winter-extract__d897ef86-c2.md) scored **1.0**, but OCR reported unplanned `t1`, `t2`, `t3` text. The required extra-text check failed, so a passing candidate ranked above it despite its high product similarity. The score measures selected dimensions of quality; it is not an approval probability.
- **Uncertainty is retained:** [US Jeep, candidate 1](submission/evidence/b1-18-jeep-us-summer-exact__05359b90-c1.md) was selected but **not approved**, because the judge did not resolve the distinctive-components check. All three candidates for that request remained UNSURE; selection did not manufacture a passing result.

The median recorded generation-stage time was **34.01 seconds per candidate**, and evaluation time was **22.54 seconds**; these are not full-request wall-clock times. Recorded cost estimates totalled **$2.874**: $2.349 for candidate generation, $0.445 for evaluation-judge calls and $0.080 for shared request-level calls across the batch. These are token-based estimates, not provider invoices or a valuation of local compute.

**Methodological boundary:** requests 01 and 02 were used to refine the evaluator. Their six rescored candidates all passed; the remaining 21 produced 14 PASS, 3 FAIL and 4 UNSURE. The combined set is not a fully held-out benchmark. There are no human labels, so these counts describe automated judgments, not measured evaluator accuracy or verified image correctness.

Figures were checked against [results.json](submission/results.json) and [requests.jsonl](submission/requests.jsonl). The [full report](submission/report.md) and [contact sheet](submission/contact-sheet.html) retain every candidate and its ranking; the linked evidence cards make individual decisions inspectable.

## 8. Limitations and next steps

Thresholds are provisional. OCR, detection and LLM-judge answers can be wrong. The LLM judge shares a model family (OpenAI) with the planner and plan reviewer, though not with the image generator (Gemini). Country plausibility is weaker than recognisable localization. Region exclusion can hide ad text that overlaps a product. Small similarity differences need not mean perceptible quality differences. The batch is a small demonstration, not evidence of broad generalization or model superiority.

Next priorities: independent human labels, per-dimension false-alarm/missed-failure measurement, a frozen held-out evaluation, and targeted improvement of uncertain cases. Add models or a UI only after establishing whether the evaluator is trustworthy.
