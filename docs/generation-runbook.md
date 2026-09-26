# Generation v0.1: implementation contract and runbook

2026-09-26. This checkpoint implements generation only. User authorization for this session is **offline implementation only**. Commands mentioning live inference below are future operator instructions, not evidence that a live call occurred.

## 1. Scope and architecture

The current code follows design v0.4, with the explicitly bounded implementation corrections in [the review](generation-implementation-plan.md). There are no evaluator modules, local OCR/embedding dependencies, evaluation/selection tables, scores, best-image exports or UI.

| Stage | Implementation and persisted result |
|---|---|
| Intake | `assets.py`: inspect bytes, enforce input limits, reject duplicate originals/animation, EXIF orientation, sRGB conversion, white alpha background, <=1024 rendition with no upscale; save originals and renditions |
| Copy selection | `text.py`: Exact in code; Extract through one structured OpenAI request; validate codepoint offsets, exact substrings, source order, nonoverlap, protected spans and capacity; save omissions |
| Context | `context.py`: 8 country fact rows × 4 season inputs; southern months shifted six months; broad climate notes and exclusions |
| Product analysis | One structured multimodal OpenAI request over the canonically ordered full reference set; shared across candidates and cached across matching runs |
| Creative planning | One structured OpenAI plan per candidate; only copy roles/counts/linebreak counts, product profile, context, grid and policy; prior scene summaries encourage diversity |
| Plan guardrails | Keyword checks on proposed visible scene, plus OpenAI review against static rule IDs; one explicit replan; rejected second valid plan renders with a flag |
| Compilation | Six sections: PRODUCT, SCENE, LAYOUT, TEXT, AVOID, OUTPUT; actual selected strings enter only as literal display copy; omitted source and rationale are excluded |
| Image generation | One Gemini call per candidate, all reference renditions in user order, IMAGE modality, 1:1/1K, minimal thinking; automatic function calling and transport retries disabled |
| Output gate | Ignore thought images; require exactly one final image; decode, require square, retain original bytes, normalize published PNG <=1024; no quality judgment |
| Export | Save every successful candidate, text plan, summary and state snapshot; `winner:null`, `evaluation_performed:false`, `generated_unscored` |

Copy selection precedes paid product analysis to reject invalid selections cheaply. Exact validation is also done before creating a run. The product analysis cache key and actual input order both use sorted rendition hashes; generation preserves the declared reference order. A cached result remains connected to its original execution and receipt.

