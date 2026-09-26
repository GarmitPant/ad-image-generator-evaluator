# Image generation pipeline specification

Version 0.1 · Proposed · 2026-09-26

## 1. Objective and scope

Given one reference product image, a supported country code, a season, and exact ad copy, produce a contextual display ad and evidence explaining whether it satisfies the request. Keep generation and evaluation connected through immutable typed contracts. Return an honest non-passing outcome when evidence or quality is insufficient.

This iteration specifies generation in implementation-level detail. Evaluator internals and calibrated thresholds will be designed next. The public evaluator contract below is required now so the generation agent cannot invent scores or conflate missing evaluation with success.

### Requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| G01 | Generation uses an organizer-allowed Gemini image model | Recorded requested and returned model identifiers |
| G02 | Country and season are typed; unsupported values rejected | Offline schema tests |
| G03 | Exact user text retained, never rewritten or translated | Input/prompt round-trip tests; later OCR and human labels |
| G04 | Published generated artifacts have long edge ≤1024 px | Decode actual bytes, assert dimensions |
| G05 | Reference identity survives; only scene/composition may change | Separate product evaluation against original reference |
| G06 | Context additions are traceable to a reviewed profile | Cue IDs, profile version, resolved assumptions |
| G07 | Generation has bounded cost and termination | State-machine tests and dispatch ledger |
| G08 | No selected output without complete passing evidence | Selection truth-table tests |
| G09 | Every mutation creates a new artifact and evaluation | Parent hashes and evaluation/image hash equality |
| G10 | Offline execution never silently contacts providers | Network-denied tests and replay cache misses fail |

Non-goals now: UI, hosting, distributed workers, online search during generation, model training, brand policy systems, CTR optimization, additional ad sizes, automatic translation.

## 2. Boundary types

Use Pydantic v2, frozen models where practical, forbidden extra fields, finite numeric values, explicit schema versions. The shapes below are normative field contracts, not tested Python code.

### AdRequest

| Field | Type/default | Contract |
|---|---|---|
| schema_version | literal `ad-request/1` | Version validation semantics |
| request_id | bounded safe string | Human tracking ID; never used as content identity |
| product_image | local path | Resolve to immutable image artifact before downstream stages |
| geography | enum `US,GB,DE,JP,IN,AU,BR,AE` | Require registry entry for selected season; incomplete entries fail explicitly |
| season | enum `spring,summer,autumn,winter` | Season experienced in the chosen market, not current local date |
| ad_text | string | 1–60 Unicode code points; ≤8 whitespace-delimited tokens; preserve exact code points |
| aspect_ratio | literal `1:1` in v1 | No silent acceptance of unsupported ratios |

Input text validation must **reject**, never silently strip/collapse/translate/rewrite. Reject leading/trailing whitespace, repeated spaces, newlines, tabs, control characters, and bidirectional override controls in this initial single-line contract; return a specific correction message. Interior ordinary spaces are retained. Unicode punctuation and non-Latin letters are preserved. Validation supports Unicode, but evaluation requires a declared OCR-language profile; unsupported scripts return `unsupported_text_evaluation` before spending. Initial validated coverage is English/Latin text, digits, and common currency/percent symbols. Emoji/grapheme rendering is an extension.

Store the original string separately from any diagnostic comparison normalization. Allowed rendering reflow may wrap at an existing space; it cannot insert hyphens, change token order, omit punctuation, or alter case. Structural escaping in JSON/XML is allowed only if decoding reconstructs the identical text. Ad copy is data, not instructions to the model.

Do not infer a text language from country. An English headline in Japan remains English. If language extension is implemented later, add an explicit typed `text_language`, not an undocumented heuristic.

### RunPolicy

Separate system policy from user creative input:

