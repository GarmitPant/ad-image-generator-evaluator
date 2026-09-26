# Handoff to the implementation agent

Status: generation-first design v0.1. The full evaluator design is a subsequent collaboration step. Do not treat provisional evaluator choices as calibrated facts.

## 1. Operating brief

Build a Python CLI/library for the pipeline in `01-generation-pipeline.md`. Use the model decisions in `02-model-decisions.md`. Garmit wants separate reference-analysis, ad-planning, and image-rendering tasks. Analysis and planning can share a model ID but must have distinct schemas and cached results. Preserve the required ad text exactly.

Implementation happens in a new repository. Copy the original seven context documents for provenance. Reconcile the old `AGENT_BRIEF.md` against the explicit decisions here before turning it into root `AGENTS.md`. In particular, remove contradictions around whitespace normalization, similarity-based text pass, retry caps, missing evidence, and score ranking. Record Garmit's accepted/rejected design decisions as they arrive.

The coding agent must not invent organizer answers, model-access results, successful live tests, calibrated thresholds, human labels or budget authorization. No UI work until pipeline and evaluator evidence are complete. Do not interpret a generated preview as a passing ad.

## 2. Minimal module boundaries

```text
src/adgen/
  contracts.py        # request, artifacts, profile, plan, evaluation, run result
  assets.py           # decode, orient, normalize, hash, immutable save
  registry.py         # reviewed market/season profiles and cue compatibility
  reference.py        # cached product extraction, human-reviewed overrides
  planner.py          # structured ad planning + labelled template fallback
  compiler.py         # pure prompt and quality-contract compilation
  providers/gemini.py # text/vision and image adapters, no domain policy
  pipeline.py         # finite state flow, candidate creation and repair policy
  selection.py        # hard gates and stable tie-breaking
  store.py            # manifests, atomic artifacts, events, resume lock
  budget.py           # reservations, usage, price versions, unknown liabilities
  cli.py              # validate, plan, generate, evaluate, run, resume
  eval/               # interface now; full implementations in next milestone
```

Keep this as a single-process program. No database, vector store, web server, message queue, multi-agent runtime, or orchestration framework is needed. Separate protocols/adapters only where they make offline testing or model replacement concrete.

## 3. Six-hour working allocation

This is an approximate remaining-time allocation, not a delivery promise. Update it against elapsed time and actual setup issues. Human billing/photos and implementation preparation can proceed concurrently; this does not require spawning additional agents.

| Elapsed allocation | Work | Exit condition |
|---|---|---|
| 0:00–0:25 | Repo/dependency setup; keys/billing; one approved compatibility probe | Allowed model returns one decoded square image with cost/latency receipt |
| 0:25–1:25 | Typed contracts, registry subset, product profile, planner, compiler, generation/store | One request reaches `generated_unscored`; dry-run/replay work offline |
| 1:25–1:50 | Four diverse pilot requests, inspect profiles/plans and outputs | Freeze obvious prompt fixes and declare calibration vs holdout samples |
| 1:50–3:20 | Evaluator implementation from next reviewed spec; integrate interfaces | Genuine positive and negative fixtures per dimension, reliability semantics work |
| 3:20–4:20 | Twenty-request dataset, human labels, recorded judge calls, offline regression tests | Counts/manifests complete including failures; thresholds frozen before held-out report |
| 4:20–5:00 | One repair path and paired context ablation if time permits | Bounded repairs with full reevaluation; equal-budget comparisons |
| 5:00–6:00 | Results/write-up/disclosure, clean-clone offline run, fix issues | Honest submission with limitations and reproducible evidence |

If behind, cut repair, ablations, nonessential color metrics and extra models first. Keep automated evaluator tests, human labels and write-up. Do not drop fidelity checks and still claim the original quality bar. Report any incomplete metric as unsupported/unknown.

PaddleOCR/Grounding DINO/DINOv2 installation and one local inference should be checked early. Do not wait until hour three to discover unavailable model weights or runtime incompatibility. Choose one OCR engine after the probe, not two redundant engines by default.

## 4. Build tickets for the generation slice

### T0 — Provider and asset probe

Deliver sanitized receipt, model/SDK manifest, image with measured dimensions, and a failed-call fixture. No bulk generation. Stop if billing/model access fails; continue offline schema work while Garmit resolves access.

### T1 — Immutable inputs and reviewed context

Deliver request validation, image normalization, reference/profile artifacts, small reviewed registry and deterministic hashes. CLI validation returns errors before any paid call. Preserve product source details and permit explicit human profile overrides.

### T2 — Structured ad planner and compiler

Deliver the exact AdPlan contract, semantic validator, template fallback with visible provenance, and two deterministic composition prompts. Compilation and schema validation are pure/offline. The planner cannot change headline or acceptance criteria.

### T3 — Candidate generation and records

Deliver two independent calls, concurrency cap, dispatch accounting, strict native resolution validation and crash-safe artifact save. Support generation-only output with no false pass. Do not add repair until T4/T5.

### T4 — Evaluator adapter and selection

