# 01 — Problem statement

Two versions follow: the organizers' text exactly as issued, then the problem restated as
a definition an implementing agent can work from. Where they differ, the organizers' text wins
and the difference is listed under "Assumptions" so it can be checked.

---

## 1. Organizers' text (G2 AI Hiring Hackathon, Problem statement 2)

> **Theme:** Multimodal AI: Images
> **Problem statement name:** Enrichment of image generation using structured context
>
> **Overview.** Consider an image generation pipeline which depends on structured context to
> refine the outputs. How would you guarantee that generation quality is achieved in the
> generation process?
>
> *Note: This exercise requires an API key for accessing Gemini models. You can request a free
> API key for yourself at https://aistudio.google.com/*
>
> **Tech stack:** Python, Typescript, or Ruby preferred
>
> **Task**
> 1. Propose an image generation pipeline for display advertisement generation that uses
>    Gemini 3.1 Flash-Lite Image or Gemini 3.1 Flash Image. The pipeline should take a reference
>    product image plus three structured text fields (target geography, season, and freeform
>    text that must be included in the generated image) as input. This added context leads to
>    refinement of the generated image. *Note: Text rendering may not reliably be perfect; this
>    is acceptable, but consider this in your solution.*
> 2. Decide an effective generation strategy for images generated using this pipeline, then
>    implement the generation pipeline. The maximum resolution of generated images must be 1K
>    (long edge ≤1024px).
> 3. Implement an evaluator that judges the quality of the outputs across ≈20 images output from
>    the pipeline.
> 4. Demonstrate that your evaluator can identify passing and failing outputs against quality
>    metrics you define through automated tests. At a minimum, consider 1) context adherence,
>    2) fidelity of reference product, and 3) text rendering fidelity.
>
> **Restrictions:** A coding agent may be used, but you must explain how you collaborated with
> (prompted) the agent to arrive at your solution.
>
> **Submission format**
> - Details about your solution, including an explanation of your engineering design, your
>   rationale for it, definition of success criteria for your solution, level of achievement
>   against your criteria, and any limitations of your solution, in a Markdown or PDF file
> - Disclosure of coding agent use: you must disclose the use of coding agents in developing
>   your project. Where used, you must explain how you directed the agent to arrive at the
>   outputs it generated. This may be achieved by sharing documentation of the architectural
>   requirements you supplied to the agent, or by providing summarized traces of your
>   interactions with the agent.
> - GitHub/GitLab for code commit containing your solution, as well as your golden dataset and
>   tests

---

## 2. Constraints added by Garmit (2026-09-26)

| Constraint | Detail |
|---|---|
| Language | **Python** |
| Input must be structured | **Target geography and season are strongly typed.** Not free strings. |
| System parts | (1) image generation pipeline, (2) automated evaluator |
| UI | **Later.** Added after the pipeline and evaluator work. Must sit on top of the same pipeline API, not beside it |
| Models | **No restriction** beyond the organizers' requirement that generation uses Gemini 3.1 Flash Image or Flash-Lite Image. Other models (judges, OCR, detectors, embeddings) are open. See `03-models-apis-and-budget.md` for what his subscriptions do and do not cover |
| Repository | A **new** git repository, separate from resume-workbench |
| Submission | Markdown or PDF write-up (design, rationale, success criteria, results, limitations), coding-agent disclosure, repo with solution + golden dataset + tests |

---

## 3. The problem, defined for an implementing agent

### Goal
Build a Python system that turns **one product photo plus a typed context** into a
**display-advertisement image**, and a separate **evaluator** that decides, per image and per
quality dimension, whether the output passes. Then prove the evaluator works with automated
tests that show it passes good outputs and fails bad ones.

The organizers' framing question — *"how would you guarantee generation quality is achieved in
the generation process?"* — means the evaluator should not only grade after the fact. It should
sit **inside** the pipeline: generate candidates, evaluate them, keep the best, retry the ones that
fail with targeted fixes, and label anything that still fails honestly.

### Inputs (one ad request)

