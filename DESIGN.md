# Ad generation with evidence-based evaluation

**Design draft · reviewed against commit `441eff7` · batch results pending**

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

## 7. Results to attach after the batch

The current plan is **9 requests × 3 candidates = 27 images**; report actual attempts and completions, not the planned count alone. Derive coverage from the requests actually run—the older 20-request coverage table is stale.

Keep this section short: attempted/generated/evaluated counts; PASS/FAIL/UNSURE by dimension; approved winners; estimated cost and latency; and three linked examples—a pass, a generation failure and an evaluator limitation. Link the full report rather than duplicating its candidate tables.

The two pilot requests informed evaluator changes and are development data, even after rescoring. Identify them separately. There are no human labels in the final batch, so report automated outcomes without calling them measured accuracy or a fully held-out benchmark. Confirm evaluator/config versions before aggregating results.

## 8. Limitations and next steps

Thresholds are provisional. OCR, detection and LLM-judge answers can be wrong. The LLM judge shares a model family (OpenAI) with the planner and plan reviewer, though not with the image generator (Gemini). Country plausibility is weaker than recognisable localization. Region exclusion can hide ad text that overlaps a product. Small similarity differences need not mean perceptible quality differences. The batch is a small demonstration, not evidence of broad generalization or model superiority.

Next priorities: independent human labels, per-dimension false-alarm/missed-failure measurement, a frozen held-out evaluation, and targeted improvement of uncertain cases. Add models or a UI only after establishing whether the evaluator is trustworthy.
