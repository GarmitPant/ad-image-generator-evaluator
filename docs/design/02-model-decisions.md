# Model choices and source audit

Researched 2026-09-26. Capability statements below are documentation-backed; task suitability is a recommendation awaiting a pilot. No model was benchmarked or called for inference in this design session.

## 1. Recommended division of work

v0.2 priority update: generation is a functional baseline; evaluation is the main engineering deliverable. User-confirmed Exact/Extract modes supersede the old whole-input-verbatim assumption. Models below are options, not a requirement to install every component before seeing a working evaluator.

| Responsibility | Initial choice | Why this choice | What would change it |
|---|---|---|---|
| Architecture/specification in this chat | GPT-6 Astra with high reasoning effort; increase effort for difficult reviews | Quality-first reasoning choice, outside the runtime pipeline | User's selected model and available limits |
| Product reference analysis | `gemini-3.8-flash`, structured vision input | One Google integration; extract visible facts once per reference | Missed distinguishing features on reviewed pilot photos |
| Extract-mode content selection | `gemini-3.8-flash`, structured call | Select source-backed relevant text and protected phrases; no visual art direction | Semantic selection failures on independently labelled plans |
| Aesthetic planning | Code templates initially | Sufficient for functional generation; prioritize evaluator effort | Add a creative model only after evaluator validation |
| Image generation and repair | `gemini-3.1-flash-image` | Organizer-allowed; reference-driven generation/editing | An evidence-backed comparison favors allowed Lite for an explicit mode |
| Exact-mode content | **No model** | Entire source is binding, subject to render-capacity validation | User explicitly switches to Extract |
| Final prompt assembly, validation, routing | **Python code** | No ambiguity about exact obligations; repeatable hashes | No current reason to add a model |
| Headline/label OCR | PP-OCRv5 via PaddleOCR | Local text boxes and recognition evidence | Installation/latency failure: explicitly switch to EasyOCR and recalibrate |
| Product localization | `IDEA-Research/grounding-dino-tiny` | Proposed baseline consistent with Garmit's experience | Pilot shows unacceptable misses or hardware cost |
| Crop similarity | `facebook/dinov2-small` | Low-complexity embedding baseline; compare original vs output crop | Same-category swaps pass too often; use stronger attribute checks before adding more embeddings |
| Semantic selection / visual judge | `claude-sonnet-5`, separate prompts | Independent evidence for source→copy meaning and image-level product/context criteria | Human-labelled calibration favors another judge within latency/budget |
| Judge research comparator | `claude-opus-5-5` on a small fixed calibration subset only | Tests whether a larger model fixes relevant mistakes | Skip unless basic pipeline and labels are complete |

OpenAI describes Astra as its most capable model for complex reasoning/research. “Use high effort for this design” is our workflow recommendation, not a measured optimum. The assistant has not changed the current chat's model selection. [Official model page](https://developers.openai.com/api/docs/models/gpt-6-astra)

Gemini 3.8 Flash accepts images and supports structured output; its documented thinking options are low/medium/high, not minimal. Proposed settings: low for reference analysis, medium for source-content selection; pin and record them. These differ from the image model's settings. [Google model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)

Flash Image supports image output and editing but not structured JSON output or function calling. Keep schema-based analysis/planning in the text/vision model. [Flash Image model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image)

The image guide favors Flash for reference consistency and warns that Lite is not optimized for multiple references or sequential editing; Lite's own page nevertheless describes local edit support. This is a suitability distinction, not a claim that Lite cannot edit. Use Flash initially, defer Lite comparison. The guide documents minimal/high thinking and linked edits through `previous_interaction_id`. [Image guide](https://ai.google.dev/gemini-api/docs/image-generation), [Lite model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-image)