- `candidate_count=2`; `max_repairs=1`; `max_image_dispatches=3`.
- `generator_model=gemini-3.1-flash-image`; `image_size=1K`; `thinking_level=minimal` as the initial pilot baseline, not a validated optimum.
- `max_image_inflight=2`; reference analysis is cached per product.
- `resolution_policy=strict_native`; `text_mode=model`; `overlay_enabled=false`.
- `reference_analysis_max_dispatches=1` per unique product; `ad_planner_max_dispatches=1` per request; `judge_max_dispatches=3` for the intended one-call-per-candidate judge adapter, no hidden retries.
- Proposed operational timeouts: 120 s/image call; 60 s/analysis or judge; 420 s/request including local evaluation. Treat these as initial settings, measure actual latency, and record any change.
- Require explicit `run_budget_usd` and dated price configuration before live mode. No implicit dollar allowance. User authorizes a concrete live batch estimate separately; this design is not spend authorization.
- `mode=dry_run|live|replay`; `sampling_run_id` distinguishes intentional new samples from resume.

A later model comparison must not silently change models within a run. The only exception is an explicitly named experimental arm with its own manifest.

### ImageArtifact and ReferenceAsset

`artifact_id`, relative file path, encoded-byte SHA-256, optional decoded-pixel SHA-256, MIME type, width, height, color space, source kind (`reference|generated|edited`), parent artifact ID, preprocessing version.

Reference processing:

1. Decode PNG/JPEG/WebP by bytes, not extension. Reject animated/multiframe images, truncated files, decompression bombs, and inputs over proposed 20 MB / 40 megapixels limits.
2. Apply EXIF orientation once. Convert through the available ICC profile to sRGB; if absent, document sRGB assumption. Preserve the source artifact and its hash.
3. Produce a model input with long edge ≤1024, preserving aspect ratio and without enlargement. For transparency, composite onto a declared neutral background for v1 and record it; do not mutate the original.
4. Flag a minimum side below 512 as a low-detail warning, not proof of invalidity. Abort before spending if a human-required brand detail cannot be seen or if multiple products make the intended subject ambiguous. For the golden set, resolve such cases once during preparation.
5. OCR and reference analysis use this normalized orientation. Crops use normalized coordinates and explicitly identify the artifact to which they apply.

The original reference—not the analyzer's description—is authoritative for product evaluation. Store normalized references separately from generated-output resolution checks.

### ProductProfile

Fields: `profile_version`, `reference_sha256`, `analyzer_model`, `analysis_prompt_hash`, `analysis_schema_hash`, `category`, `subject_bbox?`, `shape_features[]`, `colors[]`, `materials[]`, `distinctive_features[]`, `visible_text[]`, `uncertainties[]`, `review_status`, and `profile_hash`.

Every descriptive assertion carries `evidence_source=vision|ocr|human`, optional region, and `observability=clear|uncertain|unreadable`. Unknown fields are null/empty; never guess brand, exact color code, material, or unreadable label text. Optional bounding boxes are proposals until reviewed or detected. OCR confidence is an engine score, not a calibrated probability of correctness.

One Gemini 3.8 Flash structured extraction per unique normalized reference is the proposed default. Validate its schema and field bounds. On invalid output, stop with `reference_analysis_failed`; allow a separately supplied, explicitly human-authored profile to resume. No invisible “JSON repair” model that changes facts.

For 4–5 products, one human review of each cached profile is cheap and prevents a hallucinated profile contaminating all twenty ads. Record that intervention. Once frozen, generation must not alter the profile in response to its own output.

### ResolvedContext

Fields: `registry_version`, `profile_id`, `geography`, `season`, `locale_scope`, `season_interpretation`, `assumptions[]`, `required_cues[]`, `optional_cues[]`, `forbidden_cues[]`, `source_notes[]`, `context_hash`.

Country codes do not uniquely specify climate, culture, city, or season appearance. Each registry entry chooses and names a plausible **scene locale** and a narrow set of visible cues. Example: `AU / winter / temperate southeast coastal café`, with cool daylight and subdued winter foliage. This is a creative assumption, not a claim that all Australia looks that way.

