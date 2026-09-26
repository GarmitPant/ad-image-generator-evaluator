# AGENTS.md — G2 hackathon: context-enriched ad image generation + evaluator

> Drop-in brief for the coding agent in the new repo. Copy this file to the repo root as
> `AGENTS.md` (and symlink or copy it to `CLAUDE.md` for Claude Code), and copy files
> `01`–`05` into `docs/context/`. This brief is the summary; those files are the detail.

## Mission
Build, in **Python**, (1) a pipeline that turns a **reference product image + typed context
(geography, season) + required ad text** into a **display-ad image** using **Gemini 3.1 Flash
Image** (`gemini-3.1-flash-image`; Flash-Lite `gemini-3.1-flash-lite-image` allowed), and (2) an
**evaluator** that decides pass/fail per image on **text fidelity**, **product fidelity** and
**context adherence**, with **offline automated tests proving it separates good from bad
outputs**. A thin UI comes later, on top of the same pipeline API.

## Non-negotiables
1. **Typed inputs.** `geography` is an enum of ISO 3166-1 alpha-2 markets backed by a data
   registry; `season` is an enum (`spring|summer|autumn|winter`, as experienced in that market,
   so hemisphere-aware); `ad_text` is validated and rendered **verbatim**.
2. **Every output image ≤1024 px on the long edge.** At "1K" only 1:1 is natively 1024×1024;
   other ratios must be downscaled in code. A test enforces this for every committed image.
3. **Composition in code.** No model ever returns the overall score or verdict.
   `PASS = gates ∧ text ∧ product ∧ context`.
4. **Deterministic checks before model judgments.** OCR + normalized edit distance for text;
   Grounding DINO + DINOv2 similarity (+ colour ΔE) for product; a vision-language judge answers
   an **atomic yes/no checklist compiled from the same creative brief that drove generation**
   for context.
5. **Cross-check model claims.** Judge vs OCR, judge vs detector. Disagreement → `degraded`.
   Terminal states: `ok | degraded | failed`; headline metrics use `ok` only.
6. **Tests never call paid APIs.** Judge responses are recorded and replayed, keyed by
   `(image_sha256, prompt_hash, model_version)`. A `-m live` smoke test is opt-in.
7. **Secrets in `.env` only** (gitignored). Never print or commit a key.
8. **Ask before spending.** Show an estimate before any bulk generation. Keep a cost ledger.
9. **Log collaboration as you go.** At each milestone's end, append to
   `docs/agent-collaboration.md`: instruction received, what you built, what the human changed,
   why. Record design decisions in `docs/decisions.md` with the alternative considered.
10. **Honest reporting.** Counts beside percentages; say what thresholds were tuned on; no
    overclaiming (see `docs/context/05-personal-context.md` §5).

## Architecture (detail in `docs/context/02-scope-and-design.md`)
```
AdRequest ─► reference analysis (ProductProfile, cached)
          ─► context expansion (market registry → CreativeBrief: season_resolved, cues,
             must_not, text_plan)
          ─► prompt compile (versioned template, prompt_hash)
          ─► generate N=2–3 (Gemini 3.1 Flash Image, 1:1, 1K)
          ─► post-process (resize guard)
          ─► evaluate (gates → text → product → context) ─► compose (code)
          ─► select best | targeted edit repair (≤2) | labelled text-overlay fallback | FAIL
          ─► append-only JSONL run log + images + cost/latency
```

## Build order (5–8 h; cut from the bottom)
M0 smoke test (1 image at 1:1/1K is 1024×1024) → M1 schema + registry + prompt + generation →
M2 ~20 golden images → M3 evaluator (text, then product, then context, with record/replay) →
M4 constructed negatives + evaluator tests → M5 human labels + agreement report → M6 best-of-N
+ repair loop → M7 write-up + disclosure → M8 enriched-vs-raw ablation → M9 UI.

## Definition of done
- `pytest` green offline from a clean clone, no keys set
- ~20 golden requests with images, EvalRecords and human labels committed
- Per metric: constructed negatives fail on that metric; good outputs pass; agreement with human
  labels reported with kappa and counts
- `docs/WRITEUP.md`: design, rationale, success criteria stated before results, results,
  limitations, "how the agent was directed" (links the collaboration log and decisions)

## Where things are
- Problem and assumptions: `docs/context/01-problem-statement.md`
- Design, metrics, dataset, tests, success criteria, risks: `docs/context/02-scope-and-design.md`
- Model facts, SDK snippets, prices, what to buy, local models: `docs/context/03-models-apis-and-budget.md`
- Prior art and what to take from each: `docs/context/04-prior-art.md`
- Who you are working with and how: `docs/context/05-personal-context.md`

## When unsure
Stop and ask Garmit. Propose options with trade-offs; don't pick silently on scope, spend, or
anything that changes what the evaluator measures.
