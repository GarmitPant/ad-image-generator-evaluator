# Implementation handoff — evaluation first

Version 0.2 · 2026-09-26

## 1. Mission

Implement in this repository. Read AGENTS.md and document 05 first. The primary engineering deliverable is a defensible automated evaluator, not an elaborate ad-generation architecture. Garmit confirmed explicit Exact/Extract text policies, with optional protected phrases. Freeform text supplies ad content, not visual style.

Latest specification authority: 05 defines text/evaluation; 01 defines minimal generation; 02 gives provisional model choices. Historical context contains obsolete whole-input-verbatim and generation-first defaults. Do not copy those back into code.

## 2. Ticket order

| Ticket | Deliverable | Exit evidence |
|---|---|---|
| E0 | Contracts, rubric skeleton and fixture manifest | Exact/Extract schema tests; separate selection/render/product/context verdicts |
| G0 | Functional one-image generator | One allowed-model image, final pixels ≤1024, immutable input/TextPlan/image manifest |
| E1 | Source→copy checks and render OCR/alignment | Protected coverage, span integrity, omission semantics, spatial one-to-one matching, exact/CER/WER observations |
| E2 | Product/context evidence modules | Real observed evidence, documented model limitations, unknown handling and code-based composition |
| E3 | Human-labelled dev examples and threshold freeze | Criteria and tuning splits recorded before held-out evaluation |
| E4 | About twenty held-out pipeline images plus targeted negatives | Actual recorded observations, pass/fail/unknown labels and offline regression tests |
| E5 | Report and disclosure | Confusion counts, abstention/coverage, separate text-stage metrics, failure analysis and clean-clone replay |
| Optional | Generation repair, best-of-N, enrichment ablation, UI | Only after E0–E5; separately bounded costs |

Aim to keep initial generation work to roughly one fifth of remaining engineering time; spend the rest on evaluation/data/reporting. This is a planning recommendation, not a claim about judges' numeric scoring weights. The earlier six-hour estimate is stale; check actual remaining time before setting deadlines. Do not burn the final report/test buffer on image polish.

## 3. Minimal modules

```text
src/adgen/
  contracts.py          # request, source contract, TextPlan, EvalRecord
  assets.py             # decoding, normalization, hashes, artifact save
  text_selection.py     # Exact in code; Extract model + structural validation
  registry.py           # reviewed geography/season profiles
  compiler.py           # fixed composition and literal selected copy
  generation.py         # one allowed Gemini image call
  store.py  budget.py   # manifests, resume, usage and reservations
  eval/
    source_fidelity.py  # source→plan checks and semantic observations
    text_rendering.py   # blind OCR, spatial blocks, assignment, exact/CER/WER
    product.py          # presence/identity/branding evidence
    context.py          # atomic scene checklist
    compose.py          # policy in code, unknown propagation
    providers.py        # structured judge and record/replay
    report.py           # metrics from labels + records, no invented summaries
  cli.py                # generate, evaluate, replay, report
```

Use one Python process and files. The evaluator accepts external fixtures and never invokes generation. Keep provider-boundary schemas and versions explicit. Do not add an orchestration framework just to express this sequence.

## 4. Acceptance cases

### Text contract and extraction

- Exact input retains all visible characters in order, with only documented whitespace/reflow equivalence.
- Extract accepts longer source prose and may omit irrelevant material without creating a whole-source OCR mismatch failure.
- Protected name omitted or altered fails source selection even if the rendered image matches the bad plan exactly.
- Invalid offsets, normalized-string offsets, wrong source hash, ambiguous repeated occurrences and out-of-range spans fail validation.
- Selecting “waterproof” from “Not waterproof” passes a substring lookup but fails semantic fidelity.
- Losing “up to” or “selected items” from an offer is tested with frozen human-labelled expectations.
- Capacity overflow returns copy_capacity_exceeded; no silent truncation or switch from Exact to Extract.
- The selector cannot invent product claims or render instructions. Raw prose is not passed into scene planning.
- Scene instructions inside source text do not change the structured geography/season profile.

### Rendering and evidence

- Correct selected blocks are matched one-to-one to spatial OCR blocks; a single word cannot satisfy two required occurrences.
- Changed number/currency/percent/case/punctuation, missing word, clipped text and extra offer produce specific failed checks.
- A harmless font or line-wrap change remains a positive when legible.
- A matching phrase only on the product label does not silently satisfy an ad-headline requirement.
- Expected text is absent from blind transcription prompts; store those prompts so leakage can be audited.
- Missing or conflicting OCR evidence propagates unknown/degraded, not a fabricated typo or automatic pass.
- Source selection and rendering verdicts are reported separately and jointly.

### Product/context and composition

- Same-category wrong product/brand is a required negative; a high embedding score cannot bypass branding criteria.
- Missing/duplicate product, altered distinguishing features and allowable viewpoint changes have labelled fixtures.
- Context negatives rely on observable violations, not arbitrary “wrong-country” labels for visually ambiguous scenery.
- Optional scenery is not a hard requirement. Dependencies skip invalid follow-up questions when their subject is absent.
- A trusted failure remains a failure even if another check is unknown; an unknown required check prevents pass when there are no failures.
- Model outputs supply observations/atomic answers only; overall verdict is composed in code.

### Operations and reproducibility

- No fourth-party generation or non-allowed image model fallback; one baseline image dispatch and zero hidden retries.
- Refusals/no-image/corrupt/oversized responses are classified; generated-unscored is never accepted.
- Crash/resume reuses completed artifacts without repeating paid generation; uncertain remote outcomes stay explicit.
- Cache invalidation covers source, protected spans, plan, image/reference, rubric, thresholds and model configuration.
- Missing replay fixtures fail offline. Actual model calls are opt-in and separately budgeted.
- Repeated-judge stability uses independent calls, not multiple reads of the same cache entry.

## 5. Data and report requirements

Use a separate development set for prompt/threshold tuning. Keep a held-out set around twenty pipeline outputs for the submission, with mode/length/product/context variation. Preserve every attempted request, including invalid plans and failed generations; show why the output count differs from requests if it does.

Have Garmit label source-selection faithfulness and image dimensions separately, blind to machine results. Human expected content permits valid extraction alternatives; do not demand one gold string for all Extract examples. Label any mutation side effects so negatives are not falsely assumed to target only one metric.

Commit curated test images/manifests/labels and recorded observations with rights/provenance. Heavy model weights need pinned downloadable revisions and explicit setup; offline test execution must not make hidden downloads. Do not commit keys, environments or transient bulk runs.

Reports must include dimensional confusion counts, false accepts/rejects, abstention/coverage, undefined metric cases, actual latency/cost, threshold sources and repeat instability. Replay verifies regression; it does not prove a learned judge is correct. No target percentages are achieved by construction.

## 6. Updated initial implementation prompt

> Read AGENTS.md and docs/design/05, 01 and 04. Implement E0 and the minimal G0 path, then prioritize evaluator E1–E5. Use explicit Exact/Extract modes and source-span-backed TextPlans; freeform text is copy, not visual direction. Evaluate selection fidelity separately from rendered text fidelity. Keep generation to one allowed Gemini image call per request. Use real labelled fixtures plus offline record/replay and code-composed verdicts. Do not implement repair, best-of-N, aesthetic planning or UI yet. Before paid calls show a concrete estimate and use Garmit's approved budget. Record implementation decisions and actual validation in the collaboration log.