Rules:

- A southern-hemisphere winter stays winter; do not flip the requested season name to summer. Month metadata, if included, resolves with locale, never by country-wide hemisphere alone.
- Do not assign Brazil one uniform climate or make Indian winter universally snowy. Equatorial and multi-climate countries need explicit local interpretation.
- Select 1–2 compatible geography cues and 1–2 season cues, with observable evidence; avoid a crowded checklist of props. Prefer architecture, vegetation, and light over flags, costumes, or landmarks used as shortcuts.
- `required` means testable campaign requirement; `optional` is never a pass condition. Forbidden cues express this scene policy, not universal impossibility.
- Validate cue dependencies/conflicts by stable IDs. IDs can be checked deterministically; natural-language plausibility still needs human review.
- No holidays unless explicitly requested in a future schema. No translation, unrelated claims, or invented discounts beyond user copy.
- Freeze the context before rendering any candidate. All candidates and repairs retain this context hash.

The eight-market enum preserves the source intent. Review only the market/season pairs used in the pilot first; do not fabricate the remaining registry combinations merely to fill an enum.

### CreativeBrief and QualityContract

Create two artifacts from shared versioned inputs after validating the planner output:

**CreativeBrief**: product preservation constraints; resolved context; chosen cues; composition plan; exact text plan; allowed transformations; prompt template version. It controls generation.

**QualityContract**: original text; reference hash; required/forbidden context IDs; measurable technical requirements; rubric version. It controls evaluation. The evaluator receives required scene evidence but not generator explanations, prior scores, repair instructions, or ablation labels.

Keeping a shared contract prevents drift. It does **not** prove that the contract itself is culturally correct or useful. Human review validates the registry; human-labelled images validate the evaluator. Neither output generation nor a judge may revise acceptance requirements to rescue a candidate.

### AdPlan: the creative planning model

Following Garmit's proposal, use an explicit second model task between context resolution and prompt compilation. The reference analyst and planner may use the **same model ID** with separate prompts, schemas, caches and responsibilities; there is no inherent gain from a different vendor for each task.

Inputs: reviewed ProductProfile, normalized reference image, typed country/season, exact headline, reviewed allowed cue inventory, required/forbidden cues, available layout IDs, and output dimensions. Reference analysis is reused across requests; planning runs once per distinct request and returns both candidate variants.

Recommended model: `gemini-3.8-flash`. The image generator remains `gemini-3.1-flash-image`; the text/vision model is not being asked to generate pixels. Its structured-output capability is documented in the [model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).

Proposed planner response contract:

```text
AdPlan:
  schema_version: ad-plan/1
  product_profile_hash: string
  resolved_context_hash: string
  variants: exactly 2 PlanVariant objects

PlanVariant:
  variant_id: A | B
  layout_id: top_headline | side_headline
  selected_optional_cue_ids: list drawn from input inventory
  background_arrangement: approved arrangement ID
  contact_surface: approved material/surface ID
  lighting: approved lighting ID
  background_palette: approved palette ID
  headline:
    exact_text: string identical to AdRequest.ad_text
    zone_id: determined by layout_id
    typography: sans_bold | sans_medium | serif_bold
    alignment: left | center
    line_break_after_token_indices: ordered unique integer list
    contrast_strategy: dark_on_light | light_on_dark
  rationale: <=200 characters, audit-only, not sent to evaluator
```

Use IDs for factual/semantic choices and short finite style choices for aesthetics. The planner must not create new weather, regional facts, product features, claims, brand copy, or mandatory evaluation criteria. Exact required cues are immutable and automatically included by the compiler, not chosen by the planner. Initial approved inventories can be small; sophistication comes from compatible choices, not a giant ontology.

Validate in code before generating:

1. Hashes match inputs; exactly A and B; no unknown keys or cue/style IDs.
2. Headline equality holds character-for-character; line breaks occur only at existing token boundaries, preserve order, and reconstruct the same single-space headline.
3. Chosen cues fit the frozen context and do not conflict; required cues cannot be omitted.
4. Layout regions do not overlap by template construction; typography and palette choices apply only to headline/background.
5. Both variants differ in at least one permitted composition choice. If constraints leave only one feasible layout, require a different approved arrangement, not invented scene details.

On invalid schema/semantics, use a deterministic planner fallback from the same inventories, **labelled** `planner_source=template_fallback` with validation errors retained. This is an explicit design choice, not silent model-output repair. Stop if the inventory itself is incomplete or contradictory. No second planner call in v1. Track fallback counts in results. A future planner retry has a separately configured call budget.

Cache planning by reference/profile/context hashes, exact text, allowed inventories, planner model/prompt/schema/settings, and template version. Store validated plan and raw structured response. A user revision creates a new plan; candidate outcomes cannot retroactively modify the cached plan.

### What the proposed text-generation stage does

The supplied freeform field is the **literal text to display**, not a loose campaign brief. Therefore a copywriter must not paraphrase it or invent a CTA. Text preparation consists of the planner's type treatment, permitted line wrapping, placement and contrast decisions; final generation instructions are then compiled in code.

If Garmit meant “generate the detailed image prompt,” the compiler already performs that role from AdPlan. Another unconstrained prose model can change obligations and is unnecessary for the six-hour build. If future requirements add separate campaign-intent input and editable copy, a copywriter may propose text **before** a user-approved headline is frozen; that is outside this schema.

## 3. Layout and prompt compilation

Let the planner select from deterministic layout templates initially. Example normalized zones:

- Variant A: product zone `[0.18,0.32,0.82,0.92]`; headline zone `[0.08,0.06,0.92,0.26]`.
- Variant B: product zone `[0.08,0.18,0.58,0.88]`; headline zone `[0.62,0.18,0.92,0.78]`.
- Margins ≥0.06. Region rectangles are guidance to the generator, not guaranteed pixel masks. Their later measured adherence is diagnostic until a layout evaluator is validated.
- If estimated text fit rejects B, use A with a second allowed background arrangement. A simple font-size estimate is only a preflight heuristic and must not rewrite copy.
- Palette applies to background/accent colors only. Never recolor the reference product to match the season.
- Default front/three-quarter view close to the reference; preserve readable label orientation. Avoid requesting unseen surfaces that cannot be verified from one photo.

Prompt template sections, in order:

1. Task: one square display ad, one instance of the attached reference product.
2. Reference role and preservation: silhouette, relative proportions, color, visible branding; original photo authoritative; discard reference background as scene guidance.
3. Approved scene: locale, season interpretation, chosen visible cues, exclusions.
4. Composition: chosen product/headline zones, contact surface, coherent light/shadow, uncluttered scene.
5. Exact headline as an escaped data field. Render precisely; no translation, paraphrase, added punctuation, or invented CTA.
6. Preserve visible existing product label text. No **additional scene/headline text** beyond supplied copy; this distinction avoids telling the model to erase branding.
7. Output constraints: one complete image; no collage, border, legend, or extra product copy.

Do not ask for removal of provider provenance watermarks. Do not put secrets, local file paths, or irrelevant personal context into prompts. Reference text or user headline content must not be treated as instructions to change the task.

The source bank's “text-first” strategy becomes a frozen exact text plan before generation; another LLM call to invent text would add risk because the user already supplied it. No claim is made that this planning step guarantees spelling.

Canonical JSON is UTF-8 with stable keys and separators, preserving string code points. Compute `prompt_hash` from compiled prompt bytes; compute `invocation_fingerprint` from ordered image hashes, prompt hash, model ID, complete effective configuration, variant ID, and API adapter version. Store exact compiled prompts for inspection.