Deliver evaluator protocol, fixture-backed offline implementation for control-flow tests, and explicit unknown results in unimplemented live dimensions. Only the actual later evaluator can certify outputs. Fixed index breaks ties among passing candidates.

### T5 — One repair and safe resume

Deliver eligible-failure routing, one linked edit, complete reevaluation, dispatch cap and ambiguous-timeout recovery. Parent artifacts remain untouched. A child can be worse than its parent; the system must record this rather than overwrite evidence.

## 5. Acceptance tests with behavioral value

| ID | Scenario | Expected behavior |
|---|---|---|
| A01 | Unsupported market/season or unimplemented profile pair | Explicit validation failure before providers |
| A02 | `Save 20% — Today!` input | Exact copy persists in request, plan and prompt; punctuation/case unchanged |
| A03 | Leading space, newline, control override, oversized text | Reject with reason; no automatic rewriting |
| A04 | Country Japan with English text | Scene resolves for Japan; copy remains English |
| A05 | Southern-market winter | Winter remains winter; correct reviewed locale profile chosen |
| A06 | EXIF-rotated JPEG and deceptive extension | Correct orientation/type detection by bytes; hash identifies actual normalized content |
| A07 | Animated/decompression-bomb/undecodable image | No paid call; explicit input error |
| A08 | Analyzer guesses unreadable label | Schema permits unknown; review required, guessed label not enforced as truth |
| A09 | Planner changes copy or chooses unlisted cue | Reject plan; declared template fallback or missing-inventory error |
| A10 | Planner returns duplicate A/B plans | Validation catches lack of composition diversity; bounded deterministic fallback |
| A11 | Same inputs/config, different local reference pathname | Same content/plan fingerprint |
| A12 | Different reference, cue version or headline | Different fingerprint; stale evaluation not reused |
| A13 | Text-only refusal or multiple final images | No accepted candidate; classify output and record usage |
| A14 | 1376×768 generated fixture | Strict output rejection, never publish as compliant |
| A15 | A fails, B reliably passes | Select B; no repair |
| A16 | A/B both reliably pass | Select A by stable index; completion order irrelevant |
| A17 | Text-only failure on A; B fails several metrics | One A edit if budget remains; recheck every dimension |
| A18 | Edited headline fixed but logo changed | Child fails; no selected image unless another candidate already passes |
| A19 | Degraded/unknown evidence on all viable images | `review_required`; not selected or automatically image-repaired |
| A20 | Three image dispatches consumed | Fourth impossible, including SDK resubmissions |
| A21 | Insufficient reserved dollars or expired deadline | Stop before next provider submission; preserve available evidence |
| A22 | Timeout after dispatch but before receipt | Unknown remote outcome and cost; no silent duplicate |
| A23 | Crash after image save, before evaluation event | Recover hash-verified image and evaluate it without regenerating |
| A24 | Two processes resume same run | One acquires run lock; no duplicate dispatch |
| A25 | Replay fixture missing | Hard cache error, zero network fallback |
| A26 | Same image, changed thresholds/rubric/reference | Reevaluate or require new matching fixture |
| A27 | Judge repeat experiment | Independent replicate IDs/calls; cache replay not counted as model stability |
| A28 | Generation-only mode | Preview plus `generated_unscored`; selected image is null |

Use synthetic provider fixtures for operational edge cases and actual, disclosed recorded responses for evaluator regression. Those are different kinds of evidence. Avoid asserting that an uncalibrated similarity value must pass a real image.

## 6. Pilot request coverage

Use four development cases, not the held-out twenty, to expose problems cheaply:

1. A distinctive labelled bottle, short headline, temperate northern winter.
2. The same bottle and headline, Australian winter in the explicitly chosen southeast coastal locale.
3. A differently shaped product with prominent color, Indian summer in a reviewed local setting; headline contains a number and `%`.
4. A mug or box with readable branding, Japanese autumn locale; English text with punctuation.

These are proposed coverage categories, not already supplied product facts. Garmit picks actual images. Review reference profiles before generating and human-label pilot images before inspecting automated scores.

## 7. Suggested opening instruction in the new repository

> Read AGENTS.md, docs/context/ and docs/design/. Implement only T0–T3 of the generation pipeline initially. Preserve exact ad copy; use separate structured reference analysis and ad planning; use allowed Gemini Flash Image for rendering. Build dry-run and offline fixtures first. Before any live inference, present the concrete call count and estimate against Garmit's approved budget. Return measured provider compatibility, test results, unresolved assumptions and generated previews clearly labelled unscored. Log collaboration and architectural deviations. Do not implement UI or claim evaluator accuracy yet.

## 8. Artifacts needed before submission

Persist all requests and attempts, frozen input/plan/rubric versions, generated images, human labels, recorded evaluations, constructed-negative manifests, failure counts, costs/latencies and the agent-collaboration log. Link the design requirements and actual human revisions in the coding-agent disclosure. Pin dependency/model-weight revisions and document offline fixture setup so a clean clone does not require hidden caches.
