# Generation pipeline

Version 0.3 · 2026-09-26 · Supersedes v0.2 (fixed template, per-pair scene registry, no planner)

## 1. Purpose and changes from v0.2

Generate a display ad from a reference product image, typed geography and season, and freeform text content, with an auditable, resumable record of every stage. Generation is implemented first; the standalone evaluator (document 05) follows and remains the main judged deliverable.

Changes confirmed by Garmit on 2026-09-26:

| Change | Replaces |
|---|---|
| An LLM **creative planner** designs scene, composition and text styling | Fixed code template for scene/layout |
| Geography and season are predefined enums; each country has one row of objective facts. **No per geography×season registry** | Reviewed scene profile per (country, season) pair |
| **General guardrails** (stereotypes, tokenism, season contradictions, etc.) apply to every country, so adding a country is one row | Per-pair `must_not` / `avoid` lists |
| Guardrails are enforced by code checks plus an LLM reviewer; **one replan max**, then generate anyway and flag the run for evaluation | — |
| A **SQLite state store** records every stage, artifact and model call (architectural requirement; observability built on it later) | Files-only run directory |
| LLM stages use **OpenAI**; image generation uses **Google Gemini**. No Anthropic/Claude implementation for now | Gemini 3.8 Flash for analysis/selection; Claude judge |
| The planner receives **text roles and lengths only**, never the copy itself | — |

The text contract (Exact/Extract, protected phrases, frozen TextPlan) is unchanged and remains authoritative in document 05 §3.

## 2. Request

Pydantic models, explicit schema versions, `extra="forbid"`, bounded values.

| Field | Contract |
|---|---|
| request_id | Human-readable tracking ID; not content identity |
| product_image | Local PNG/JPEG/WebP path; decoded and hashed |
| geography | `Geography` enum: `US, GB, DE, JP, IN, AU, BR, AE` |
| season | `Season` enum: `spring, summer, autumn, winter` — the season as experienced in that country |
| text | TextInput: source_text, `exact`/`extract` policy, optional protected phrases (document 05 §3) |
| aspect_ratio | `1:1` only in this version |

### Country facts table (code, versioned data)

One row per enum value. Objective facts only; no creative cues. Adding a country means adding one reviewed row plus a test.

| Code | Name | Hemisphere | Climate band (primary population centres) |
|---|---|---|---|
| US | United States | northern | temperate |
| GB | United Kingdom | northern | temperate |
| DE | Germany | northern | temperate |
| JP | Japan | northern | temperate |
| IN | India | northern | tropical |
| AU | Australia | southern | temperate |
| BR | Brazil | southern | tropical |
| AE | United Arab Emirates | northern | arid |

Climate band is a declared simplification for large or varied countries. The resolver records it as an assumption, not a fact about every region.

Season months are computed from hemisphere: northern spring Mar–May, summer Jun–Aug, autumn Sep–Nov, winter Dec–Feb; southern shifted by six months. The season name is never swapped. AU winter stays "winter" (Jun–Aug).

A small **band × season contradiction table** (3 bands × 4 seasons, country-independent) lists generic contradictions. For example, `summer → snow, bare winter trees`; `tropical/arid, any season → snow, frost`; `winter, temperate → beachwear-in-sun as the main scene`. It is data, versioned and unit-tested. It feeds both guardrail checks and the prompt's avoid list.

## 3. Pipeline map

A deterministic orchestrator (code) runs stages in order. Every stage reads its inputs from the state store and writes its outputs and status back (document 06). Stages never call each other. The LLM stages ("sub-agents") are single, bounded, schema-constrained calls with no tools. None is an autonomous agent.

```text
AdRequest
 S1 intake ............... code     validate enums/text/image; reference rendition ≤1024; hashes
 S2 product_analysis ..... LLM      OpenAI vision → ProductProfile (cached per reference hash)
 S3 copy_selection
      exact .............. code     full input → TextPlan
      extract ............ LLM      OpenAI → source spans only
      validate ........... code     offsets, protected phrases, capacity → frozen TextPlan
 S4 context_resolution ... code     country row + season → ResolvedContext
 S5 creative_planning .... LLM      OpenAI → CreativePlan   (inputs exclude the copy itself)
 S6 plan_guardrails
      code_checks ........ code     schema, bounds, lexicons, zones
      review ............. LLM      OpenAI reviewer → per-rule verdicts; decision composed in code
      on reject .......... → S5 once with reasons; if still rejected, continue and flag
 S7 prompt_compilation ... code     ProductProfile + CreativePlan + TextPlan + policy → prompt
 S8 image_generation ..... Gemini   gemini-3.1-flash-image + reference image, 1:1, 1K, one call
 S9 output_gate .......... code     decode, square, long edge ≤1024, store → evaluator handoff
```

