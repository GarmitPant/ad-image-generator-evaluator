# Implementation handoff

> Implementation checkpoint (2026-09-26): generation-only v0.1 is implemented and tested offline. Evaluation/selection remain future design below. Read [the runbook](../generation-runbook.md) for actual modules, commands, schema differences and recovery semantics.
Version 0.4 · 2026-09-26 · Generation implemented first; the pipeline generates 3 candidates, evaluates each and presents the best; the evaluator remains the main judged deliverable

## 1. Mission

Implement in this repository. Read AGENTS.md, then documents 01 (generation), 06 (state store) and 05 (text contract and evaluator).

Garmit confirmed on 2026-09-26:
- **Order:** build the generation pipeline first, then the evaluator.
- **Planning:** an LLM creative planner with general guardrails, not a registry per geography × season pair.
- **State store:** a SQLite state store.
- **Providers:** OpenAI for LLM stages, Google Gemini for images. No Anthropic code.
- **Keys:** placeholders only in the repository.

Freeform text is content, not visual direction. Historical `docs/context/` defaults (whole-input verbatim, best-of-N loop) are obsolete.

Progress checkpoints are kept in [docs/implementation-status.md](../implementation-status.md). Update it, and commit, at the end of every ticket.

## 2. Ticket order

| Ticket | Deliverable | Exit evidence (offline unless marked live) |
|---|---|---|
| G0 | Scaffold: `pyproject.toml` (uv), package layout, `config/pipeline.toml`, `.env.example`, README setup | `pytest` runs green on an empty suite from a clean clone with no keys |
| G1 | State store: schema incl. candidate/evaluation/selection, migrations, repository API, `adgen state init/show`, lock, events | Transition, resume/fingerprint, dispatched→unknown, per-candidate independence and no-secret tests |
| G2 | Contracts: AdRequest (1–3 references, candidates 1–4), enums, country + band×season tables, text contracts, ProductProfile, ResolvedContext, CreativePlan, GuardrailReview | Schema tests, hemisphere/month tests, enum-table completeness |
| G3 | S1 intake (multi-reference) + S4 context resolution | Decode/limits/rendition/hash/duplicate-reference tests on `data/products/`; resolver tests for all 8×4 pairs |
| G4 | LLM provider interface: OpenAI client (structured output, no hidden retries), record/replay, cost estimation | Replay tests; missing recording fails without network |
| G5 | S3 copy selection | Document 05 §3 validation cases via replay |
| G6 | S2 product analysis (all references, cached by reference set) | Cache reuse; unknowns; inconsistency warnings via replay |
| G7 | S5 planner (per candidate, told to differ from earlier plans) + S6 simple guardrails (`policy/guardrails.yaml`, keyword check, reviewer, one replan, flag) | Copy never in planner request; zone validation; approve / replan-approve / reject-then-generate / blocked paths |
| G8 | S7 compiler + S8 Gemini adapter + S9 gate + orchestrator for N candidates + `adgen generate` | Deterministic prompt hashes; response classification; one failed candidate does not stop others; end-to-end replay run saving `candidates/c{i}.png` |
| G9 (live) | Compatibility probe (document 02 §4) and first real 3-candidate run | Needs keys and an approved estimate |
| E0 | Local evaluator models: pinned weights, `adgen models download`, interfaces, M1 benchmark | Install/memory/latency measured and recorded; offline tests use recorded evidence |
| E1 | Text evaluation: source→copy checks, blind OCR, spatial one-to-one matching, CER/WER, rendering score | Document 05 text negative matrix on fixtures |
| E2 | Product (multi-reference) + context + image-guardrail checks; OpenAI judge; composition and scores | Truth-table and score tests; unknown propagation |
| G10 | S10 in-pipeline evaluation + S11 selection + S12 export (`outputs/…/best.png`, `summary.json`, `adgen export`) | Ranking-rule tests (verdict gate beats score); approved vs best-not-approved presentation; replay end-to-end |
| E3 | Human-labelled dev examples and threshold freeze | Criteria and tuning splits recorded before held-out |
| E4 | ~20 held-out requests (3 candidates each) + targeted negatives; **batched evaluation** command | Recorded observations, labels, offline regression tests |
| E5 | Report and disclosure | Confusion counts, abstentions, per-stage text metrics, selection analysis (did the winner match the human-preferred candidate), clean-clone replay |
| Optional | Repair, ablations, UI, hosted evaluator models, alternative LLM backend | Only after E5 |

