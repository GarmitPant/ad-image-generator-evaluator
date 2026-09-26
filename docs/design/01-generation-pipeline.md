# Generation pipeline

Version 0.4 · 2026-09-26 · Supersedes v0.3 (single image; per-rule guardrail review) and v0.2 (fixed template, per-pair scene registry)

## 1. Purpose and confirmed changes

For one input, the pipeline:
1. generates **three candidate ads**, each from its own creative plan;
2. **evaluates every candidate**;
3. **ranks** them in code;
4. **presents the highest-ranked one**;
5. saves every image and record.

Batched evaluation across many requests comes after this flow works. The evaluator (document 05) remains the main judged deliverable. Generation is implemented first.

Confirmed by Garmit on 2026-09-26:

| Decision | Replaces |
|---|---|
| LLM **creative planner** designs scene, composition and text styling. It sees text **roles and lengths only**, never the copy | Fixed code template |
| Geography: enum of 8 countries, one row of facts each. Season: enum. No per geography×season registry | Per-pair scene profiles |
| **Simple, functional, predefined guardrails**: one static versioned file with global rules plus optional per-country notes. No web lookup. Rigour goes into evaluation | v0.3 per-rule evidence-verified review |
| Guardrails: planner gets the rules, keyword check, one reviewer call (approve/reject + reasons), **one replan**, then generate anyway and flag | — |
| **3 candidates per request, one plan per candidate**; evaluate all; present the best; keep all | v0.2/v0.3 single image, no ranking (D04, D07) |
| **1–3 reference images** per product | Single reference |
| Generated images are saved: all candidates under the run, the winner exported to `outputs/` | — |
| SQLite state store for all stages (document 06) | Files only |
| OpenAI for LLM stages, Gemini for images, no Anthropic code; local evaluator vision models only | Gemini 3.8 Flash text stages; Claude judge |
| Repository commits `.env.example` placeholders only | — |

The text contract (Exact/Extract, protected phrases, frozen TextPlan) is unchanged. It is defined in document 05 §3.

## 2. Request

Pydantic models with explicit schema versions, `extra="forbid"` and bounded values.

| Field | Contract |
|---|---|
| request_id | Human-readable tracking ID; not content identity |
| product_images | **1–3** local PNG/JPEG/WebP paths showing the **same** product. Each is decoded and hashed; order is preserved; duplicates (same hash) are rejected |
| geography | `Geography` enum: `US, GB, DE, JP, IN, AU, BR, AE` |
| season | `Season` enum: `spring, summer, autumn, winter`, as experienced in that country |
| text | TextInput: source_text, `exact`/`extract` policy, optional protected phrases |
| candidates | Integer 1–4, default **3** |
| aspect_ratio | `1:1` only in this version |

The system cannot verify that several references show the same product. That is the user's declaration. The product-analysis stage reports visible inconsistencies between references as warnings.

### Country facts and seasons (code, versioned data)

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

- Months come from the hemisphere: northern spring Mar–May, summer Jun–Aug, autumn Sep–Nov, winter Dec–Feb; southern is shifted six months. The season name is never swapped.
- The climate band is a declared simplification.
- A small, country-independent **band × season contradiction table** (for example `summer → snow`, `tropical/arid → snow, frost`) feeds the planner's avoid list and the keyword check.

## 3. Pipeline map

A deterministic code orchestrator runs the stages. Each stage reads its inputs from the SQLite state store and writes its outputs and status back (document 06). Stages S5–S10 run **once per candidate** (`candidate_index` 1…N). LLM "sub-agents" are single bounded, schema-constrained calls with no tools.

```text
AdRequest
 S1  intake ................ code     enums, text, 1–3 references → renditions ≤1024, hashes
 S2  product_analysis ...... LLM      OpenAI vision, all references → one ProductProfile (cached by reference set)
 S3  copy_selection ........ code | LLM   Exact in code; Extract = OpenAI spans → validated, frozen TextPlan
 S4  context_resolution .... code     country row + season → ResolvedContext + guardrail policy
 ── per candidate i = 1..N ────────────────────────────────────────────────────────────────
 S5  creative_planning ..... LLM      OpenAI → CreativePlan_i  (roles + lengths, never the copy;
                                      told to differ from plans 1..i-1)
 S6  plan_guardrails ....... code + LLM   keyword check + reviewer → approve | reject(reasons)
                                      reject → S5 once; still rejected → continue, flag
 S7  prompt_compilation .... code     ProductProfile + CreativePlan_i + TextPlan + policy → prompt_i
 S8  image_generation ...... Gemini   gemini-3.1-flash-image + all references, 1:1, 1K, one call
 S9  output_gate ........... code     decode, square, ≤1024 → save candidates/c{i}.png
 S10 evaluation ............ evaluator (document 05) → EvalRecord_i with verdicts + scores
 ── after all candidates ──────────────────────────────────────────────────────────────────
 S11 selection ............. code     rank candidates → winner + reasons
 S12 export ................ code     outputs/<request_id>/<run_id>/best.png + summary.json
```

