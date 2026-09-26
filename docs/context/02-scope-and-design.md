# 02 — Scope and design

This is the proposed design. It is a starting point for the implementing agent, not a frozen
spec: where the agent finds a better option, it proposes the change to Garmit and records the
decision in the new repo's `docs/decisions.md`. Facts about models and prices live in
`03-models-apis-and-budget.md`; sources for every method named here are in `04-prior-art.md`.

---

## 1. The core idea in one paragraph

The structured context is turned into **data before it reaches any model**: a typed request
resolves against a market registry into a creative brief (hemisphere-adjusted season, concrete
visual cues, things that must *not* appear). That brief drives the generation prompt **and** the
evaluator's checklist, so what we ask for and what we check are the same list. The evaluator
runs inside the pipeline: generate a few candidates, score each on three metrics with
deterministic checks wherever possible and a model judge only where no deterministic check
exists, keep the best, retry failures with a targeted edit, and label what still fails. Scores
are composed in code, never by a model.

This mirrors Garmit's LLM-as-judge harness at Amazon (see `05-personal-context.md` §3): the
rubric is a contract, composition is data, and every model claim is checked against something
mechanical.

---

## 2. Typed inputs

"Strongly typed" is a hard requirement from Garmit. Sketch (Pydantic v2; the agent may refine):

```python
from enum import StrEnum
from pydantic import BaseModel, Field, field_validator

class Season(StrEnum):
    SPRING = "spring"; SUMMER = "summer"; AUTUMN = "autumn"; WINTER = "winter"

class Market(StrEnum):
    # ISO 3166-1 alpha-2. Only markets with a profile in the registry are allowed.
    US = "US"; GB = "GB"; DE = "DE"; JP = "JP"; IN = "IN"; AU = "AU"; BR = "BR"; AE = "AE"

class AspectRatio(StrEnum):          # extension; default 1:1
    SQUARE = "1:1"; PORTRAIT_4_5 = "4:5"; LANDSCAPE_16_9 = "16:9"

class AdRequest(BaseModel):
    product_image: Path               # validated: exists, PNG/JPEG/WebP, min side >= 512 px
    geography: Market
    season: Season
    ad_text: str = Field(min_length=1, max_length=60)   # verbatim; no translation
    aspect_ratio: AspectRatio = AspectRatio.SQUARE

    @field_validator("ad_text")
    def _clean(cls, v): ...           # strip, collapse whitespace, reject control chars,
                                      # cap word count (e.g. <= 8) since long text renders worse
```

### The market registry is where "enrichment" lives
`markets.yaml` (data, versioned, unit-tested) holds one profile per market:

```yaml
AU:
  name: Australia
  hemisphere: southern          # season months flip
  climate: temperate/arid; tropical north
  primary_languages: [en-AU]
  seasons:
    winter:
      months: [6, 7, 8]
      cues: [cool coastal light, light jackets, eucalyptus/bush landscapes, cafe culture]
      must_not: [snow-covered Christmas scenes, heavy alpine snow as default]
    summer:
      months: [12, 1, 2]
      cues: [beach, bright harsh sun, outdoor BBQ, Christmas-in-summer is plausible]
      must_not: [snow, autumn leaves]
  setting_cues: [Australian urban/coastal architecture, native flora]
  avoid: [kangaroo-on-every-image stereotypes, outback caricature]
```

Why data and not a prompt to an LLM: it is auditable, testable (`AU + winter` must never yield
snow-Christmas cues), identical on every run, and it is **the same list the evaluator checks**.
An LLM may *elaborate* the brief (turn cues into a scene description) but only inside the
registry's `cues` and `must_not`, validated against a schema.

**Edge cases to encode and test** (they make good write-up material):
- **Southern hemisphere**: AU/BR winter is June–August; Christmas falls in summer
- **Tropical/equatorial markets** (IN, parts of BR, AE): "winter" is mild; IN has a monsoon.
  The profile maps the four enum values to what they plausibly mean there and says so
- **Stereotype avoidance**: every profile has an `avoid` list; the evaluator checks it

Pick **6–8 markets**, including at least one southern-hemisphere market and one tropical
market. More markets add typing surface, not insight.

---

## 3. Pipeline