### S1 Intake

Decode bytes rather than trusting the extension. Reject unreadable, animated or oversized inputs. Proposed limits: 20 MB and **50 MP**, raised from 40 MP because the supplied `heineken-3.jpg` is about 42.2 MP. Apply EXIF orientation and convert to sRGB. Create a reference rendition with long edge ≤1024 and no enlargement. The original stays authoritative for evaluation. Resolve protected phrases to spans (document 05 §3).

### S2 Product analysis (sub-agent)

- **Model:** proposed `gpt-6-sol`, low reasoning effort, structured output.
- **Input:** reference rendition.
- **Output — ProductProfile:**
  - category
  - silhouette and shape description
  - dominant colours
  - materials and finish
  - distinctive components
  - visible label/logo text, transcribed only where legible
  - `unknown` fields
- **Rules:** cached per reference hash, so there is at most one call per unique product. A human-authored profile may replace it and is recorded as `human_supplied`. The model must not guess brand or label text it cannot read.

### S3 Copy selection

Unchanged from document 05 §3. Exact mode is code. Extract mode is one structured call (proposed `gpt-6-sol`, medium effort) returning source spans only; code validates them and freezes the TextPlan. An invalid plan ends the run as `invalid_text_plan`. There is no silent fallback.

### S4 Context resolution

Pure code. It produces ResolvedContext:
- country name, hemisphere, climate band (with the simplification note), season, months
- generic contradictions for that band × season
- the guardrail policy version

### S5 Creative planning (sub-agent)

- **Model:** proposed `gpt-6-sol`, medium effort, structured output.
- **Inputs:**
  - ProductProfile
  - ResolvedContext
  - guardrail policy text
  - canvas `1:1`
  - the zone grid
  - **text layout requirements**: for each TextPlan block, its `block_id`, role (`product_name | tagline | offer | qualifier | supporting_text`), character count, word count and line breaks.
- **Excluded:** the copy itself. The planner can size and place text areas but cannot let the words steer the scene. "Winter savings" in the copy cannot pull a summer scene towards winter.

**CreativePlan output** (`creative-plan/1`, all strings length-bounded):

```text
setting:            ≤300 chars — where the scene is, as observable elements
lighting:           time of day, light quality, direction
surface_and_props:  ≤5 items; the product's contact surface first
palette:            ≤5 named colours
people:             none | background_non_identifiable      (default none)
product_placement:  {zone, scale: fraction of frame height 0.25–0.7, orientation}
text_layout:        per block_id: {zone, size: large|medium|small, alignment,
                                   type_style: ≤60 chars, contrast_treatment:
                                   clean_background | solid_panel | gradient_scrim}
context_cues:       2–6 × {cue, kind: geography|season}   — observable things only
avoid:              ≤8 items
rationale:          advisory; stored, never compiled into the prompt
```

**Zone grid:** a fixed 3×3 enum (`top_left … bottom_right`) plus `top_band`, `bottom_band`, `left_third`, `right_third`. Code validates:
- the product zone and all text zones do not overlap;
- every TextPlan block has exactly one layout entry;
- no layout entry refers to an unknown block.

### S6 Plan guardrails

**Guardrail policy** (`policy/guardrails.yaml`, versioned, hashed; applies to every country):

| Rule | Prohibits |
|---|---|
| GR-STEREO | People, dress, accents or behaviour used as racial, ethnic, national or religious shorthand; caricature |
| GR-TOKEN | Flags, national monuments, famous landmarks or iconic wildlife as the geography signal |
| GR-RELIGION | Religious symbols, sites or ceremonies as decoration |
| GR-SEASON | Cues contradicting the resolved season or climate band (band × season table) |
| GR-PEOPLE | Identifiable real people or celebrities; minors in any scene with an age-restricted product |
| GR-ALCOHOL | For alcohol products: minors, driving, excessive consumption, health or performance claims |
| GR-TEXT | Instructions for extra text, signage, logos or watermarks in the scene; legible background text is avoided because it pollutes OCR |

Geography should come through ordinary, observable, non-stereotyped cues: architecture, streetscape, vegetation, light, materials, everyday settings.

**Code checks** run first:
- schema validity and field bounds
- zone validity
- a banned-term lexicon per rule, versioned
- band × season contradiction terms
- the CreativePlan must contain no quoted strings that could render as text

