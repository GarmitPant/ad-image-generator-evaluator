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


## 2026-09-26 — Candidates, selection and simplified guardrails, v0.4 (Garmit, via Claude Code session)

| Decision | Status and reason | Supersedes / alternative considered |
|---|---|---|
| Guardrails are simple, functional, predefined: one static policy file (global rules + optional per-country notes), no web lookup | Confirmed; evals matter more | v0.3 per-rule evidence-verified review; web-searched regional rules (rejected) |
| Generate 3 candidates per request, one creative plan per candidate | Confirmed | Alternative: one shared plan, N samples (cheaper, less diverse; rejected) |
| Evaluate every candidate, present highest-ranked, save all images | Confirmed flow; ranking rule (verdict tier gates, then score) proposed | Single image, no ranking |
| 1–3 reference images per product | Confirmed | Single reference |
| Evaluator vision models local only (PaddleOCR, Grounding DINO tiny, DINOv2 small); hosted later if needed | Confirmed after reviewing the M1/8 GB machine | Modal / HF Endpoints / Replicate / API-only judge (deferred) |
| Batched evaluation after single-request flow | Confirmed | — |
| Credit estimate revised: 3 candidates make $10 Gemini tight (~$15 comfortable) | Recommendation | — |

## 2026-09-26 — Generation implementation v0.1 (Codex session)

| Decision | Status and rationale |
|---|---|
| Implement generation end to end, without UI/evaluation | Explicitly requested by Garmit; supersedes any requirement to implement evaluator tables during G1 |
| Offline implementation only | Explicit response to the paid-test question; no inference calls or live compatibility claims |
| Generation-only success is `generated_unscored`, all candidates saved, winner null | Implementation of the requested staged delivery; eventual scoring/ranking design unchanged |
| Shared-stage candidate index 0; UUID4 run IDs | Fix SQLite nullable UNIQUE weakness; standard-library IDs sufficient for local pilot |
| OS lock + database owner, local POSIX only | Avoid unsafe timeout-based stealing of a lock; process death releases the OS lock |
| Immutable resume and conservative unknown-call handling | Never automatically resend a call whose dispatch may have reached a provider; failures require a new run |
| Canonical analysis order, declared generation order | Ensure order-independent cache reflects the actual analysis invocation; preserve reference presentation order for rendering |
| Copy validation before paid product analysis | Reject invalid input/selection early; freeze shared copy before candidate work |
| Scan visible plan fields, excluding avoid/rationale | Avoid rejecting a plan for naming a prohibited object only in its exclusions |
| Pinned pip environment instead of uv | Use the available Python environment; direct and transitive pins recorded, no unverified lockfile claim |
| Replay identity includes system instruction and candidate/attempt | Keep distinct stochastic candidate responses even with identical prompts; avoid stale or ambiguous fixture reuse |
| Separate raw provider bytes and published PNGs | Preserve original evidence/provenance while enforcing decoded square <=1024 outputs |
| Static prices/reservations are provisional estimates | No provider-enforced cap or free-token assumption; usage and uncertainty remain explicit |

Detailed differences and operational limits: [generation runbook](generation-runbook.md).


## 2026-09-26 — Local budget cap removed (Garmit, via Claude Code session)

| Decision | Status and reason | Supersedes / alternative considered |
|---|---|---|
| Remove the local per-run budget cap (`--budget-usd`, pre-dispatch reservations, `budget_cap_usd`/`reservation_usd` columns) | Confirmed by Garmit: users set usage limits on the provider API accounts; the local cap was an estimate, not an enforceable limit | Keep local cap (rejected) |
| Keep `--allow-paid`, dispatch-recorded-before-send, never resending unknown-outcome calls, and per-call usage with report-only cost estimates | Agent recommendation accepted; prevents accidental live runs and duplicate charges, and supplies cost-per-ad for the report | Remove all cost recording (not chosen) |
| Implement as additive migration 002 (drop columns) rather than editing migration 001 | Implementation choice; existing local databases upgrade in place | Rewrite 001 (would break existing DBs) |


## 2026-09-26 — Product fidelity scope (Garmit, via Claude Code session)

| Decision | Status and reason | Supersedes / alternative considered |
|---|---|---|
| Product fidelity checks only whether the ad shows the *same object*: presence/count, type, shape, colours/materials, distinctive components, legible branding | Confirmed by Garmit: generated products already follow reference pose; position/orientation checks are redundant | Attribute rubric that included main-subject visibility/placement |
| Keep Grounding DINO only to crop and count (no scoring of box position/orientation/scale) | Agent decision under that direction: a crop makes DINOv2 and label OCR compare the product, not the scene background; count supports the missing/duplicate check | Drop detector and embed whole images (rejected: background dominates similarity) |
| DINOv2 similarity is a diagnostic until dev calibration shows it separates same vs wrong objects | Proposed; no threshold assumed | Fixed similarity threshold |
| Pinned weights: grounding-dino-tiny `a2bb814d`, dinov2-small `ed25f3a3` (Apache-2.0) | Proposed pins from Hugging Face on 2026-09-26 | — |


