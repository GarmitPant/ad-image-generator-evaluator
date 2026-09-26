# Model choices and source audit

Version 0.3 · 2026-09-26. Capability statements are documentation-backed. Task suitability is a proposal awaiting the compatibility probe. No model has been called or benchmarked.

## 1. Providers (confirmed by Garmit, 2026-09-26)

- **Google Gemini API:** image generation only.
- **OpenAI API:** all text and vision LLM stages, in both generation and evaluation.
- **No Anthropic/Claude implementation for now.** Claude models may be a future backup. No client, config or code path for them is written in this version.

## 2. Roles

| Responsibility | Proposed choice | Notes |
|---|---|---|
| Product analysis (S2) | `gpt-6-sol`, low effort, vision + structured output | Cached per reference |
| Extract copy selection (S3) | `gpt-6-sol`, medium effort | Spans only |
| Creative planning (S5) | `gpt-6-sol`, medium effort | Sees text roles and lengths only |
| Guardrail review (S6) | `gpt-6-sol`, low effort, separate prompt | Same family as the planner, so independence is limited; disclose it |
| Image generation (S8) | `gemini-3.1-flash-image`, 1:1, 1K | Organizer-allowed; Flash-Lite deferred |
| Prompt assembly, validation, routing, verdicts | Python code | — |
| Evaluator semantic and visual judge | `gpt-6-sol` (proposal) | Cross-family relative to the Gemini generator; same family as the planner, so it must not take planner outputs as criteria |
| OCR | PP-OCRv5 (PaddleOCR) | Unchanged proposal |
| Product localization / crop similarity | Grounding DINO tiny / DINOv2 small | Unchanged proposal |
| Cheaper alternative | `gpt-6-luna` | Use only if a stage shows equal behaviour on recorded cases at lower cost; don't assume it |

**OpenAI facts** (from the [model catalog](https://developers.openai.com/api/docs/models), checked 2026-09-26):
- All current flagship models accept text and image input and are served through the Responses API.
- `gpt-6-sol`: $2 per million input tokens, $10 per million output; reasoning effort from none to max.
- `gpt-6-luna`: $0.10 / $0.50.
- `gpt-6-astra`: $10 / $50. Not needed for these bounded tasks.
- Structured output: see [OpenAI's structured output guide](https://developers.openai.com/api/docs/guides/structured-outputs).

**Gemini image facts:**
- Flash Image supports image output and editing, but not structured output or function calling. [Model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image)
- The listed 1K image-output price is about $0.067; Lite's is $0.0336. There is no free tier for either model. [Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- The image guide favours Flash for reference consistency. [Image guide](https://ai.google.dev/gemini-api/docs/image-generation)

**Other tools:**
- PP-OCRv5 documentation still shows errors on artistic text. [PaddleOCR](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html)
- Neither Grounding DINO nor DINOv2 documentation establishes an identity threshold for our images. [Grounding DINO](https://huggingface.co/docs/transformers/en/model_doc/grounding-dino), [DINOv2](https://huggingface.co/docs/transformers/en/model_doc/dinov2)

## 3. Spending

Garmit asked for a credit recommendation: **about $10 Gemini + $10 OpenAI**. Purchase status is unconfirmed. Paid runs still need an explicit estimate and approval.

Illustrative arithmetic, not a measured usage profile:

| Item | Calls | Estimate |
|---|---:|---:|
| Gemini images: smoke 1 + dev ~6 + held-out ~20 + reserve ≤20 | ≤47 | ≤ ~$3.15 image output, plus input/thinking |
| OpenAI generation stages (~3k in / ~1k out each at `gpt-6-sol` rates ≈ $0.016) × ≤6 per request × ~27 requests | ≤ ~160 | ≤ ~$2.60 |
| OpenAI evaluator judge calls, including repeats | ~200 | ~$3 |

Reasoning tokens bill as output and can dominate. Measure them in the probe and update these figures before bulk runs. Actual prices are recorded per call in the state store.

## 4. Compatibility probe (after keys and a small approved spend)

1. Pin SDK versions (`google-genai`, `openai`). Verify that the model IDs are available on each account.
2. One structured `gpt-6-sol` vision call on a reference image. Check schema adherence, token and reasoning usage, and how unknown fields are handled.
3. One planner call and one reviewer call on a fixed request.
4. One `gemini-3.1-flash-image` call at 1:1/1K. Check the returned dimensions, final image count, latency and usage.
5. Record everything in the state store. A rejected parameter is an integration failure, not a reason to swap models silently.

## 5. Source-bank assertions not adopted as verified facts

- The old non-square dimension table is unverified here. v1 accepts square only and inspects real pixels.
- "CPU is fine for 150 images", "DINOv2 proves identity" and "OCR package X is best for these ads" need measurement.
- Cross-family judging reduces one possible source of bias. It does not validate a judge; human-labelled calibration does.
- The historical prior-art list was not fully source-audited. Reopen the original papers before citing them.