```
AdRequest (typed)
  │
  ├─(1) Reference analysis ── vision model → ProductProfile (category, colours, distinctive
  │                            features, visible label/logo text). Cached per image hash.
  │                            Local: product detected once (Grounding DINO), crop saved as
  │                            the reference crop for fidelity checks.
  │
  ├─(2) Context expansion ──── registry lookup (deterministic) → CreativeBrief
  │                            {season_resolved, scene_cues, must_not, palette, text_plan}
  │                            optional LLM elaboration constrained to the registry
  │
  ├─(3) Prompt compilation ─── versioned template + brief + profile → prompt; prompt_hash
  │
  ├─(4) Generate ───────────── Gemini 3.1 Flash Image, 1K, N candidates (N = 2–3)
  │
  ├─(5) Post-process ───────── enforce long edge ≤1024 (Lanczos) and record it; save PNG
  │
  ├─(6) Evaluate ───────────── text / product / context metrics → EvalRecord per candidate
  │
  ├─(7) Select or repair ───── best passing candidate; else targeted edit retry (max 1–2);
  │                            else text-overlay fallback (if allowed, labelled); else FAIL
  │
  └─(8) Persist ────────────── append-only JSONL run log + images + cost/latency ledger
```

### Generation strategy (task 2 asks us to *decide* one; these are the decisions)
1. **Text-first, per Google's own guidance.** The image-generation docs state that Gemini
   "works best if you first generate the text and then ask for an image with the text". So the
   brief includes a `text_plan` (exact string in quotes, font style described in words,
   placement zone, contrast requirement) produced *before* the image call.
2. **Product-preservation instruction plus the reference image.** The prompt names what must
   not change (shape, colour, logo, label text) using the `ProductProfile`. Google's prompting
   guide has "high-fidelity detail preservation" and "product mockup" templates to start from.
3. **Composition for an ad.** Product as focal point; a clean zone for the headline; no other
   text; no watermarks; no second copy of the product.
4. **Best-of-N (N = 2–3), selected by the evaluator.** The evaluator is the quality gate, not a
   report card.
5. **Targeted repair using multi-turn editing.** When a candidate fails one metric only, send a
   narrow edit ("change only the headline to read exactly '…'; change nothing else") instead of
   regenerating from scratch. The Gemini image models support conversational editing.
6. **Text fallback.** If text still fails, generate/edit with the text zone left clean and
   overlay the exact string with Pillow. Output is labelled `text_source: overlay`. **Only if
   the organizers allow it** (assumption 1); results report model-rendered and overlay rates
   separately.
7. **Resolution guard.** 1:1 at 1K is natively 1024×1024. **Every other aspect ratio at 1K
   exceeds 1024 on the long edge** (16:9 is 1376×768; see `03` §2). Non-square outputs are
   downscaled in code and the step is disclosed. A test asserts every committed image is
   ≤1024.

### Levers worth an ablation (only if time; each is one table in the write-up)
| Ablation | Question it answers |
|---|---|
| **Enriched brief vs raw fields in the prompt** | **Does structured context actually improve context adherence?** This is the problem's own premise. **Do this one.** ~20 extra images, ~$1.40 |
| Flash vs Flash-Lite | Quality vs cost/latency |
| Thinking `minimal` vs `high` | Does model reasoning help text or context? |
| Reference with vs without background removal | Does a clean cut-out improve fidelity or hurt edges? |

---

## 4. Evaluator

### Design rules (carried over from the Gavel judge harness)
- **Deterministic first.** A model judges only what no deterministic check can.
- **A model's claim is cross-checked by a second, independent reader.** The image analogue of
  Gavel's substring-verified evidence quote: if the vision judge says the text reads X, OCR must
  agree; if it says the product is present, the detector must also find it. Disagreement →
  `degraded`, not a guess.
- **Composition is code.** The model never returns an overall score or an overall pass.
- **Three terminal states.** `ok`, `degraded` (a score exists but under compromised conditions:
  OCR engines disagree, judge output needed repair, detector confidence borderline), `failed`
  (no score: API error, content filtered). Headline metrics use `ok` rows only; `degraded`
  counts are reported beside them.