## 2026-09-26 — Evaluator implementation decisions (Claude Code; for Garmit's review)

| Decision | Status and reason |
|---|---|
| Evaluator runs inside the pipeline after each output gate; `generate` evaluates by default, `--skip-evaluation` opts out | Implements the confirmed generate → evaluate → present-best flow |
| One visual judge call per candidate (product P2–P6, context, image guardrails); judge never sees expected copy or passing answers | Cost/latency bound; blindness tested |
| P1 (exactly one product) requires detector and judge agreement, else unknown | Detector alone gave a 0.70 "sunglasses" box on a beer bottle |
| Image rule GR-TEXT not asked of the judge; unplanned text is judged by OCR rendering checks | Avoids the judge flagging the intended ad copy |
| Proposed success criteria written into the report before results: no human-labelled failure accepted; false rejects ≤20% of labelled passes; abstentions reported | Proposed targets; not yet measured |
| Known score weakness: text-rendering score is CER-based, so duplicated copy lowers the verdict but not the score | Ranking still correct because verdicts gate; stated in limitations |


## 2026-09-26 — Regional style guardrails v2 and batch v1 (Garmit, via Claude Code session)

| Decision | Status and reason | Supersedes |
|---|---|---|
| Separate stereotyping people and beliefs (banned) from regional style (encouraged). Landmarks and skylines allowed in the background; native wildlife and plants allowed; the planner must make the country recognisable through ≥2 regional cues and may pick a specific city or region | Confirmed by Garmit: countries were hard to tell apart | guardrails/1 bans on landmarks and wildlife; "understated contemporary" country notes |
| Flags, national emblems and religious sites stay banned, even in the background | Agent recommendation, not overridden by Garmit | — |
| C-REGION ("recognisable as {country}?") is a diagnostic, not required | Agent recommendation, not overridden; subjective and uncalibrated; human `region` labels can calibrate it | — |
| Versions bumped (generation/2, guardrails/2, evaluator/2); only new runs count | Confirmed by Garmit | Earlier runs, which remain as history |
| Batch v1: 20 requests × 3 candidates covering all countries, seasons, products and text modes plus deliberate hard cases; pilot 2, then freeze, then run all as held-out with provisional thresholds | Agent plan per Garmit's request | — |
| Blind labelling: sheet without verdicts; labels template for every candidate × 6 dimensions (overall, 4 dimensions, region) | Implemented for the credibility check | — |


## 2026-09-26 — Jeep product, no human labels, readable report (Garmit, via Claude Code session)

| Decision | Status and reason | Supersedes |
|---|---|---|
| Add Jeep references; replace requests 07, 09, 13 and 18 with Jeep requests (same countries and seasons). Never combine 2-door jeep-2 with 4-door jeep-1/jeep-3; jeep-2 (snowy) is used in a summer request as a season-leakage probe | Confirmed by Garmit (new images); variant handling is an agent decision | Heineken GB, sunglasses AE, Modelo AU, bottle US requests |
| Drop human labelling and the label-agreement report | Confirmed by Garmit: short on time. The report states that evaluator accuracy is not measured against humans | Batch v1 steps 6–7 (blind labels, credibility check) |
| Report output rewritten for people: plain-language check names, per-request ranking with reasons, per-candidate evidence cards (`evidence/*.md`), readable CSV | Confirmed by Garmit | Machine-oriented CSV/JSON only |


## 2026-09-26 — Evaluator/3 after pilot (Claude Code; for Garmit's review)

| Decision | Reason |
|---|---|
| Fix line merging, block wrap, label exclusion, detector prompt and count threshold (0.4 plus IoU de-duplication) | Three genuine false rejects in the pilot |
| Version the evaluation stages and re-score existing runs with `adgen evaluate`, instead of regenerating | Generation was correct; only scoring changed. Saves image cost |
| Treat pilot requests 01 and 02 as evaluator development data | The evaluator was changed after seeing their results |
| Ranking/2: after verdict, failed checks and score, break ties by country recognisable (C-REGION), then DINOv2 product similarity, then guardrail status, then index | Confirmed by Garmit. Pilot showed all candidates tying at PASS/1.0, so winners were decided by index. Diagnostics only break ties. The ranking version is part of the export stage name, so re-ranking reuses stored evaluations (verified: 0 model calls) |
| Batch reduced to 9 requests × 3 candidates = 27 images (pilot 01–02 + 03, 04, 06, 07, 12, 18, 20); 11 requests parked, not deleted | Confirmed by Garmit: about 25–30 images, time-limited. Subset keeps all countries, seasons and products plus the negation, qualifier, alcohol-in-UAE, snowy-reference and offer cases |