## 4. Provider boundary

Use the official Google Python SDK behind `ImageGenerator.generate(GenerationInput) -> GenerationResult`. Prefer the documented Interactions path for this initial adapter. The documented API supports image input, image response format, and linked edits; exact installed SDK behavior must pass a live compatibility probe. [Google image guide](https://ai.google.dev/gemini-api/docs/image-generation)

The domain layer must not depend on SDK objects. An input contains compiled prompt, ordered reference assets, generation configuration, and an optional edit parent. A result contains final image blocks, provider/model IDs, interaction ID, finish/status metadata, usage, elapsed time, and sanitized error details.

Adapter requirements:

- Send explicit model, square aspect, 1K size, and chosen thinking setting on every generation and edit. Do not inherit unspecified defaults during repair.
- Request one final image per call. Parse final image output blocks explicitly; do not select the first arbitrary binary/inline part or thought/intermediate image.
- If no final image: classify refusal, truncation, provider error, or `no_image_output`. A textual apology is not an image and is not a successful candidate.
- If multiple final images unexpectedly arrive: record a contract violation and usage; do not cherry-pick one for headline results. Decode only within safety limits; no candidate is accepted from that dispatch.
- Check actual file type, dimensions, and square aspect ratio. v1 strict mode rejects an oversized result instead of relying on resizing to reinterpret the organizer's cap. Log actual dimensions and failure; do not publish it as a valid artifact.
- A smaller square result can satisfy ≤1024 but records `requested_size_mismatch`; the live compatibility gate expects 1024×1024. Do not upsample to pretend compliance with the requested size.
- Store a lossless final PNG in sRGB and evaluate those exact bytes. Any permitted representation conversion is versioned. No crop, enhancement, background removal, or text overlay after a passing evaluation.

Capabilities confirmed by documentation are not evidence that this account/key can access the model. Missing model access or an unsupported SDK parameter blocks live execution; never silently switch to a non-allowed generator.

## 5. Candidate flow and total attempt budget

Create independent candidates A and B from the same frozen brief. They differ only in allowed composition choices. Separate calls avoid shared edit history between candidates. Concurrency two is permitted only after reserving both costs.

Each candidate transitions:

`planned → reserved → dispatched → generated → validated → evaluated`.

Alternative terminal attempt states: `provider_failed`, `refused`, `invalid_output`, `unknown_remote_outcome`, `cancelled_before_dispatch`. Each attempt has a unique ID and timestamps. A local timeout does not prove that the provider did not generate or bill an image.

After A and B:

1. Select from fully passing candidates if any exist; stop image generation.
2. Otherwise consider a repair only when an evaluation is reliable (`ok`), technical gates pass, and **exactly one** quality dimension fails with a supported narrow repair.
3. Select repair parent by fewest failed required checks, then variant index. Do not use an uncalibrated weighted average of unrelated scores.
4. Repair at most once; its result is C with parent A or B. Evaluate all dimensions again. Keep parents immutable.
5. If C passes, select C. Otherwise emit a truthful terminal result. Never return the “least bad” candidate as selected/pass.

The **three-dispatch cap includes every image-provider submission**, including retries, uncertain timeouts, and edits. A transport resubmission consumes remaining budget and can eliminate the repair slot. SDK automatic retries must be disabled or counted by a tested transport wrapper. `max_repairs=1` alone is not a cost bound.

Pilot v1 permits no automatic image transport retries. Preserve the receipt and allow an explicit resume that consumes a remaining dispatch. A completed one-candidate run after another dispatch fails can still select that candidate if it passes; report the actual candidate count. Insufficient evidence never triggers “retry until pass.”

### Repair policy

| Failure | Eligible action | Required preservation | Otherwise |
|---|---|---|---|
| Headline typo/missing character; product and context pass | One headline-only edit | Original reference, product details, scene, copy string, output config | No further edit |
| One localized context mismatch; text/product pass | One background cue edit | Copy and product; replace identified cue only | Reject repair if it implies global scene rebuild |
| Product identity/branding failure | No targeted repair in v1 | Identity cannot be rescued by accepting similar category | Return no passing output; examine reference/prompt in next design experiment |
| Multiple dimensions fail | No repair in v1 | — | Record failure; address root cause offline |
| Evaluation uncertain/degraded | No image repair | Missing evidence is not image defect | Return review required unless another candidate passes |

Edits use the selected parent's interaction ID when valid, reattach the original reference with its role explicitly identified, and reassert frozen constraints. An edit may change unrelated pixels despite narrow wording; full reevaluation detects regressions. If the interaction is unavailable, v1 returns `edit_context_unavailable`; a future stateless edit adapter must be tested and separately identified, not silently substituted.

## 6. Evaluator interface — reserve now, implement next

`evaluate(final_image, original_reference, quality_contract, evaluator_config) -> EvalRecord`.

Required fields:

- Image/reference/contract hashes, evaluator version, all component model and preprocessing versions.
- `execution_status=ok|degraded|failed` describing evidence reliability, not visual quality.
- Technical gates, then each dimension with `verdict=pass|fail|unknown`, typed observations, failed check IDs, optional diagnostic scores, thresholds and calibration-manifest ID.
- `overall_verdict` composed only in code. A trusted required failure establishes `fail`; otherwise any unknown establishes `unknown`; all required checks passing establishes `pass`. Missing/skipped dimensions are unknown, never pass.
- `eligible_for_selection = execution_status == ok AND overall_verdict == pass`.

Key distinctions:

- A confidently detected typo is `ok + fail`, not a runtime failure.
- A detector finding no product is uncertain until calibrated/cross-checked. It is not mathematical proof of absence.
- OCR, detection, embeddings and VLMs are learned measurements; only arithmetic and policy composition are deterministic. Report their failure modes.
- Case and punctuation matter. A high normalized edit similarity is diagnostic, not enough to certify verbatim text. Define rendering-only line-break equivalence explicitly; do not casefold a pass decision.
- Judge evidence descriptions are not mechanically verified merely because a box or text span is supplied. Independent checks establish only what those checks actually measure.
- DINO similarity cannot prove correct brand/logo. A similar-looking different product is a mandatory negative case for later calibration.
- Legibility and extra invented text require spatial checks; do not concatenate all OCR tokens globally and accept an accidental match on the product label.

Before evaluator completion, generation returns `generated_unscored`; it may expose preview paths but never `selected_image` or pass. A fake evaluator is allowed in offline control-flow tests only and is visibly marked synthetic.

### Selection and RunResult

For v1, choose the lowest candidate index among fully passing candidates. This is intentionally a deterministic quality-gated choice, not an unsupported aesthetic ranking. A later ranking model requires separate validation and cannot override hard failures.

Run outcome enum:

- `selected`: at least one fully passing candidate; selection reason and EvalRecord ID required.
- `no_passing_candidate`: complete reliable evidence rejects available candidates.
- `review_required`: no pass and at least one viable candidate lacks decisive evidence.
- `generated_unscored`: explicit generation-only mode before evaluator integration.
- `failed`: validation/provider/system failure prevents usable evaluated output.

Include `termination_reason` separately: completed, input_invalid, budget_exhausted, deadline_exceeded, refused, provider_error, unknown_remote_outcome, etc. Every result includes attempts, incurred/estimated/unknown cost, artifacts, selection (nullable), and unresolved issues. Failure previews are separately named and visibly unapproved.

## 7. Persistence, resume, and cost

One local process and one writer; no queue service or orchestration framework. Suggested records:

```text
runs/<run_id>/
  request.json  policy.json  product-profile.json
  context.json  brief.json  quality-contract.json
  attempts/<attempt_id>/prompt.txt
  attempts/<attempt_id>/dispatch.json
  attempts/<attempt_id>/receipt.json
  attempts/<attempt_id>/image.png
  attempts/<attempt_id>/evaluation.json
  events.jsonl  result.json
```

Write artifacts to a temporary sibling and atomically rename before emitting their completed event. Flush dispatch intent before network send. Flush provider receipt and image artifacts before evaluation. Ignore a truncated final JSONL event on recovery; do not ignore corruption in the middle. Use one process lock per run, so two resumes cannot both dispatch the same plan.

Content identities:

- Reference analysis cache: normalized image hash + analyzer model + exact prompt/schema/config hashes + preprocessing version. Add human override hash when reviewed facts change.
- Request content hash: normalized reference hash + exact text + geography + season + output contract; human request ID and file pathname are excluded.
- Plan fingerprint: request hash + frozen brief/registry/profile + generation policy/template/adapter versions.
- Attempt identity: plan fingerprint + sampling run ID + candidate index + operation kind + parent artifact hash (when editing).
- Evaluation cache: final image hash + reference hash + quality-contract hash + complete evaluator/model/threshold/schema/preprocess configuration. Repeated-judge measurements add `replicate_id` and must make independent calls; cache hits are not stability samples.

Resume verifies manifest/artifact hashes. A previously completed matching attempt is reused. A dispatched attempt without a terminal receipt is `unknown_remote_outcome`; retrieve existing provider interaction if its ID is available, otherwise do not silently redispatch. An explicitly authorized new attempt receives a new ID and retains the uncertain cost liability. Exactly-once remote inference cannot be guaranteed by local files.

Record per call: timestamps, wall latency, requested/returned model, SDK version, provider request/interaction ID, input/output usage broken down where available, pricing version, estimated vs reported cost, and error type. Never log credentials or authorization headers. Store image bytes as artifacts rather than giant base64 log fields.

Use immutable model/weight revisions when the provider exposes them. If only a mutable model name is available, record that limitation, the returned model metadata and timestamp; a name plus hash cannot guarantee identical future inference. Reproducibility here means replay of recorded artifacts and decisions, not guaranteed pixel-identical regeneration.

Before dispatch reserve estimated worst-case cost using bounded inputs/outputs and the model pricing configuration. For output-size controls unsupported by the endpoint, use a conservative documented model-limit reservation and block bulk execution until accounting is understood. Unknown usage stays unknown; do not label it zero. An app ledger is a spend control, not a provider billing guarantee. One run total includes analysis, planning, images, judge calls, retries and unsuccessful requests.

## 8. Experiment integrity

The context-enrichment experiment compares the same requests, references, model settings, image-call budget, and evaluator. Only the addition of enriched scene instructions changes. The raw arm includes the country, season and exact copy, while retaining common product/text/format constraints. Hold the selected layout/typography constant across the pair, remove enriched scene clauses in the raw prompt, and do not run a separate unconstrained planner for that arm. This estimates the effect of scene enrichment, not the entire planner. Both are evaluated against the same predeclared semantic contract, not different arm-specific rubrics. Blind arm labels from judges and human annotators.

Freeze one or two acceptable context cue sets per request before running either arm. Include a human check that the raw input could reasonably elicit those cues; report the bias created by more prescriptive enrichment. Keep “matches chosen brief” separate from broader “plausible geography/season.” Otherwise enrichment trivially wins by teaching to an idiosyncratic checklist.

For the pilot, report first-candidate outcomes separately from selected-after-repair outcomes. Never compare enriched best-of-two against raw single-shot. Preserve all attempted requests, failed calls and rejected candidates in denominators. Report accepted/requested, evaluation coverage, conditional agreement on reliable rows, and degraded/failed counts. Excluding degraded rows without coverage inflates the apparent quality.

No empirical success rate, latency, model superiority or evaluator accuracy is claimed by this specification.