A failed candidate (refusal, invalid image, blocked plan) does not stop the others. It is recorded and ranked last. The run succeeds if at least one candidate reaches S10.

### S1 Intake

- **Decode** the bytes rather than trusting the file extension.
- **Reject** unreadable or animated images, and files over 20 MB or 50 MP.
- **Normalize:** apply EXIF orientation, convert to sRGB, make a rendition with long edge ≤1024 without enlarging.
- **Keep originals:** they stay authoritative for evaluation.
- **Protected phrases:** resolve them to spans.

### S2 Product analysis (sub-agent)

- **Model:** proposed `gpt-6-sol`, low effort.
- **Input:** all reference renditions in one call.
- **Output — ProductProfile:**
  - category, silhouette, dominant colours, materials, distinctive components
  - visible label/logo text, only where legible
  - `unknown` fields
  - `reference_inconsistencies` warnings
- **Caching:** by the sorted set of reference hashes. A human-supplied profile may replace the model's and is recorded as `human_supplied`.

### S3 Copy selection

As in document 05 §3. Exact mode is code; Extract mode is one structured call. The code validator freezes the TextPlan. All candidates share this one TextPlan, so candidates differ in visuals, not copy.

### S4 Context resolution

Pure code. It produces ResolvedContext: country, hemisphere, climate band (with note), season, months, band × season contradictions, the guardrail policy version and any per-country notes.

### S5 Creative planning (sub-agent, per candidate)

- **Model:** proposed `gpt-6-sol`, medium effort.
- **Inputs:**
  - ProductProfile
  - ResolvedContext
  - the guardrail rules
  - canvas and zone grid
  - text layout requirements: per TextPlan block, `block_id`, role, character and word counts, line breaks
  - summaries of earlier candidates' plans (setting, lighting, placement), so each candidate explores a different concept
- **Excluded:** the copy itself.

**CreativePlan output** (`creative-plan/1`, bounded strings):

```text
concept:            ≤120 chars, one-line idea distinguishing this candidate
setting:            ≤300 chars, observable elements
lighting:           time of day, light quality, direction
surface_and_props:  ≤5 items; product contact surface first
palette:            ≤5 named colours
people:             none | background_non_identifiable (default none)
product_placement:  {zone, scale 0.25–0.7 of frame height, orientation}
text_layout:        per block_id: {zone, size large|medium|small, alignment,
                                   type_style ≤60 chars,
                                   contrast_treatment clean_background|solid_panel|gradient_scrim}
context_cues:       2–6 × {cue, kind: geography|season}
avoid:              ≤8 items
rationale:          advisory; stored, never sent to the image model
```

Code validates:
- the zones come from a fixed 3×3 grid plus bands and thirds;
- the product and text zones don't overlap;
- every TextPlan block has exactly one layout entry.

### S6 Plan guardrails (simple, functional)

**Policy file** `policy/guardrails.yaml`: predefined, static, versioned and hashed. No web lookup.

```yaml
version: 1
global_rules:            # sent to planner and reviewer
  - id: GR-STEREO    text: No people, dress, accents or behaviour used as racial, ethnic, national or religious shorthand; no caricature.
  - id: GR-TOKEN     text: No flags, national monuments, famous landmarks or iconic wildlife as the geography signal.
  - id: GR-RELIGION  text: No religious symbols, sites or ceremonies as decoration.
  - id: GR-SEASON    text: No cues contradicting the resolved season or climate.
  - id: GR-PEOPLE    text: No identifiable real people; no minors with age-restricted products.
  - id: GR-ALCOHOL   text: For alcohol, no minors, driving, excessive drinking or health claims.
  - id: GR-TEXT      text: No extra text, signage, logos or watermarks in the scene.
keywords:                # coarse keyword check; misses are expected, reviewer is the backstop
  GR-TOKEN: [flag, kangaroo, eiffel, taj mahal, ...]
  ...
country_notes:           # optional, short; most countries have none
  AE: [Alcohol advertising is restricted; alcohol products are flagged for review.]
```