Anthropic lists vision support for its current models. Sonnet 5 costs $2/M input and $10/M output; Opus 5.5 costs $4/M input and $20/M output. That supports a modest calibration comparison, not an assertion that either is a validated judge. [Anthropic model overview](https://platform.claude.com/docs/en/models/overview)

Claude's current JSON-output field is `output_config.format`; strict tool output is another option. Validate the installed SDK/model combination with one approved pilot call. Schema adherence does not establish visual correctness. [Structured output documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

PP-OCRv5 includes scene-text detection/recognition; its documented evaluations still show errors on artistic text. Do not interpret an OCR result as perfect transcription. [PaddleOCR documentation](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html)

Grounding DINO performs text-conditioned detection; DINOv2 supplies visual features. Neither documentation establishes a universally valid product-identity threshold for our images. [Grounding DINO documentation](https://huggingface.co/docs/transformers/en/model_doc/grounding-dino), [DINOv2 documentation](https://huggingface.co/docs/transformers/en/model_doc/dinov2)

## 2. Distinct responsibilities, minimal generation

Exact mode prepares copy in code. Extract mode makes one structured selection call; the result cites original source spans and preserves explicitly protected phrases. Both freeze TextPlan before rendering. There is no unconstrained copywriter or model that uses raw freeform prose as visual art direction.

A cached reference analyzer can describe product facts. A deterministic registry resolves geography/season and a template compiles the final image prompt. Separate responsibilities do not require separate vendors or agents. Dedicated creative planning, multiple candidates and repair are deferred.

The source-selection evaluator sees original input and chosen spans, and checks omitted qualifiers/negations/relevance independently. The rendering evaluator transcribes pixels without seeing expected text, then compares the transcript to TextPlan in code. A visual judge checks product/context evidence. Keep these prompts and evidence separable even when one judge model serves multiple roles.

Google-to-Claude separation is a provisional independence choice, not proof of reliable judgments. Validate judges against human labels; do not choose them solely because they are larger or cross-family. Use a stronger model on a fixed calibration subset only when there are concrete failure cases to investigate.

## 3. Initial spending proposal — not approved

Google lists no free API generation tier for the two allowed image models. Flash's listed 1K image-output price is approximately $0.067; Lite's is $0.0336. Input, textual/thinking output and any extra services are additional. Enable Gemini billing before the smoke test. [Google pricing](https://ai.google.dev/gemini-api/docs/pricing)

Revised baseline image-output arithmetic using the rounded Flash list figure:

| Work | Image calls | Image-output subtotal |
|---|---:|---:|
| Compatibility smoke | 1 | ~$0.07 |
| Six development requests, one image each | 6 | ~$0.40 |
| Twenty held-out requests, one image each | 20 | ~$1.34 |
| Additional genuine failure fixtures / development reserve | ≤20 | ≤$1.34 |
| Sum of these caps | ≤47 | ≤$3.15 |

These are image-output subtotals, not hard billing caps; image inputs, reasoning/text outputs, selection and evaluation are extra. With generation simplified, prioritize the remaining budget for genuine evaluator observations, difficult cases and independent judge repeats. No image-repair or Lite-ablation spend is part of this baseline.

For a judge-call illustration, 4,000 input tokens and 600 output tokens at Sonnet's listed rates cost $0.014; 200 such calls cost $2.80. This assumption is not a measured usage profile and excludes extra thinking/output usage. Reference/planner costs must be estimated from their actual selected settings and usage; do not assume free-tier quota or negligible thinking costs.

Propose an initial **$15 total application budget**, with an optional later increase only after seeing actual usage. This is a planning envelope, not a spend instruction. Start with a separately approved small smoke/pilot estimate, then update remaining-budget projections before any bulk run. Provider account funding minimums may differ.

## 4. Compatibility probe the implementation agent must run

After Garmit enables billing and authorizes the concrete pilot spend:

1. Verify model IDs on the account and pin installed SDK versions.
2. Extract one product profile with structured output; test empty/uncertain facts handling.
3. Prepare one Exact request and one Extract TextPlan offline/with an approved selection call; prove protected coverage and selected-copy preservation.
4. Generate one Flash square 1K image; measure returned dimensions, final block count, latency and usage.
5. Keep edit/repair probing deferred; test OCR and source-to-copy observations on the baseline image/plan instead.
6. Test one structured judge response once evaluator integration is ready.

Do not call SDK snippets in the old context “tested” until these steps actually pass. Record model availability, endpoint/API surface, SDK versions and unsupported features. A rejected parameter is an integration failure, not a reason to replace the required model silently.

## 5. Source-bank assertions not adopted as verified facts

- The old non-square dimension table was not reproduced in the fetched current guide. Its exact values remain unverified here; v1 accepts square only and inspects real pixels.
- The guide and model pages contain differently worded thinking descriptions. Use the documented, smoke-tested configuration; do not claim reasoning can be disabled on this basis.
- Broad statements that “CPU is fine for 150 images,” that DINOv2 proves identity, or that one OCR package is best for these ads require measurements on the actual machine/data.
- No automatic superiority claim is made for cross-family judges. Independent families reduce one possible source of correlation; human-labelled calibration is still required.
- The original literature/prior-art list was read but not exhaustively source-audited in this iteration. Do not reuse its precise empirical claims or citations in a final submission without opening and checking the original papers.

All primary-source links above were opened during this iteration. Model/pricing facts should be rechecked if implementation moves beyond the event date.