The implementation uses the accepted default model IDs `gpt-6-sol` and `gemini-3.1-flash-image`, and pinned OpenAI 2.54.0 / google-genai 2.25.0 SDKs. These IDs appear in the official [OpenAI model catalog](https://developers.openai.com/api/docs/models/gpt-6-sol) and [Gemini model catalog](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image). Account-specific availability and actual generation behavior still require a live compatibility probe. Gemini uses the SDK's `models.generate_content` interface; transport fixtures verify its serialized payload, not a live server's acceptance.

## 2. Setup and safe demo

Run all commands from the repository root. Python 3.11+ is declared; this checkpoint was locally exercised with Python 3.13.3 on macOS.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
adgen state init
adgen demo --directory runs/demo
```

`requirements.lock` is a pinned pip environment snapshot, including development dependencies; it is not a hash-verified cross-platform lock. `pyproject.toml` also pins direct runtime dependencies. No environment file is loaded for demo/replay. The demo creates its own small reference image, request and exact-match response fixtures, then runs three synthetic candidates. Images explicitly say they are synthetic. They are control-flow evidence only.

To replay that exact demo through the separate file-backed adapter:

```sh
adgen generate --request runs/demo/request.json --mode replay --fixtures runs/demo/fixtures
```

Change input, model, system/user prompt, schema, references, sampling identity or inference settings and the matching fixture is required. Missing fixtures stop the relevant stage; replay has no paid fallback. Cross-run product-cache hits may avoid a redundant recorded analysis. Use a separate `--db` to exercise every fixture from scratch.

## 3. Request contract

```json
{
  "request_id": "bottle-au-summer",
  "product_images": ["../data/products/water-bottle.jpg"],
  "geography": "AU",
  "season": "summer",
  "text": {
    "mode": "extract",
    "source_text": "Stay refreshed. Your everyday water bottle.",
    "protected_phrases": ["Stay refreshed."],
    "protected_spans": []
  },
  "n_candidates": 3,
  "aspect_ratio": "1:1"
}
```

- Closed schemas reject unknown fields. Source is 1–2000 Unicode codepoints, with visible content; unsafe controls/surrogates are rejected. Tabs/newlines/carriage returns are retained.
- Offsets are zero-based Unicode codepoints, start inclusive/end exclusive, without Unicode normalization. Protected phrases resolve **every** exact occurrence, including overlapping occurrences. Every protected span must be wholly contained in a selected block, not split between blocks.
- Exact preserves the entire string in one block. This is stricter than merely allowing whitespace reflow. Extract emits 1–4 contiguous spans in source order, with matching original substrings, no overlap and no paraphrase.
- Maximum selected content: 120 non-whitespace characters and 20 whitespace-delimited words. This is a conservative pilot limit, not a typography guarantee or universal language tokenizer.
- Extract can still omit essential meaning despite syntactic validity. `semantics_evaluated:false` is deliberate. Its semantic fidelity and rendered pixels must be assessed later.
- Reference byte limit: 20 MiB each. Pixel limit: 50,000,000 each. PNG/JPEG/WebP only, decoded rather than trusted by extension. Supports the committed ~42.2 MP Heineken reference. User must supply views of the same product; analysis records inconsistencies but does not prove identity.
- There are 1–3 references and 1–4 candidates. Full source strings are not passed to the creative planner, although naturally visible product branding may appear in its product profile.

## 4. Saved state and recovery

Default database: `runs/state.db`. Use shell environment `ADGEN_STATE_DB` or global option `adgen --db path/to/state.db ...` to override. Global options (`--db`, `--config`, `--policy`) precede the command.

Tables: `schema_version`, `run`, `stage_execution`, `artifact`, `stage_artifact`, `model_call`, `candidate`, `event`. Migrations: 001 (generation schema) and 002 (removes the local budget cap columns). Older databases upgrade in place on open; newer, unknown versions refuse to run. WAL and foreign keys are enabled. Shared stages use candidate index **0**, avoiding SQLite's nullable-UNIQUE loophole. Run IDs are UUID4 hex strings, not the design's proposed ULIDs.

Content-addressed artifacts live at `runs/artifacts/<prefix>/<sha256>` without extensions. Original bytes, normalized references, requests, source contracts, plans, prompts, policy/config snapshots, provider receipts and output images are stored and linked. Files are written using same-directory temp files, flush/fsync and atomic replacement before their database references are completed. Do not edit them manually.

Per-run OS file locks plus SQLite `lock_owner` prevent two workers handling the same run. OS locks release on process death. This implementation targets a local POSIX filesystem, not Windows, shared NFS or a distributed worker fleet.

```sh
adgen state show RUN_ID
adgen generate --request runs/demo/request.json --fixtures runs/demo/fixtures --run-id RUN_ID
adgen export RUN_ID --destination runs/my-export
adgen export-fixtures RUN_ID --destination runs/recordings/RUN_ID
```

Resume requires unchanged request, original-reference bytes, effective config/policy and mode. Completed stage artifacts are rehashed. Completed provider receipts can be reused after a crash before stage validation. A committed dispatch without a committed receipt becomes **unknown** and is never automatically resent. This conservatively treats even a crash immediately before network dispatch as uncertain.

Failed or blocked terminal stages are not automatically retried. An interrupted code-only stage can resume; a completed call can be reparsed from its receipt. To change input/config, retry a terminal provider failure or resolve a missing replay fixture, start a new run. Starting a new **live** run can spend again; inspect the prior call ledger first. There is no provider reconciliation API or override to blindly resend unknown calls in this version.

`export-fixtures` includes cached analysis receipts, preserves synthetic/live provenance, and refuses to overwrite a matching invocation with a different response. Use one directory per recording/run. Candidate and attempt identity are included, so two identical candidate prompts can retain different stochastic outputs. Records contain user copy and image content; keep the gitignored run directories local unless intentionally curating shareable evidence.

Exported files:

```text
runs/exports/RUN_ID/
  candidate-01.png
  candidate-02.png
  candidate-03.png
  summary.json
  text-plan.json
  state-snapshot.json
```

Only successfully gated images are exported. Partial success is represented by per-candidate statuses; no candidate is selected as best. `guardrail_status:approved` describes the **plan review**, not a judgment of the resulting image. A second rejected plan may still have a generated image, distinctly flagged.

## 5. Live operation and spend control

Create a local `.env` from `.env.example` and supply credentials. Do not put keys in requests or CLI arguments. `store=False` is sent to OpenAI. Exception payloads and SDK request headers are never persisted by the ledger.

```sh
adgen generate --request examples/heineken-exact.json --mode live --allow-paid
```

`--allow-paid` is the explicit opt-in for paid calls. It prevents an accidental live run and is not a budget. **There is no local spend cap** (removed 2026-09-26 at Garmit's direction). Control spend on the provider accounts: prepaid credit without auto-recharge, and project usage limits on OpenAI and Google.

Per three-candidate request, calls are:

| Case | LLM calls | Image calls |
|---|---:|---:|
| Exact, no replans | 7 | 3 |
| Extract, no replans | 8 | 3 |
| Exact, every candidate replans/reviews twice | 13 | 3 |
| Extract, every candidate replans/reviews twice | 14 | 3 |

Product cache hits reduce calls.

**Ledger:**
- Every call is recorded as `dispatched` before any network traffic.
- After the response, the returned usage and model ID are stored with a **report-only** cost estimate: token counts × list prices in `config/pipeline.toml`.
- Missing usage, or an uncertain outcome, sets `cost_unknown` instead of claiming zero.
- Estimates are for reporting cost per ad; the provider dashboards are the billing source of truth.
- No real cost is incurred by replay or synthetic calls.

Both SDK transport retries are disabled. Planner replan is a distinct, explicit attempt (at most two); image calls have no automatic retry. Provider errors, refusal, no final image or multiple final images become recorded candidate failures. A malformed first plan may be replanned without a reviewer; two invalid plans stop that candidate.

CLI exit codes: 0 all requested candidates generated; 3 partial success; 2 validation/blockage/no usable candidates. JSON output includes the run ID once created. Intake failures before run creation have no ledger/run ID.

## 6. Verification and next handoff

The offline suite covers all 32 geography/season combinations, exact Unicode spans/protection/capacity, image normalization/large references, text isolation, both replan outcomes, independent failures, SDK request/response transports, retries, locks/receipts, report-only cost estimates, schema migration, immutable resume, corruption and replay/export. It denies sockets globally. Synthetic fixture success does not test visual quality, prompt adherence or semantic extraction.

Next step: a small recorded live compatibility probe (one candidate first, then multi-reference and Extract), with spend limits set on the provider accounts. Confirm models, structured schema support, image modality/config and usage fields. Only after generation is proven should the next agent implement evaluation against independently defined criteria, then ranking and batch evaluation. Existing saved artifacts and text contracts provide its inputs; no evaluator criterion should be inferred from the planner's rationale.
