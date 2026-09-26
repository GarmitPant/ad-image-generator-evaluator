# 04 — Prior art and references

Researched 2026-09-26. Each entry gives the link, what it is, and **what to take from it**. Star
counts and paper claims are as reported by the source. Nothing here was run or reproduced.

---

## A. Official Google material (read first)

| Resource | What it is | Take |
|---|---|---|
| [Gemini image generation guide](https://ai.google.dev/gemini-api/docs/image-generation) | Official docs for the Nano Banana models (now written for the Interactions API) | Prompt templates (product mockup, accurate text, detail preservation, multi-image composition), the 1K dimension table, the limitations list (text-first advice, best languages) |
| [Gemini 3.1 Flash Image model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image) / [Flash-Lite Image](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-image) | Capabilities and limits | No structured output or function calling on image models; thinking cannot be disabled |
| [How to prompt Gemini 2.5 Flash Image](https://developers.googleblog.com/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/) (Google Developers Blog) | Earlier prompting guide with fill-in templates | The text-in-image and product-photography templates, quoted in `03` §2 |
| [intro_gemini_3_1_flash_image_gen.ipynb](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/getting-started/intro_gemini_3_1_flash_image_gen.ipynb) | Official notebook for this exact model | `ImageConfig(aspect_ratio, image_size)` usage, editing examples |
| [creative_content_generation.ipynb](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/use-cases/marketing/creative_content_generation.ipynb) | Google's marketing use-case notebook (Gemini + Imagen) | How Google frames ad-creative generation |
| [Gecko on Vertex AI](https://cloud.google.com/blog/products/ai-machine-learning/evaluate-your-gen-media-models-on-vertex-ai) | Google's rubric-based, interpretable autorater for image/video generation (`RubricMetric.GECKO_TEXT2IMAGE`) | Evidence that **rubric → atomic questions → VLM answers** is how Google itself evaluates gen-media. Our context checklist is the same shape, compiled from typed context instead of a free prompt |

---

## B. Open-source ad-generation systems

| Project | What it does | Take / contrast |
|---|---|---|
| [google-marketing-solutions/adios](https://github.com/google-marketing-solutions/adios) | Google Ads image-asset manager: ad-group context → Gemini-written prompts → Imagen images; manual review UI; v1.1 added automatic Gemini-based **policy** validation | Context-to-prompt at scale, with a validation gate. Their gate checks policy, not product fidelity or text accuracy. That gap is exactly what our evaluator fills |
| [google-marketing-solutions/gen-v](https://github.com/google-marketing-solutions/gen-v) | Product images → Gemini analyses them and writes prompts → video ads | "Analyse the product image first, then generate" = our reference-analysis step |
| [motiful/product-shots](https://github.com/motiful/product-shots) (~79★) | Claude Code skills turning one product photo into e-commerce visuals incl. ad creatives, using Nano Banana | Prompt patterns for product preservation; an example of skills-as-pipeline. No evaluator |
| [n8n: e-commerce ad creative with Nano Banana](https://n8n.io/workflows/8226-generate-unlimited-e-commerce-ad-creative-with-nano-banana-image-generator/) | No-code workflow: product image + prompts → ad images | The typical approach: generation with no quality gate. Useful as the "what most people build" contrast |
| [browser-use ad-use example](https://docs.browser-use.com/open-source/examples/apps/ad-use) | Agent browses a landing page, then generates an ad image | Context gathered by an agent rather than typed fields. The opposite design choice to ours |

---

## C. Research on product and ad image generation

| Paper | Key point | Take |
|---|---|---|
| **SimplePoster** (CVPR 2026) — [arXiv 2605.08784](https://arxiv.org/html/2605.08784v2) | Product poster generation. Evaluates **product preservation** with a human-judged **Subject Preservation Rate** (structure, texture, colour, branding kept) and **text** with **Sentence Accuracy (exact line match)** and **Normalized Edit Distance**. Baselines include **Gemini 2.5 Flash**, PosterMaker, FLUX-Kontext, SeedEdit 3.0 | The Sen.Acc + NED pair for our text metric. SPR's definition (structure, texture, colour, branding) is a ready-made rubric for our product metric and for Garmit's hand labels |
| **PosterMaker** (CVPR 2025) | Product posters with accurate text rendering | A named baseline in this area; cite if discussing text rendering |
| **PAID: Product-Centric Advertising Image Design** — [arXiv 2501.14316](https://arxiv.org/html/2501.14316v2) | Four stages: prompt generation → layout → background generation → **graphics rendering** (text drawn as graphics, not by the image model). Metrics: FID, CLIP-T/I, fore-/background matching, mIoU/AP | **Precedent for the text-overlay fallback**: serious ad systems separate text rendering from image generation. Cite it when defending the fallback |
| **CTR-Driven Advertising Image Generation with MLLMs** (WWW 2025) — [arXiv 2502.06823](https://arxiv.org/html/2502.06823v1) | Optimises generated ad images for click-through rate while preserving product integrity | "Ad effectiveness" is a fourth dimension beyond our three. Out of scope; mention in future work |
| **Personalized Advertising Image and Text Generation** — [arXiv 2605.12138](https://arxiv.org/html/2605.12138v1) | PAd1M dataset; a **Product Background Similarity** metric | Another product-vs-background metric idea |
| **AutoPP** (AAAI) — [PDF](https://ojs.aaai.org/index.php/AAAI/article/download/37377/41339) | Automated product poster generation and optimisation | Related-work citation |

---

## D. Evaluation methods

| Method | Key point | Take |
|---|---|---|
| **DreamBooth** — [arXiv 2208.12242](https://arxiv.org/html/2208.12242v2) | Introduced the **DINO** subject-fidelity metric. CLIP-I rewards "same kind of object"; DINO tracks identity better (Pearson 0.32 vs 0.27 with human preference, as reported) | **DINOv2 crop similarity is the primary product-fidelity signal**; CLIP/SigLIP secondary |
| **DreamSim** (NeurIPS 2023) — [PDF](https://proceedings.neurips.cc/paper_files/paper/2023/file/9f09f316a3eaf59d9ced5ffaefe97e0f-Paper-Conference.pdf) | Learned perceptual similarity from CLIP/DINO ensembles, tuned to human judgments | Alternative or extra fidelity signal if DINOv2 separates poorly |
| **TIFA** — [arXiv 2303.11897](https://www.alphaxiv.org/abs/2303.11897) | Text-to-image faithfulness via question generation + VQA | Foundation for question-based context adherence |
| **Davidsonian Scene Graph (DSG)** (ICLR 2024) — [arXiv 2310.18235](https://arxiv.org/html/2310.18235v3), [code](https://github.com/j-min/DSG) | Atomic, unique questions in a **dependency graph**; don't score "is it red?" if the object is absent | Our checklist's Q0 gate: skip dependent questions when the product is not visible |
| **VQAScore / GenAI-Bench** | Score = P("Yes") to "Does this figure show {text}?"; beats CLIPScore on alignment benchmarks | A softer score if the judge exposes token probabilities; otherwise binary answers |
| **Gecko** — [arXiv 2404.16820](https://arxiv.org/html/2404.16820v1) | Skills-based benchmark plus an interpretable rubric autorater (Google DeepMind) | Same as A; cite as the research basis |
| **TextInVision** — [arXiv 2503.13730](https://arxiv.org/html/2503.13730v1) | OCR + edit-distance scoring with an **algorithm that locates the expected text inside noisy OCR output** (substring → word matching → edit distance on the remainder); also shows human "text accuracy" worsens as edit distance grows | **Use its alignment algorithm** in the text metric |
| **TextDiffuser / MARIO-Eval** (NeurIPS 2023) — [project](https://jingyechen.github.io/textdiffuser/) | Text-rendering benchmark with OCR-based metrics | Related-work citation for text metrics |
| **MLLM-as-a-Judge** — [site](https://mllm-judge.github.io/) (arXiv 2402.04788) | Multimodal judges agree with humans in **pairwise** comparisons but diverge in **scoring** and batch ranking; show biases and inconsistency | Ask **atomic yes/no** questions, not "rate 1–10". Report agreement with humans instead of trusting the judge |
| **MLLM-as-a-Judge Exhibits Model Preference Bias** — [arXiv 2604.11589](https://arxiv.org/html/2604.11589v1) | Across 12 MLLMs and 1.29M caption-score pairs, judges tend to prefer their own outputs | **Use a judge from a different family than the generator** |
| **A survey on LLM-as-a-judge** — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2666675825004564) | Self-enhancement bias ("avoid using the same model as the evaluator"); **cultural bias** in judges | Supports the cross-family judge; cultural bias is a limitation to state for the geography checks |
| **G-Eval** (in resume-workbench: `docs/interview-prep/g-eval.md`) | Rubric judge with auto chain-of-thought and probability-weighted scores | Garmit already knows it; useful for interview discussion of judge scoring |

---

## E. Geography and cultural representation

| Paper | Take |
|---|---|
| **DIG In** (TMLR 2023) — geographic disparities in image generation | Models render some regions stereotypically. Justifies the registry's `avoid` list and the inverse checklist questions |
| **GeoDiv** — [arXiv 2602.22120](https://arxiv.org/html/2602.22120v1) | A framework for measuring geographic diversity in text-to-image output. Related work |
| **Inspecting the Geographical Representativeness of Images from Text-to-Image Models** (Basu et al.) | Related work |
| **Towards Geographic Inclusion in the Evaluation of Text-to-Image Models** (FAccT 2024) — [ACM](https://dl.acm.org/doi/fullHtml/10.1145/3630106.3658927) | Humans in different regions judge "looks like my region" differently. A limitation of any single-judge geography check, ours included |

---

## F. Tooling references

| Resource | Take |
|---|---|
| [HF Grounding DINO docs](https://huggingface.co/docs/transformers/en/model_doc/grounding-dino) | Exact `AutoModelForZeroShotObjectDetection` + `post_process_grounded_object_detection` usage; MM-Grounding-DINO as a stronger alternative |
| [8 open-source OCR models compared (Modal)](https://modal.com/blog/8-top-open-source-ocr-models-compared) / [Open-source OCR 2026 (Unstract)](https://unstract.com/blog/best-opensource-ocr-tools/) | PaddleOCR is the most accurate classic engine but heavier; EasyOCR is the easiest; Tesseract is weak on stylised/scene text. Ad text is scene-like, so avoid Tesseract |
| [OpenRouter unified Image API](https://openrouter.ai/blog/announcements/image-api/) (2026-06-23) and [guide](https://openrouter.ai/docs/guides/overview/multimodal/image-generation) | One request shape across 30+ image models (`resolution`, `aspect_ratio`, `input_references`). Useful for judge or model comparisons; keep Gemini generation on the Google SDK |

---

## G. What most submissions will do, and what this design does instead

| Typical submission | This design |
|---|---|
| Concatenate the three fields into one prompt | Typed request → market registry → creative brief. **The same brief drives the prompt and the evaluator checklist** |
| Ask one vision model to "rate this ad 1–10" | Deterministic metrics (OCR+NED, detection+DINOv2+ΔE) where possible; atomic yes/no checklist only for context; **composition in code** |
| Gemini judges Gemini's images | Cross-family judge, plus OCR and the detector cross-checking the judge's claims |
| Evaluator runs after generation as a report | Evaluator **inside** the loop: best-of-N plus targeted edit repair |
| Tests call the live API (flaky, costs money) | Offline tests over committed images and recorded judge responses |
| "The evaluator works" is asserted | Constructed negatives per metric, human labels, agreement + kappa + flip rate, counts reported |
| 16:9 at "1K" silently ships 1376 px | Resolution guard + test; the 1:1 default is explained |
| "Structured context improves output" is assumed | **Measured**: enriched-brief vs raw-fields ablation |
