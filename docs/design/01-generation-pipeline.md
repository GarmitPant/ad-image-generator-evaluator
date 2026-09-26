# Functional generation baseline

Version 0.2 · 2026-09-26 · Supersedes v0.1 generation priorities

## 1. Purpose

Generate a usable ad and an auditable record for the evaluator. Evaluation engineering is the primary deliverable. Use one image per request and a simple fixed layout initially; no aesthetic ranker, mandatory best-of-two, dedicated art-director agent or repair loop.

The authoritative text and evaluation contracts are in [05-evaluation-and-text-contract.md](05-evaluation-and-text-contract.md). This document specifies only the generation boundary, operational behavior and future extensions. Original v0.1 remains available in Git history.

## 2. Request

Proposed Pydantic models use explicit schema versions, forbidden extra fields and bounded values.

| Field | Contract |
|---|---|
| request_id | Human-readable tracking ID; not content identity |
| product_image | Local PNG/JPEG/WebP reference; decoded and hashed |
| geography | Supported ISO country enum backed by a reviewed registry entry |
| season | spring, summer, autumn, winter |
| text | TextInput: source_text, explicit exact/extract policy, optional protected spans |
| aspect_ratio | 1:1 in baseline |

Source text may be longer than the visible copy. It is not an aesthetic brief. Never reuse the v0.1 assumption that every input is already a ≤60-character headline. Exact mode retains full content; Extract produces selected source spans. Both use the render-capacity preflight in document 05. Never truncate to fit.

Use a typed geography/season registry. Initially support only reviewed pairs used in the dataset; unsupported pairs return a validation error rather than generic invented context. Country is not one climate: declare a local scene interpretation and its assumptions. Winter remains winter in the southern hemisphere; month metadata is auxiliary, not an instruction to swap the season name.

## 3. Stages

### A. Validate and prepare reference

Decode bytes rather than trust extension; reject unreadable, animated or oversized inputs. Proposed limits: 20 MB and 40 megapixels. Apply EXIF orientation, convert to sRGB with a declared profile assumption, keep source hash, and create a reference rendition with long edge ≤1024 without enlargement. Record alpha-compositing choice if needed.

For the small initial dataset, use reviewed product descriptions/reference boxes supplied in its manifest or one cached Gemini 3.8 Flash extraction per product. Record provenance. Do not require a new analysis call for every request. Unknown brand/label/material remains unknown. Original photo remains authoritative for product evaluation.

### B. Select textual content

Exact mode uses code; no selection model is necessary. Extract mode uses one schema-constrained call, proposed Gemini 3.8 Flash, to identify relevant source spans and optional role metadata. It cannot rewrite copy, invent claims or set scene/style instructions. Validate offsets, protected coverage, content groups and capacity; freeze TextPlan.

An invalid plan returns invalid_text_plan. A separately recorded human correction can unblock a run but is labelled human_supplied. Do not silently substitute a different extraction or repeatedly spend until validation passes.

The evaluator later checks semantic selection fidelity independently. Generation may proceed after structural validation with semantic status unscored; this is useful for capturing selector failures in the dataset. An optional preflight semantic check can stop a known bad plan, but logs must retain that request and failure in end-to-end denominators. A validated schema alone does not establish faithful content.

### C. Resolve scene and compile prompt

Resolve product/geography/season into a small compatible cue set and fixed product/text zones. Keep image look and feel independent of freeform input. The compiler receives selected text blocks, not the raw prose. Treat them as literal content even if they contain words such as “winter,” “bright red,” or “ignore previous instructions.”

Prompt sections:

1. One square display ad featuring one reference product; preserve silhouette, proportions, color and readable branding.
2. Local scene interpretation, geography/season cues and explicit contradictions to avoid.
3. Simple uncluttered composition and contact surface, coherent light/shadow, product zone and text zone.
4. Enumerated TextPlan blocks with roles/order and escaped exact render strings. Preserve each selected string; no paraphrase or extra offer/CTA.
5. Preserve the product's own visible label separately from selected ad text. No unplanned ad copy or duplicate product.
6. One final image with explicit square 1K output settings.

No model is needed to turn validated fields into the final prompt. An optional creative planner can later select layout choices without changing the frozen TextPlan or quality criteria. Defer it until evaluation evidence is complete.

### D. Generate once