- **Every record carries** `prompt_hash`, `model_version`, `evaluator_version`, thresholds used.

### Metric 1 — Text rendering fidelity (mostly deterministic)
1. OCR the image with a primary engine (PaddleOCR; EasyOCR as a lighter fallback). Optionally a
   second reader (a vision model asked to transcribe) as the cross-check.
2. Locate the required string inside the OCR output with best-substring alignment (the
   TextInVision benchmark's algorithm is a good reference: exact substring → 0; else align
   word-by-word, then edit distance on the remainder).
3. Compute:
   - **Exact match (strict)** — case and punctuation preserved. Literature name: sentence
     accuracy (Sen.Acc)
   - **NED** — 1 − normalized Levenshtein, on a lenient normalization (casefold, unify quotes,
     collapse whitespace)
   - **Missing words** — required words absent from OCR
   - **Extra text** — OCR tokens that are not the required text and not on the product's own
     label (hallucinated gibberish is a common failure)
4. **Pass (initial, to be calibrated):** NED ≥ 0.95 **and** no missing words **and** no extra
   text block above a small size. Report strict exact-match beside it.
5. **Degraded** when the two readers disagree materially, or OCR confidence is low.

### Metric 2 — Product fidelity (local vision models + one model check)
1. **Detect** the product in the generated image with Grounding DINO (HF
   `IDEA-Research/grounding-dino-tiny`), prompting with the `ProductProfile.category`. No
   detection → **fail** (gate). More than one confident detection → flag duplicate.
2. **Crop** (optionally mask with SAM, or cut out with rembg) both the reference and the
   generated product.
3. **Embedding similarity**: DINOv2 cosine between crops is the primary signal. DreamBooth
   introduced the DINO metric because it tracks human judgment of *subject identity* better than
   CLIP image similarity, which rewards "same kind of thing". CLIP/SigLIP similarity is reported
   as secondary.
4. **Colour check**: dominant-colour ΔE2000 (CIELAB) between masked product pixels. Catches
   recolours that embeddings forgive.
5. **Label/logo text**: if the reference has readable text on the product, OCR the generated
   crop and compare (NED). Catches garbled branding.
6. **Model check (tie-breaker, not the verdict)**: a vision model sees both crops and lists
   concrete differences. Used for the evidence field and to flag cases near the threshold.
7. **Pass (initial):** detected **and** DINOv2 similarity ≥ τ_sim **and** ΔE ≤ τ_col **and**
   (no label text **or** label NED ≥ τ_lbl). τ values are set from the score distributions of
   positives vs constructed negatives on a dev split, then frozen.

### Metric 3 — Context adherence (model judge on a compiled checklist)
Method: question-generation/answering in the style of TIFA, DSG and Google's Gecko. The
checklist is **compiled from the same CreativeBrief that drove generation**. The judge is not
asked "is this a good winter ad for Japan?"; it is asked atomic yes/no questions:

```
gate      Q0  Is there a product clearly visible as the main subject?            (dependency root)
geography Q1  Does the setting plausibly look like {market.name}? Name what shows it.
          Q2  Is any element clearly inconsistent with {market.name}?            (inverse)
season    Q3  Are there {season_resolved} cues (e.g. {cues[:3]})? Name them.
          Q4  Is any cue from a different season present (e.g. {must_not})?     (inverse)
ad        Q5  Is the composition usable as a display ad (focal product, clear text area)?
safety    Q6  Does the image rely on a stereotype from the avoid list?          (inverse)
```

- Answers come back as **structured output** (JSON schema / tool call): `{answer: yes|no,
  seen: "<short description of the visible element>", confidence}`. The `seen` field is the
  evidence. Structured output is enforced at the API boundary, as in Gavel.
- **Score** = weighted fraction of satisfied questions, computed in code. **Hard fail** on Q0
  = no or any inverse question = yes (a wrong-season cue sinks the ad).
- **Judge model from a different family than the generator** (e.g. Claude or GPT judging Gemini
  output) because judges are documented to prefer their own family's output. If budget forces a
  Gemini judge, say so in the limitations.
- **Stability:** re-ask a sample 3 times and report the **flip rate**. It is the noise floor;
  any threshold effect smaller than it is noise.

