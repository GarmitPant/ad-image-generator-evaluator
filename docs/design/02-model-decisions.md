# Model choices and source audit

Researched 2026-09-26. Capability statements below are documentation-backed; task suitability is a recommendation awaiting a pilot. No model was benchmarked or called for inference in this design session.

## 1. Recommended division of work

| Responsibility | Initial choice | Why this choice | What would change it |
|---|---|---|---|
| Architecture/specification in this chat | GPT-6 Astra with high reasoning effort; increase effort for difficult reviews | Quality-first reasoning choice, outside the runtime pipeline | User's selected model and available limits |
| Product reference analysis | `gemini-3.8-flash`, structured vision input | One Google integration; extract visible facts once per reference | Missed distinguishing features on reviewed pilot photos |
| Ad planning and typography plan | `gemini-3.8-flash`, separate structured call | Distinct responsibility, same client; choose compatible cues/layouts without rewriting copy | Invalid-plan frequency or human review shows weak composition |
| Image generation and repair | `gemini-3.1-flash-image` | Organizer-allowed; reference-driven generation/editing | An evidence-backed comparison favors allowed Lite for an explicit mode |
| Exact headline content | **No model** | User already supplied the required string | A future separate creative-brief input and approved copywriter workflow |
| Final prompt assembly, validation, routing | **Python code** | No ambiguity about exact obligations; repeatable hashes | No current reason to add a model |
| Headline/label OCR | PP-OCRv5 via PaddleOCR | Local text boxes and recognition evidence | Installation/latency failure: explicitly switch to EasyOCR and recalibrate |
| Product localization | `IDEA-Research/grounding-dino-tiny` | Proposed baseline consistent with Garmit's experience | Pilot shows unacceptable misses or hardware cost |
| Crop similarity | `facebook/dinov2-small` | Low-complexity embedding baseline; compare original vs output crop | Same-category swaps pass too often; use stronger attribute checks before adding more embeddings |
| Context judge | `claude-sonnet-5` | Separate family from image generator and planner; schema-constrained observations | Human-labelled calibration favors another judge within latency/budget |
| Judge research comparator | `claude-opus-5-5` on a small fixed calibration subset only | Tests whether a larger model fixes relevant mistakes | Skip unless basic pipeline and labels are complete |

OpenAI describes Astra as its most capable model for complex reasoning/research. “Use high effort for this design” is our workflow recommendation, not a measured optimum. The assistant has not changed the current chat's model selection. [Official model page](https://developers.openai.com/api/docs/models/gpt-6-astra)

Gemini 3.8 Flash accepts images and supports structured output; its documented thinking options are low/medium/high, not minimal. Proposed settings: low for reference extraction, medium for planning; pin and record them. These differ from the image model's settings. [Google model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)

Flash Image supports image output and editing but not structured JSON output or function calling. Keep schema-based analysis/planning in the text/vision model. [Flash Image model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image)

The image guide favors Flash for reference consistency and warns that Lite is not optimized for multiple references or sequential editing; Lite's own page nevertheless describes local edit support. This is a suitability distinction, not a claim that Lite cannot edit. Use Flash initially, defer Lite comparison. The guide documents minimal/high thinking and linked edits through `previous_interaction_id`. [Image guide](https://ai.google.dev/gemini-api/docs/image-generation), [Lite model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-image)