**Flow:**
1. The planner receives the rules.
2. The code keyword check runs on the plan (including band × season contradiction terms).
3. One reviewer call (proposed `gpt-6-sol`, low effort) returns `{decision: approve|reject, reasons: [{rule_id, explanation}]}`.
4. A keyword hit or a reviewer reject counts as a rejection.
5. On rejection, re-run S5 once with the reasons. If the new plan is still rejected, generate anyway and set that candidate's `guardrail_status = rejected_after_replan`.
6. If the plan is schema-invalid twice, that candidate is `blocked`.

Adding a region means editing this file. Guardrails are intentionally simple here. Checking guardrail compliance in the generated *image* belongs to the evaluator.

### S7 Prompt compilation

Code with a versioned template. It has six sections:
1. **PRODUCT**, from ProductProfile. All references are attached; preserve identity; exactly one product.
2. **SCENE**, from CreativePlan.
3. **LAYOUT**, from CreativePlan zones.
4. **TEXT**, from the frozen TextPlan: exact escaped strings, with styles from the plan, labelled literal copy.
5. **AVOID**: global rules, band × season contradictions and plan `avoid`.
6. **OUTPUT**: 1:1, 1K.

Raw source text and the planner's rationale never enter the prompt.

### S8 Image generation

- **Model and settings:** `gemini-3.1-flash-image` through the `google-genai` SDK behind an `ImageGenerator` adapter. Explicit 1:1, 1K, minimal thinking as a pilot setting.
- **Inputs:** the prompt plus all reference renditions.
- **One dispatch per candidate, no automatic retries.**
- **Record** the requested and returned model, SDK version, request ID, usage and latency.
- **Response classification:** refusal, no image, corrupt bytes or multiple images.

### S9 Output gate

Decode the image and check it is square with a long edge ≤1024. Write `runs/<run_id>/candidates/c{i}.png` atomically. Nothing is post-edited.

### S10 Evaluation

The standalone evaluator (document 05) scores each candidate. It receives:
- the original references
- the source text contract and TextPlan
- ResolvedContext and guardrail policy
- the candidate image
- the candidate's `guardrail_status`

It returns an EvalRecord with dimension verdicts and scores. The evaluator never calls generation. It also runs independently on stored images and in batch mode later.

### S11 Selection (code)

Candidates are ranked by, in order:
1. **overall verdict tier:** `pass` > `unknown` > `fail` > not evaluated;
2. **fewer failed required checks**;
3. **higher overall score** (document 05 §7);
4. **guardrail status:** `approved` > `approved_after_replan` > `rejected_after_replan`;
5. lower `candidate_index` as a deterministic tie-break.

The top candidate is presented:
- If its verdict is `pass`, it is presented as **approved**.
- Otherwise it is presented as **best available, not approved**, with its failed or unknown checks listed.

A high score never overrides a failed required check.

### S12 Export

The pipeline writes `outputs/<request_id>/<run_id>/` containing:
- `best.png`
- `summary.json`: ranking table, per-candidate verdicts and scores, winner, reasons, guardrail flags, costs
- `candidates/` with all candidate images

`adgen export <run_id>` regenerates this folder from the state store.

`runs/` and `outputs/` are gitignored. Curated golden and demo sets are copied into `data/` deliberately.

## 4. Model calls and limits per request (N = 3)

| Stage | Provider / proposed model | Max calls |
|---|---|---|
| S2 product analysis | OpenAI `gpt-6-sol` | 1 per unique reference set (cached) |
| S3 extract selection | OpenAI `gpt-6-sol` | 1 (Exact: 0) |
| S5 creative planning | OpenAI `gpt-6-sol` | 2 per candidate → 6 |
| S6 guardrail review | OpenAI `gpt-6-sol` | 2 per candidate → 6 |
| S8 image | Google `gemini-3.1-flash-image` | 1 per candidate → 3 |
| S10 evaluation | per document 05 (OpenAI judge + local models) | bounded per candidate |

Model IDs, efforts, timeouts, price tables and N live in `config/pipeline.toml`. Proposed timeouts are 120 s per image and 60 s per text call. Every call is recorded before dispatch. A dispatched call with no outcome becomes `unknown` and is never re-sent automatically. The run-level budget cap is checked before every dispatch.

All LLM calls use one provider interface with an OpenAI implementation and a record/replay implementation for offline tests. No other LLM backend is implemented.

## 5. Credentials

Keys come from a gitignored `.env`. The repository commits only `.env.example`:

```text
GEMINI_API_KEY=
OPENAI_API_KEY=
```

Users supply their own keys. Keys never appear in the state store, artifacts, logs, prompts or commits. Offline tests and replay need no keys. The local evaluator models need no keys; they need a one-time weight download (document 05 §6).

## 6. Deferred

Targeted repair, text-overlay fallback, Flash-Lite comparison, the enrichment ablation, UI, hosted (remote) evaluator models and alternative LLM backends.
