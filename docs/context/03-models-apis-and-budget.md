# 03 — Models, APIs and budget

Everything here was checked against official pages on **2026-09-26**. Model lineups and prices
move fast. Re-check the two Google pages (models, pricing) on the morning of the hackathon.

---

## 1. The finding that changes the plan: the free key cannot generate images

Google's pricing page lists **"Free Tier: Not available"** for **both** image models the
problem allows. The organizers' note ("request a free API key") is therefore not enough on its
own. **Enable billing on the Gemini API project before the event** (AI Studio → set up billing;
the pricing page describes it as prepaid, then pay-as-you-go), and smoke-test one generation.

Source: https://ai.google.dev/gemini-api/docs/pricing

---

## 2. The two allowed generation models

| | **Gemini 3.1 Flash Image** ("Nano Banana 2") | **Gemini 3.1 Flash-Lite Image** ("Nano Banana 2 Lite") |
|---|---|---|
| Model code | `gemini-3.1-flash-image` (stable, Feb 2026) | `gemini-3.1-flash-lite-image` (stable, Jun 2026) |
| Input / output tokens | 131,072 / 32,768 | 65,536 / 4,096 |
| Inputs → outputs | Text, image, video, PDF → image + text | Same |
| Output sizes | 0.5K, **1K (default)**, 2K, 4K | **1K only** |
| Aspect ratios | 14, incl. 1:1, 4:5, 16:9, 1:4, 4:1, 1:8, 8:1 | 14, incl. 1:1, 3:2, 2:3, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9 |
| Reference images | Up to **10 objects** and 4 characters per workflow | Not stated in docs |
| Thinking | On by default and **cannot be disabled**; levels `minimal` and `high` | Same (`minimal`, `high`) |
| Structured output / function calling | **Not supported** | **Not supported** |
| Search grounding | Supported (incl. image search) | Not supported |
| Watermark | SynthID on every image | SynthID (always on) + C2PA |
| Speed claim | "low latency" | Google: sub-2 s target. OpenRouter: ~4 s, ~2.7× faster than Flash |
| **Price (paid tier)** | $0.50/M input; $3/M text+thinking output; $60/M image output = **$0.067 per 1K image** ($0.045 at 0.5K) | $0.25/M input; $1.50/M text output; $30/M image output = **$0.0336 per 1K image** |
| Batch API | Supported, 50% off (**$0.034 per 1K image**) | Supported (**$0.0168 per 1K image**) |
| Free tier | **Not available** | **Not available** |

Sources: model pages https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image and
https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-image ; pricing page above;
image-generation guide https://ai.google.dev/gemini-api/docs/image-generation

**Not allowed for this problem:** Gemini 3 Pro Image ("Nano Banana Pro"). It has better text
rendering, but the problem names only the two 3.1 models above.

### Output dimensions at 1K (Gemini 3.1 Flash Image) — the 1024 px trap

| Ratio | Pixels | Long edge ≤1024? |
|---|---|---|
| **1:1** | **1024×1024** | **Yes** |
| 4:5 / 5:4 | 928×1152 / 1152×928 | No |
| 3:4 / 4:3 | 896×1200 / 1200×896 | No |
| 2:3 / 3:2 | 848×1264 / 1264×848 | No |
| 9:16 / 16:9 | 768×1376 / 1376×768 | No |
| 21:9 | 1584×672 | No |
| 1:4 / 4:1 | 512×2048 / 2048×512 | No |
| 1:8 / 8:1 | 384×3072 / 3072×384 | No |

Every ratio is ~1120 output tokens at "1K", so **only square fits the ≤1024 rule natively**.
Options: default to 1:1; for other formats, downscale in code (and disclose it), or generate at
0.5K. Flash-Lite's per-ratio pixel table is not published separately. Check the returned
dimensions in the M0 smoke test.

### What Google's own docs say that matters here
- "When generating text for an image, Gemini works best if you **first generate the text and
  then ask for an image with the text**." (Limitations section.) → the pipeline's `text_plan`.