Anthropic lists vision support for its current models. Sonnet 5 costs $2/M input and $10/M output; Opus 5.5 costs $4/M input and $20/M output. That supports a modest calibration comparison, not an assertion that either is a validated judge. [Anthropic model overview](https://platform.claude.com/docs/en/models/overview)

Claude's current JSON-output field is `output_config.format`; strict tool output is another option. Validate the installed SDK/model combination with one approved pilot call. Schema adherence does not establish visual correctness. [Structured output documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

PP-OCRv5 includes scene-text detection/recognition; its documented evaluations still show errors on artistic text. Do not interpret an OCR result as perfect transcription. [PaddleOCR documentation](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html)

Grounding DINO performs text-conditioned detection; DINOv2 supplies visual features. Neither documentation establishes a universally valid product-identity threshold for our images. [Grounding DINO documentation](https://huggingface.co/docs/transformers/en/model_doc/grounding-dino), [DINOv2 documentation](https://huggingface.co/docs/transformers/en/model_doc/dinov2)

## 2. Why separate tasks do not require separate model families

Use distinct prompts and schemas for the reference analyst and planner. The analyst describes only observable product facts; the planner chooses a compatible creative arrangement using those facts and the context inventory. Caching the former saves repeated work across campaigns. Running the planner per request permits different scenes for the same product.

A third copywriting model would be actively risky under this problem statement: the freeform text is required output content. A prompt-writing model is also unnecessary initially because validated structured plans can compile into detailed prompts in code. The separation we want is between responsibilities and contracts, not as many model calls as possible.

Do not put a frontier reasoning model into every runtime stage merely because we want excellent architecture. Model quality is task-dependent; preprocessing and clear contracts may matter more than an extra large-model call. Use a stronger planner only after specific pilot failures justify the integration cost.

Do not enable browsing/search grounding during generation in v1. A reviewed context inventory makes the request reproducible and keeps model comparisons interpretable. The separate research/design workflow can use external sources to improve that inventory.

## 3. Initial spending proposal — not approved

Google lists no free API generation tier for the two allowed image models. Flash's listed 1K image-output price is approximately $0.067; Lite's is $0.0336. Input, textual/thinking output and any extra services are additional. Enable Gemini billing before the smoke test. [Google pricing](https://ai.google.dev/gemini-api/docs/pricing)

Image-output planning arithmetic using the rounded Flash list figure:

| Work | Image calls | Image-output subtotal |
|---|---:|---:|
| First compatibility smoke | 1 | ~$0.07 |
| Four pilot requests, up to 3 calls each | ≤12 | ≤$0.81 |
| Twenty final requests, up to 3 calls each | ≤60 | ≤$4.02 |
| Twenty raw-context comparisons, 2 candidates each | ≤40 | ≤$2.68 |
| Development reserve | ≤20 | ≤$1.34 |
| Sum of these caps | ≤133 | ≤$8.92 |

These are image-output subtotals, **not hard total billing caps**. Exact token accounting may differ from rounded per-image equivalents. Repairs consume image calls too. No Flash-Lite ablation is needed within six hours.

For a judge-call illustration, 4,000 input tokens and 600 output tokens at Sonnet's listed rates cost $0.014; 200 such calls cost $2.80. This assumption is not a measured usage profile and excludes extra thinking/output usage. Reference/planner costs must be estimated from their actual selected settings and usage; do not assume free-tier quota or negligible thinking costs.

Propose an initial **$15 total application budget**, with an optional later increase only after seeing actual usage. This is a planning envelope, not a spend instruction. Start with a separately approved small smoke/pilot estimate, then update remaining-budget projections before any bulk run. Provider account funding minimums may differ.

## 4. Compatibility probe the implementation agent must run

After Garmit enables billing and authorizes the concrete pilot spend:

1. Verify model IDs on the account and pin installed SDK versions.
2. Extract one product profile with structured output; test empty/uncertain facts handling.
3. Plan one ad; prove exact headline survives validation and compilation.
4. Generate one Flash square 1K image; measure returned dimensions, final block count, latency and usage.
5. If repair is in scope and separately budgeted, perform one linked edit; reassert output settings and inspect product/text/context changes.
6. Test one structured judge response once evaluator integration is ready.

Do not call SDK snippets in the old context “tested” until these steps actually pass. Record model availability, endpoint/API surface, SDK versions and unsupported features. A rejected parameter is an integration failure, not a reason to replace the required model silently.

## 5. Source-bank assertions not adopted as verified facts

- The old non-square dimension table was not reproduced in the fetched current guide. Its exact values remain unverified here; v1 accepts square only and inspects real pixels.
- The guide and model pages contain differently worded thinking descriptions. Use the documented, smoke-tested configuration; do not claim reasoning can be disabled on this basis.
- Broad statements that “CPU is fine for 150 images,” that DINOv2 proves identity, or that one OCR package is best for these ads require measurements on the actual machine/data.
- No automatic superiority claim is made for cross-family judges. Independent families reduce one possible source of correlation; human-labelled calibration is still required.
- The original literature/prior-art list was read but not exhaustively source-audited in this iteration. Do not reuse its precise empirical claims or citations in a final submission without opening and checking the original papers.

All primary-source links above were opened during this iteration. Model/pricing facts should be rechecked if implementation moves beyond the event date.