### Technical gates (deterministic, always first)
Valid image; long edge ≤1024; aspect ratio as requested; not blank or near-uniform. Any failure →
the candidate fails without spending judge calls.

### Composition (code, not model)
```
PASS(candidate) = gates_ok AND text.pass AND product.pass AND context.pass
rank_score      = weighted geometric mean of the three metric scores (for best-of-N only)
```
A great background cannot buy back a wrong product. That is why it is AND, not an average.

---

## 5. Golden dataset

| Part | Content | Size |
|---|---|---|
| Products | 4–5 reference photos. **Best: photograph real products yourself** (no licence issues). Choose distinctive shapes, strong colours, and **at least 2 with printed label text** (fidelity checks need something to catch) | 4–5 |
| Requests | `requests.yaml`: product × (market, season) × text. Cover both hemispheres, one tropical market, text lengths 1–8 words, one with a number/percent/currency sign (hard for OCR and generation) | ~20 |
| Generated images | Committed PNGs (≤1024), each with its EvalRecord | ~20 selected (+ rejected candidates optional) |
| Human labels | `labels.csv`: request_id, metric, pass/fail, note. Labelled by Garmit **before** looking at evaluator scores | ~60 labels (20 × 3) |
| Constructed negatives | `negatives/manifest.yaml`, each with the metric it must fail on | ~20–25 |

### Constructed negatives (the evaluator's test fixtures)
Built by controlled perturbation, so the correct verdict is known by construction. This is the
same idea as the perturbation flip rate in Gavel's calibration design.

| Metric targeted | How to build it | Cost |
|---|---|---|
| Text | Overlay the required text with **one typo** / a **missing word** / **wrong case**; overlay **extra gibberish text**; image with **no text** | Free (Pillow) |
| Product | Generate with a **different product's** reference; **hue-shift** the product region; **remove** the product (crop/inpaint); **two copies** | Mostly free; swaps cost a generation each |
| Context | Generate with the **opposite season**; **wrong market**; **plain studio background** (no context); AU winter with **snowy Christmas** | One generation each |
| Gates | 1376×768 un-resized output; blank image | Free |

Also include **near-miss positives** (e.g. text correct but in a different font; product at a
different angle) to prove the evaluator is not simply strict.

---

## 6. Tests (pytest)

| Layer | What it proves | Needs network? |
|---|---|---|
| Unit | Schema rejects bad markets/seasons/text; hemisphere mapping; registry `must_not` never contradicts `cues`; prompt compilation is deterministic and hashed; NED maths; composition truth table; resize guard | No |
| Evaluator behaviour | Each constructed negative **fails on its target metric**; each gold positive passes; near-misses pass | No — judge responses are **recorded** and replayed |
| Agreement | Evaluator vs human labels per metric: agreement %, Cohen's kappa, confusion matrix; test asserts a floor (e.g. ≥85%) and prints counts | No |
| Live smoke (opt-in, `-m live`) | One real generation + one real judge call work end to end | Yes |

**Record/replay:** the judge client caches responses keyed by `(image_sha256, prompt_hash,
model_version)`. Tests run from the cache; a missing key in CI is a test error, not a live call.
This keeps tests deterministic, free, and runnable from a clean clone.

---

## 7. Success criteria (state these in the write-up *before* the results)

Initial targets. Adjust them after the first real run and say so, but write them down first.

**Evaluator (the part the problem asks us to prove)**
- Catches **100% of constructed negatives on their target metric**
- Passes **≥90% of hand-labelled good outputs** (false-fail rate ≤10%)
- Agreement with Garmit's labels **≥85% per metric**, reported with kappa and counts
- Judge flip rate on repeat reported (noise floor)

**Pipeline**
- **100%** of committed images ≤1024 px long edge (test-enforced)
- **≥80%** of the ~20 requests reach a passing image within 3 attempts
- First-attempt pass rate reported separately from after-repair rate
- Text: model-rendered exact-match rate reported; overlay fallback rate reported separately
- Cost per passing ad and median latency reported
- Enrichment ablation: context-adherence score with the enriched brief vs raw fields

Be honest about sample size: 20 requests is small. Report counts ("17/20"), not only
percentages, and do not claim statistical significance.

---