| Field | Type | Notes |
|---|---|---|
| `product_image` | image file (PNG/JPEG/WebP) | The reference product. Its identity must survive into the ad |
| `geography` | **enum**, ISO 3166-1 alpha-2 country from a supported-markets registry | Not a free string. Each supported market carries a data profile (hemisphere, climate, languages, visual cues) |
| `season` | **enum**: `spring`, `summer`, `autumn`, `winter` | The season *as experienced in that market*. Winter in Australia is June–August |
| `ad_text` | constrained string | Must appear in the image **verbatim**. Length-limited, validated |

Optional fields the design may add, clearly marked as extensions: aspect ratio / ad format,
text language tag, product display name.

### Outputs (per request)
- One or more candidate ad images, each **≤1024 px on the long edge**
- For each candidate, an evaluation record: per-metric score, pass/fail, the threshold used, the
  evidence (OCR text, detection box, similarity values, judge answers), and a terminal state
  (`ok` / `degraded` / `failed`)
- The selected image and why it was selected, or a clear "no passing candidate" result

### Deliverables
1. Generation pipeline (Python package + CLI)
2. Evaluator (Python package, usable standalone on any image + request)
3. Golden dataset: ~20 requests, their generated images, human pass/fail labels, and a set of
   deliberately constructed failing examples
4. Automated tests (pytest), runnable offline without API keys
5. Write-up (Markdown): design, rationale, success criteria, results against them, limitations
6. Coding-agent disclosure: the specs given to the agent plus a summarized interaction log
7. Later: a thin UI over the same pipeline

### Minimum quality dimensions
1. **Context adherence** — the image reflects the geography and the season, and nothing
   contradicts them
2. **Product fidelity** — the product in the ad is recognisably the reference product (shape,
   colour, logo/label), not a lookalike
3. **Text rendering fidelity** — the required text appears, spelled exactly, legible, and
   without extra invented text

### Non-goals
- Training or fine-tuning any model
- Using Gemini 3 Pro Image ("Nano Banana Pro") for generation. It exists but the problem
  names only the 3.1 Flash and Flash-Lite image models
- Production hosting, auth, multi-user state
- Brand-guideline enforcement (logo placement rules, legal disclaimers), unless time remains

### Definition of done
- `pytest` passes offline from a clean clone, with no API keys set
- The ~20 golden images are committed, each with an evaluation record and a human label
- For each of the three metrics, the tests show the evaluator **failing the constructed bad
  examples on that metric** and **passing the good ones**
- The write-up states success criteria *before* results, and reports results against them
  honestly, including counts, not only percentages
- Every generated image in the repo is ≤1024 px on its long edge, checked by a test

---

## 4. Assumptions (to confirm with organizers; defaults apply if unanswered)

These are the defaults the design uses. Each one changes the build if the answer differs.

| # | Question | Default |
|---|---|---|
| 1 | May the required text be drawn onto the image in code as a fallback when the model misspells it? | Model renders text first. A code overlay is a **labelled fallback only**, and results report both rates separately |
| 2 | What does product fidelity mean: exact identity, or the same kind of product? | Same product: shape, colour and logo/label must match. Angle, scale and lighting may change |
| 3 | Who supplies the reference product images? | We source our own (ideally photographed ourselves), with source and licence noted per image |
| 4 | What does geography change? Is the text translated? | Geography changes the **scene** only. Text stays **verbatim**, never translated |
| 5 | Is season hemisphere-aware? Are holidays in scope? | Hemisphere-aware weather seasons. Holidays are an extension, not in scope |
| 6 | May we construct known-bad images to test the evaluator? | Yes: real pipeline outputs labelled by hand **plus** constructed failures |
| 7 | Who decides pass/fail? | We define thresholds and hand-label the golden set, then report agreement |
| 8 | May the evaluator use non-Gemini models? | Yes. Deterministic checks and local models where possible; a vision-language judge from a different model family than the generator for context adherence |
| 9 | Evaluator inside the pipeline, or after? | Inside: best-of-N plus targeted retry, bounded at 3 attempts per request |
| 10 | API credits? Flash vs Flash-Lite? | We pay. Generate with Flash; compare Flash-Lite as an ablation if budget allows |
| 11 | Ad formats? Does 1024 px apply after resizing? | Square 1:1 at 1K (natively 1024×1024). Any other ratio is downscaled in code to ≤1024 and the step is disclosed |
| 12 | Tests live or offline? | Offline against committed images and recorded judge responses. One opt-in live smoke test |