The evaluator reads lineage and each candidate's `guardrail_status` from the state store.

## 3. Module layout

```text
config/pipeline.toml          # model IDs, efforts, timeouts, prices, template/policy versions
policy/guardrails.yaml        # general guardrail rules + lexicons
src/adgen/
  contracts/                  # pydantic models (request, text, context, plan, profile, review)
  geo.py                      # Geography/Season enums, country table, band×season table
  assets.py                   # decode, normalize, hash, rendition
  state/                      # sqlite schema, migrations, repository, lock
  llm/                        # provider interface, openai client, replay, pricing
  stages/
    intake.py  product_analysis.py  copy_selection.py  context_resolution.py
    creative_planning.py  plan_guardrails.py  prompt_compilation.py
    image_generation.py  output_gate.py  evaluation.py  selection.py  export.py
  orchestrator.py             # deterministic stage runner over the state store
  cli.py                      # generate, export, state init/show, models download, evaluate, report
  eval/                       # evaluator (document 05); eval/local/ = OCR, detector, embedder interfaces
tests/
```

One process and one SQLite file. No orchestration framework or agent runtime. The evaluator never invokes generation.

## 4. Acceptance cases

### Generation pipeline

- 1–3 references accepted; 0, >3 or duplicate-hash references rejected. All references reach product analysis and the image call.
- N candidates each get their own plan, guardrail result, prompt, image and evaluation. The planner for candidate i receives summaries of plans 1..i-1.
- Selection: a `pass` candidate outranks any higher-scoring `fail`/`unknown` candidate. No passing candidate means the winner is shown as "best available, not approved". Ties resolve deterministically.
- Every generated candidate image is saved and listed in `summary.json`, not just the winner.
- Invalid geography or season values are rejected by the enums. Every enum value has a country-table row (completeness test).
- AU/BR seasons resolve to southern-hemisphere months without renaming the season.
- The planner request contains block IDs, roles and lengths, and **never** any TextPlan string or source text. The test asserts on the recorded request.
- A CreativePlan with overlapping zones, a missing or unknown block_id, over-length fields or quoted display text fails code checks.
- Guardrail paths:
  - approved on first plan;
  - rejected then approved after replan;
  - rejected twice → generation proceeds and that candidate's `guardrail_status=rejected_after_replan` is recorded;
  - schema-invalid twice → that candidate is `blocked`; the others continue.
- A keyword hit counts as a rejection even when the reviewer approves.
- The compiled prompt contains no raw source text and no planner rationale. Its hash is deterministic.
- Keys never appear in the state store, recorded requests or artifacts.

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
- Missing replay fixtures fail offline. Actual model calls are opt-in (`--allow-paid`); spend limits live on the provider accounts.
- Repeated-judge stability uses independent calls, not multiple reads of the same cache entry.

## 5. Data and report requirements

Use a separate development set for prompt/threshold tuning. Keep a held-out set around twenty pipeline outputs for the submission, with mode/length/product/context variation. Preserve every attempted request, including invalid plans and failed generations; show why the output count differs from requests if it does.

Have Garmit label source-selection faithfulness and image dimensions separately, blind to machine results. Human expected content permits valid extraction alternatives; do not demand one gold string for all Extract examples. Label any mutation side effects so negatives are not falsely assumed to target only one metric.

Commit curated test images/manifests/labels and recorded observations with rights/provenance. Heavy model weights need pinned downloadable revisions and explicit setup; offline test execution must not make hidden downloads. Do not commit keys, environments or transient bulk runs.

Reports must include dimensional confusion counts, false accepts/rejects, abstention/coverage, undefined metric cases, actual latency/cost, threshold sources and repeat instability. Replay verifies regression; it does not prove a learned judge is correct. No target percentages are achieved by construction.

## 6. Initial implementation prompt

> Read AGENTS.md and docs/design/01, 06, 05 and 04. Implement tickets in the order of §2, updating docs/implementation-status.md and committing (authored by Garmit, no AI trailers) at each checkpoint. Use OpenAI for LLM stages and Gemini for image generation only; write no Anthropic code. Generate 3 candidates per request, each with its own plan. The planner sees text roles and lengths only. Guardrails are simple and predefined: one replan, then generate and flag. Evaluate every candidate with local vision models plus the OpenAI judge. Rank in code with verdicts gating scores, and export the best while keeping all. Every stage goes through the SQLite state store. Tests run offline with record/replay. No paid calls without a concrete approved estimate.