Use official Google SDK behind an ImageGenerator adapter. Proposed model: gemini-3.1-flash-image. Its image input/output and editing capabilities are documented in [Google's image guide](https://ai.google.dev/gemini-api/docs/image-generation); installed SDK/account compatibility still needs a live probe.

Send explicit model, 1:1 ratio, 1K size and chosen thinking configuration. Start with documented minimal thinking as a pilot setting, not a claim of optimal quality. Keep requested/returned model IDs, SDK/API version, interaction/request ID and usage metadata.

Parse final image blocks explicitly. No image, refusal, corrupt data or unexpected multiple final images are classified errors; do not pick arbitrary binary output or provider intermediate images. Inspect actual pixels: strict baseline rejects long edge >1024 or nonsquare output. Store canonical final image bytes before evaluation; do not crop/enhance/redraw after a passing verdict.

### E. Evaluate independently

Pass original source, explicit policy, protected spans, frozen TextPlan, original reference, final image and resolved context into the standalone evaluator. Return dimension-level observations, verdicts and reliability. A generation-only run is generated_unscored and has no accepted/selected image. The evaluator remains usable on external fixtures without generation.

## 4. State and resource limits

Baseline flow:

validated → copy_prepared → prompt_compiled → dispatched → image_saved → evaluated.

Alternative states include invalid_input, invalid_text_plan, copy_capacity_exceeded, refused, provider_failed, invalid_image, unknown_remote_outcome and generated_unscored. Keep execution reliability distinct from quality verdicts as specified in document 05.

Proposed baseline limits:

- 1 image-provider dispatch per request; 0 automatic image retries or repairs.
- 1 Extract selection call per request; Exact uses 0.
- At most 1 cached reference-analysis call per unique product when not human supplied.
- Evaluator call plan: at most 1 semantic selection judgment and 1 combined structured visual evidence judgment per image; 1 optional blind transcription on ambiguous OCR. No hidden retries. Exact selection needs no semantic relevance call when coverage is mechanically established.
- Run-wide ledger covers all calls, failures and uncertain liabilities. Concrete dollar authorization is still required before live inference.
- Proposed provider timeout 120 s/image and 60 s/text call; measure and adjust explicitly. Run deadline and concurrency are recorded policy, not implicit SDK defaults.

An unavailable or incomplete evaluator returns unknown/unscored, not pass. Missing dependencies cannot be hidden by dropping checks. SDK retries must be disabled or explicitly counted within the configured cap.

## 5. Artifacts and resume

Use a local single-process runner and one writer, with a per-run lock. No database, queue service or multi-agent runtime required.

```text
runs/<run_id>/
  request.json
  reference-manifest.json
  source-contract.json
  text-plan.json
  context.json
  prompt.txt
  dispatch.json
  provider-receipt.json
  image.png
  evaluation.json
  events.jsonl
  result.json
```

Persist dispatch intent before network send; write image/receipt via temporary file and atomic rename before emitting completion. Flush events and reject middle-of-log corruption. A truncated last event is recoverable. A dispatched call without a receipt has unknown remote outcome; it is not safe to assume no charge or redispatch automatically.

Hash source/policy/protected spans, TextPlan, reference, context, prompt, model/config and preprocessing version. Include these in generation and evaluation identities. Human IDs/pathnames are not content hashes. Distinguish deliberate resampling from resume through a sampling-run ID. A model alias may change; record returned metadata and do not promise pixel-identical regeneration.

Evaluation cache additionally includes rubric, thresholds, component model/config, schema and prompt versions. Repeats use independent replicate IDs and actual calls, not cache hits. Replay mode cannot fall through to network. Credentials stay outside artifacts/logs.

Final result includes all artifacts, execution state, per-dimension verdicts, accepted_image nullable, errors, cost estimates/actual usage/unknowns, latency and human interventions. Only reliably passing evidence produces accepted_image. Failed previews are visibly unapproved.

## 6. Deferred optimization

Best-of-N, one targeted repair, text overlay, original-product compositing, larger model comparisons, aesthetic planning and UI are optional future tickets. If enabled, name the mode and budget explicitly; retain parents, fully reevaluate edited children and report first-attempt versus final outcomes separately. v0.1's three-call loop is not the current baseline.

A context-enrichment ablation is useful only after core evaluator evidence exists. Keep paired requests, TextPlans, models, layouts, budgets and rubric fixed; vary scene-enrichment clauses only. The effect of copy extraction is a separate experiment and must not be confounded with scene enrichment.