Lexicons are coarse and admit false negatives; the reviewer is the backstop.

**Reviewer** (sub-agent; proposed `gpt-6-sol`, low effort, separate prompt):
- Input: CreativePlan, ResolvedContext and policy. No image.
- Output: one verdict per rule, `pass | violation | unsure`, with a quote from the plan as evidence.
- Code checks that each quote occurs in the plan.

**Decision** (code, not model):
- `approved` if every rule passes in both code checks and review.
- `rejected` if any rule is a violation.
- `unsure` counts as a violation, conservatively; this is a proposal.

**Replan policy:**
1. On rejection, re-run S5 once. The planner receives the rule IDs and quotes.
2. If the second plan is approved, record `guardrail_status = approved_after_replan`.
3. If it is rejected again, **continue to generation** with the second plan. Record `guardrail_status = rejected_after_replan` and the reasons. The evaluator reports this flag.
4. If a plan is schema-invalid twice, no usable plan exists. The run is `blocked`, and no plan is invented.

A reviewer that shares the planner's model family gives limited independence. The flag is evidence to evaluate, not proof of safety.

### S7 Prompt compilation

Code and a versioned template. Sections:

1. **PRODUCT**, from ProductProfile: preserve silhouette, proportions, colours and the product's own label; exactly one product.
2. **SCENE**, from CreativePlan: setting, lighting, surface/props, palette, people, context cues.
3. **LAYOUT**, from CreativePlan zones: product placement, text areas and contrast treatment.
4. **TEXT**, from the frozen TextPlan. Each block's exact string is escaped and quoted, with its role and the plan's size and style. It is labelled literal copy: no paraphrase, and no extra text, logos or watermarks.
5. **AVOID**: guardrail policy lines, band × season contradictions and CreativePlan `avoid`.
6. **OUTPUT**: one image, 1:1, 1K.

The raw source text and the planner's `rationale` never enter the prompt. The prompt hash covers the template version and all inputs.

### S8 Image generation

- **Model and settings:** `gemini-3.1-flash-image` through the official `google-genai` SDK behind an `ImageGenerator` adapter. Explicit `1:1`, `1K`, minimal thinking as a pilot setting.
- **Inputs:** the reference rendition and the prompt.
- **One dispatch, no automatic retries.** SDK retries are disabled or counted.
- **Record** the requested and returned model, SDK version, request ID, usage and latency.
- **Response parsing:** exactly one final image. No image, a refusal, corrupt bytes or multiple final images are classified errors.

### S9 Output gate

Decode the image and check it is square with a long edge ≤1024. Store the canonical bytes and hand off to the evaluator. Nothing is post-edited. A generation-only run ends as `generated_unscored`.

## 4. Model calls and limits per request

| Stage | Provider / proposed model | Max calls |
|---|---|---|
| S2 product analysis | OpenAI `gpt-6-sol` | 1 per unique reference (cached) |
| S3 extract selection | OpenAI `gpt-6-sol` | 1 (Exact: 0) |
| S5 creative planning | OpenAI `gpt-6-sol` | 2 (initial + 1 replan) |
| S6 guardrail review | OpenAI `gpt-6-sol` | 2 |
| S8 image | Google `gemini-3.1-flash-image` | 1 |

Model IDs, reasoning efforts and timeouts live in versioned config (`config/pipeline.toml`), not in `.env`. They are proposals until the compatibility probe passes.

Proposed timeouts: 120 s per image, 60 s per text call. Every call is written to the state store before dispatch. A dispatched call with no recorded outcome becomes `unknown` and is never re-sent automatically.

All LLM calls go through a small provider interface with an OpenAI implementation and a record/replay implementation for offline tests. No other LLM backend is implemented in this version.

## 5. Credentials

Keys are read from environment variables loaded from a gitignored `.env`. The repository commits only `.env.example` with empty placeholders:

```text
GEMINI_API_KEY=
OPENAI_API_KEY=
```

Anyone running the pipeline supplies their own keys. Keys never appear in the state store, artifacts, logs, prompts or commits. Offline tests and replay need no keys.

## 6. State and artifacts

Stage status, artifacts, model calls and events are recorded in the SQLite state store specified in [document 06](06-state-store.md). Artifacts are files under `runs/<run_id>/`, named by content hash. The store holds their paths and hashes. Resume skips stages that already succeeded with identical input hashes.

## 7. Deferred

Best-of-N, targeted repair, text overlay fallback, Flash-Lite comparison, the enrichment ablation, UI and alternative LLM backends. If one is enabled later, it must be named explicitly, given its own budget and evaluated separately.