## 8. Build order and time budget (5–8 hours)

| # | Milestone | Budget | Cut if late? |
|---|---|---|---|
| M0 | Repo, uv/venv, `.env`, **live smoke test: one Gemini image at 1K, check its dimensions** | 0:30 | No |
| M1 | Typed schema + market registry + prompt compiler + single generation path | 1:00 | No |
| M2 | Generate the ~20 golden images (N=2 each); persist records | 0:45 | No |
| M3a | Text metric (OCR + NED) + gates + composition | 0:45 | No |
| M3b | Product metric (detect, crop, DINOv2, ΔE) | 1:00 | ΔE and label-OCR can go |
| M3c | Context metric (compiled checklist + judge + record/replay) | 1:00 | No |
| M4 | Constructed negatives + evaluator tests | 0:45 | Keep ≥2 per metric |
| M5 | Human labels + agreement report | 0:30 | No |
| M6 | Best-of-N selection + one targeted repair loop in the pipeline | 0:30 | Repair loop can go |
| M7 | Write-up + agent disclosure | 0:45 | No |
| M8 | Enrichment ablation | 0:20 | Yes, but it answers the problem's premise |
| M9 | UI (Streamlit or Gradio) over `pipeline.run()` | 0:45 | Yes |

If time runs short, cut from the bottom and from the "Cut if late?" column. Never cut the
tests, the labels, or the write-up.

---

## 9. Suggested repo layout (new repo)

```
g2-adgen/
  AGENTS.md                 # from AGENT_BRIEF.md in this folder
  README.md                 # how to run; links the write-up
  pyproject.toml            # uv
  .env.example              # GEMINI_API_KEY=, ANTHROPIC_API_KEY= / OPENAI_API_KEY= / OPENROUTER_API_KEY=
  src/adgen/
    schema.py               # AdRequest, ProductProfile, CreativeBrief, EvalRecord
    markets.yaml, markets.py
    brief.py                # registry → CreativeBrief (+ optional constrained LLM elaboration)
    prompts/                # versioned templates; prompt_hash
    generate.py             # Gemini image client, retries, cost ledger
    postprocess.py          # resize guard, overlay fallback
    pipeline.py             # generate → evaluate → select/repair
    eval/
      gates.py  text.py  product.py  context.py  compose.py
      judge_client.py       # provider-agnostic, structured output, record/replay cache
    store.py                # append-only JSONL, single writer
    cli.py
  data/products/  data/requests.yaml  data/golden/  data/negatives/  data/judge_cache/
  tests/unit/  tests/evaluator/  tests/live/
  reports/                  # agreement tables, score-distribution plots
  docs/WRITEUP.md  docs/agent-collaboration.md  docs/decisions.md
  ui/app.py                 # phase 2
```

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| Free API key cannot generate images (image models have **no free tier**) | Enable billing before the event; smoke-test at M0 |
| Non-square 1K outputs exceed 1024 px | Default 1:1; resize guard; test |
| OCR misreads stylised ad fonts, making text scores wrong | Two readers, `degraded` on disagreement; hand labels expose OCR error rate |
| Judge prefers Gemini's own outputs | Cross-family judge; flip-rate and agreement reported |
| Thresholds tuned on the same images they are reported on | Dev/test split of negatives and positives; freeze thresholds before the final report |
| Generation non-determinism makes tests flaky | Tests never generate; they read committed images and recorded judge answers |
| PaddleOCR install friction on the day | Pre-install; EasyOCR as fallback; vision-model OCR as last resort |
| Real brand logos in generated ads | Prefer own or unbranded products; note it in limitations |
| 20 images is a small sample | Report counts; call it a smoke-scale evaluation, not a benchmark |

---

## 11. Coding-agent disclosure plan (required by the submission)

Keep it cheap by doing it as you go:
1. Commit this context bank (or a copy) into the new repo's `docs/context/`. It *is* the
   architectural requirements document the organizers ask for.
2. The agent appends to `docs/agent-collaboration.md` at the end of each milestone: what it was
   asked (prompt summary), what it produced, what Garmit changed or rejected, and why.
3. `docs/decisions.md` records each design decision with the alternative considered.
4. The final write-up has a short "How the agent was directed" section that links both files.