- Best-performing languages for text: EN, ar-EG, de-DE, es-MX, fr-FR, hi-IN, id-ID, it-IT, ja-JP,
  ko-KR, pt-BR, ru-RU, ua-UA, vi-VN, zh-CN. Keep ad text English by default; one non-Latin
  example is a stretch goal.
- The prompting guide has named templates worth starting from: **"Accurate text in images"**,
  **"Product mockups & commercial photography"**, **"High-fidelity detail preservation"**,
  **"Advanced composition: combining multiple images"**. Product-mockup template:
  *"A high-resolution, studio-lit product photograph of a [product description] on a
  [background surface/description]."* Text template (older 2.5 guide): *"Create a [image type]
  for [brand/concept] with the text "[text to render]" in a [font style]. The design should be
  [style description], with a [color scheme]."*
- The model "won't always follow the exact number of image outputs" requested → request one
  image per call and loop for best-of-N.

### Calling it from Python (`google-genai`)
Google's docs now lead with a newer **Interactions API**; the classic `generate_content` path
also works for this model (it is the example in the SDK's PyPI README). Pick one, wrap it in
`generate.py`, and confirm it in the M0 smoke test.

```python
# Classic path (PyPI README example for gemini-3.1-flash-image, plus image_size)
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()  # reads GEMINI_API_KEY
resp = client.models.generate_content(
    model="gemini-3.1-flash-image",
    contents=[prompt_text, Image.open("data/products/mug.png")],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="1:1", image_size="1K"),
    ),
)
img = next(p.as_image() for p in resp.parts if p.inline_data)
```

```python
# Interactions API (what the image-generation docs page now shows)
interaction = client.interactions.create(
    model="gemini-3.1-flash-image",
    input=[{"type": "text", "text": prompt_text},
           {"type": "image", "data": b64_png, "mime_type": "image/png"}],
    response_format={"type": "image", "aspect_ratio": "1:1", "image_size": "1K"},
)
# multi-turn edit: pass previous_interaction_id=interaction.id with a narrow edit instruction
```

The field name for the thinking level on image models was not confirmed. Look it up in the
image-generation docs before using it in the thinking ablation.

---

## 3. Garmit's subscriptions: what they cover and what they don't

| He has | Covers | Does **not** cover |
|---|---|---|
| **Claude Pro** | Claude chat and **Claude Code** (the coding agent) | **API usage.** Anthropic's help centre: "The Pro plan does not include API usage through the Claude Console." API needs separate Console credits |
| **ChatGPT Plus** | ChatGPT and **Codex** (web, CLI, IDE) | **API usage.** OpenAI's help centre: "API usage is separate and billed independently" |
| **Gemini free API key** | Free-tier **text** models, e.g. `gemini-3.8-flash`, `gemini-3.1-flash-lite` (the pricing page lists free-tier access for these; confirm in AI Studio). Free-tier content "is used to improve our products" | **Both image models** (no free tier) |

Sources: https://support.claude.com/en/articles/8325606-what-is-the-pro-plan ;
https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan ;
https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus

**Practical upshot:** both subscriptions pay for the *coding agents* used to build the project,
not for API calls the project itself makes.
- **Claude Code** is the primary agent
- **Codex** is the backup when Claude Pro usage limits bite during a long session, and a
  cheap second reviewer

---

## 4. Recommendation: what to buy

| Priority | Buy | Why | Suggested load |
|---|---|---|---|
| **Must** | **Gemini API billing** on the key's project | Required: both allowed image models are paid-only | $15–20 prepaid |
| **Should** | **Anthropic API credits** (Console) | A **cross-family judge** for context adherence (Gemini images judged by Claude). Garmit already knows the forced-tool-use structured-output pattern from Bedrock, which makes the judge design easy to defend in interview | $10 |
| Optional | **OpenRouter credits** instead of, or on top of, Anthropic | One key for Claude, GPT and Gemini. Makes a **judge-model comparison** (agreement of 2–3 judges with human labels) a config change. It also serves both Gemini image models at Google's list token prices ($0.50/$60 and $0.25/$30 per M) through a unified Image API. Check the fee on credit purchases at checkout | $10 |
| Free fallback | Gemini **text** model on the free tier as the judge | Costs nothing. Weaker story: a same-family judge, and free-tier data is used by Google. Say so in the write-up if used | $0 |

**Keep generation on the Google SDK directly**, even if OpenRouter is bought. The model-specific
features the design uses (multi-turn edit, thinking level, `image_size`) are first-class there.
A normalizing proxy may not expose them one-to-one.

### Claude API reference (for the judge)
Prices from claude.com/pricing (2026-09-26), per million tokens:

| Model | Model ID | Input | Output |
|---|---|---|---|
| Opus 5.5 | `claude-opus-5-5` | $4 | $20 |
| Sonnet 5 | `claude-sonnet-5` | $2 | $10 |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | $1 | $5 |

Sonnet 5 is the sensible judge default and Haiku 4.5 the cheap option. Run one calibration pass
on both and pick with evidence, the Gavel way: "Haiku, because it matched Sonnet's agreement
within the flip-rate noise at half the cost" is a defensible choice. "Haiku because it is
cheaper" is not.

---

## 5. Budget estimate (generation with Flash at $0.067/image)

| Item | Images | Cost |
|---|---|---|
| Dev iteration on prompts (M1) | ~50 | ~$3.35 |
| Golden set, best-of-2 (M2) | ~40 | ~$2.70 |
| Targeted repair edits (M6) | ~10 | ~$0.70 |
| Negatives that need a real generation (swap/season/market) | ~10 | ~$0.70 |
| Enrichment ablation (raw-fields arm) | ~20 | ~$1.35 |
| Flash-Lite ablation | ~20 | ~$0.70 |
| **Generation total** | ~150 | **~$9.50** |
| Judge: ~200 context judgments (candidates + negatives + 3× repeats) on Sonnet 5 | — | **~$1–3** (rough: 1–2K image tokens + ~1K text in, ~400 out per call) |

Input-image tokens are negligible: Google's pricing notes 1,120 tokens per input image for
Flash-Lite. Thinking tokens bill as text output ($3/M on Flash), so they matter a little at
`high`. **Everything fits in ~$15–25 total.** Keep a cost ledger in the run log anyway: "cost
per passing ad" is a result worth reporting.

---

## 6. Local models and libraries (free; CPU is fine for ~150 images)

| Job | Tool | Notes |
|---|---|---|
| Product detection | **Grounding DINO** via HF transformers, `IDEA-Research/grounding-dino-tiny` | `AutoModelForZeroShotObjectDetection` + `post_process_grounded_object_detection` |
| Product identity similarity | **DINOv2** (HF `facebook/dinov2-small` or `-base`) | Primary fidelity signal (DreamBooth's DINO metric) |
| Secondary similarity | CLIP or SigLIP | Report beside DINOv2 |
| Masking / cut-out | SAM (optional), **rembg** | For colour stats and cleaner crops |
| Colour difference | scikit-image `deltaE_ciede2000` | On masked product pixels, CIELAB |
| OCR | **PaddleOCR** (most accurate; heavier install), **EasyOCR** (easy, PyTorch) | Pre-install both before the day |
| String distance | `rapidfuzz` | Levenshtein / NED |
| Tests | `pytest`, record/replay cache for judge calls | No network in tests |
| UI (phase 2) | Streamlit or Gradio | Thin layer over `pipeline.run()` |

**Before the event:** download the HF weights (Grounding DINO, DINOv2, CLIP/SigLIP), install
PaddleOCR and EasyOCR, and run each once on a sample image, so no install happens on the clock.

---

## 7. Hackathon-morning checklist

- [ ] Gemini billing enabled; one `gemini-3.1-flash-image` call at 1:1/1K returns **1024×1024**
- [ ] One Flash-Lite call works; dimensions noted
- [ ] Judge API key works; one structured (JSON/tool) response from an image input
- [ ] HF weights cached; PaddleOCR/EasyOCR run on a sample
- [ ] 4–5 product photos ready, sources/licences noted
- [ ] `.env` in `.gitignore`; no key ever committed
