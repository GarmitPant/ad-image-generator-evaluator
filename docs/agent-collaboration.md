# Agent collaboration log

## 2026-09-26 — Design v0.1

- Human instruction: read the seven g2-ad-imagegen context files; research and create detailed system specs for another coding agent; begin with generation; keep chat concise and UI secondary.
- Work performed: source review; official model-documentation research; generation contracts, model roles, challenge register and staged implementation handoff.
- Human steering: about six hours left, no configured billing/budget, product photos forthcoming; proposed separate model tasks for input interpretation, ad planning and text preparation before rendering.
- Design response: separate reference-analysis and structured ad-planning calls; preserve binding ad copy; compile the validated plan into image instructions in code.
- Validation: document-local links and Markdown fence balance checked. No implementation tests, paid inference, model benchmarks or evaluator calibration performed.
- Status: draft architecture, not approved empirical results.

## 2026-09-26 — Repository preparation

- Human instruction: supplied newly created `GarmitPant/ad-image-generator-evaluator` repository for this project.
- Work performed: cloned the empty repository; copied all seven historical context files and five design documents; updated repository references; wrote reconciled agent instructions, root README, ignore rules and decision/collaboration logs.
- Human changes: repository selection is confirmed; no new architecture or budget approvals were received.
- Validation: original context integrity and documentation links checked before committing; no application code exists yet.
- Next: continue generation-design review and authorize an implementation slice separately; enable Gemini billing and source product photos before live testing.


## 2026-09-26 — Evaluation-first scope and text semantics, v0.2

- Human instruction: this repository is for implementation too; judges emphasize automated evaluation methods and criteria; generation only needs to function. Freeform input is copy/content, from which relevant parts may be selected, with some text preserved verbatim; evaluate input vs selected/rendered text.
- Clarification received: Garmit explicitly selected Exact/Extract modes with optional protected phrases.
- Work performed: introduced the evaluation/text-contract spec; separated source-selection fidelity from image-rendering fidelity; replaced generation-first handoff with evaluator-first tickets; simplified proposed generation to one image; reconciled root instructions, model roles and decision register.
- Validation: documentation references, current-contract consistency and preserved historical-context integrity checked. No application code, paid inference or empirical accuracy claims added.
- Design status: explicit priorities/modes confirmed; proposed limits, model choices, matching/calibration details remain subject to pilot evidence. Budget remains unapproved.

## 2026-09-26 — Reference product images added (Claude Code)

- Human instruction: pull `~/Downloads/Reference Images` into the workspace and repo; commits must be authored by Garmit, not Claude Code.
- Work performed: copied six originals byte-for-byte to `data/products/` (SHA-256 verified against source); recorded Unsplash provenance from download metadata, per-image evaluation roles, trademark limitation, and that `heineken-3.jpg` (~42.2 MP) exceeds the proposed 40 MP input limit.
- Validation: hash equality with source files; visual inspection of downscaled previews. No code, paid inference or design changes.
- Next: Garmit to supply pending design changes before implementation begins.

## 2026-09-26 — Generation design v0.3 (Claude Code)

- Human instructions: Claude Code is the implementing agent and keeps checkpoints. OpenAI API for text models, Gemini for image generation; no Anthropic implementation now. Start with the generation pipeline. Add an LLM planner. Replace the per geography×season registry with general anti-stereotype guardrails and predefined enums (8 countries accepted). One replan, then generate and flag in evals. SQLite state store as an architectural requirement, set up locally with instructions. Planner gets text roles and lengths only. Commit placeholder keys only.
- Agent proposals accepted by Garmit: 8-country list, roles+lengths planner input, SQLite, stage map S1–S9.
- Work performed: rewrote 01 (v0.3 pipeline, sub-agents, guardrails, prompt compiler), added 06 (state-store schema/rules), rewrote 02 (OpenAI/Gemini roles, `gpt-6-sol` proposal from OpenAI's model catalog, spend arithmetic), rewrote 04 tickets (G0–G9 then E0–E5), updated 05 context-adherence criteria so the evaluator does not grade against the planner's own cues, extended 03/decisions, added `.env.example` and docs/implementation-status.md.
- Validation: cross-document consistency and link checks. No code, tests or paid inference yet.

## 2026-09-26 — Design v0.4: candidates, selection, simplified guardrails (Claude Code)

- Human instructions: keep guardrails simple and predefined (no web search); generate multiple ads per input, judge each and present the highest scored; save generated images; allow single or multiple references; confirm the evaluator needs visual models. Chose 3 candidates with one plan each, max 3 references, and local-only evaluator models after asking about hosted options (M1, 8 GB). Instructed: update specs and commit only; do not build the scaffold yet.
- Agent proposals accepted: static policy file with optional country notes, code ranking rule with verdicts gating scores, `outputs/` export layout, candidate/evaluation/selection tables. Hosted-inference options (Modal, HF Endpoints, Replicate) presented and deferred.
- Work performed: rewrote 01 (v0.4), extended 06 schema, updated 05 (scores, ranking, multi-reference product evidence, image-level guardrail checks, local model table), 04 tickets (G0–G10, E0–E5), 02 costs, 03/decisions, AGENTS/README, .gitignore (`outputs/`), implementation-status.
- Validation: cross-document consistency and link checks only. No code, tests or paid inference.

## 2026-09-26 — Generation implementation v0.1 (Codex)

- Human instructions: inspect the revised plan/specs and implement generation end to end in this repository, no UI and no evaluator; approximately three hours remain. In response to a request for live-test authorization, Garmit explicitly selected **offline implementation only**.
- Review: retained v0.4 architecture. Corrected nullable shared-stage uniqueness, analysis cache ordering, keyword scans of avoid/rationale, and generation-only completion/export semantics. Recorded the plan in `docs/generation-implementation-plan.md`.
- Work: implemented Python contracts, intake/context/text logic, SQLite stages/artifacts/calls/events/candidates, immutable resume and locks, provisional budget reservations, OpenAI and Gemini adapters, strict replay and fixture export, product analysis, creative planning/review/replan, prompt compilation, multi-candidate orchestration, output gate, CLI, synthetic demo and generation-only export. Added pinned dependencies, examples, runbook and offline CI workflow.
- Validation: 88 offline tests and Ruff passed; real installed SDKs exercised via mock HTTP transports with sockets denied. Synthetic end-to-end smoke runs using the existing Heineken and bottle reference photos saved 3 and 2 candidate PNGs respectively. Tested the ~42 MP reference. No real inference occurred; synthetic outputs are prominently labeled and cannot substantiate model quality.
- Boundaries: no paid usage, API-key exposure, evaluator/UI implementation, image scores or winner claims. Live compatibility is deferred. Commits use the configured human author, without AI coauthor trailers.

## 2026-09-26 — CI verification and budget-cap removal (Claude Code)

- Human instructions: evaluate the completed generation implementation as a CI pipeline without changing it; then (after discussing how the budget works) remove the local budget cap because provider accounts can enforce usage limits; commit as Garmit.
- CI verification (before any change): clean clone of 4049341, Python 3.11 arm64, no keys — requirements install, `ruff check`, `pytest` (88 passed), `adgen demo`, demo replay, clean working tree, git-history secret scan and live-mode credential/flag refusal all passed. Remote GitHub Actions status could not be checked (private repo, no `gh`).
- Change: removed `--budget-usd`, reservations and cap check; added migration 002 dropping `run.budget_cap_usd` and `model_call.reservation_usd`; cost estimates now report-only (0 + `cost_unknown` when usage is missing). Updated tests (removed budget tests; added no-cap live run, v1→v2 migration and cost-estimate tests; fixed future-schema test for multi-row versions) and docs.
- Validation: 89 passed; ruff check and format clean; demo OK; live mode still refuses without `--allow-paid`; migration verified on a copy of the existing local database (3 runs, 9 calls preserved).

## 2026-09-26 — First live generation run curated (Claude Code)

- Human action: Garmit added his own keys locally and ran `adgen generate --mode live --allow-paid` on the agent-written request `runs/requests/rayban-extract.json` (sunglasses.jpg, AU summer, Extract, protected "Built for bright days.", n_candidates set to 2 by Garmit). Instruction: curate the outputs into the repository.
- Result: 8 calls completed (4 OpenAI stages + reviews, 2 Gemini images), both 1024×1024, ~$0.19 report-only estimate, ~1.5 min. Candidate 1 renders all four blocks once; candidate 2 duplicates the protected phrase although the prompt contains it once — a naturally occurring rendering negative.
- Work performed: copied request, text plan, context, product profile, per-candidate image/plan/review/prompt and per-call usage into `data/live-runs/2026-09-26-rayban-au-summer-extract/`; README separates agent observations from human labels; `labels.json` left empty for Garmit's independent labelling. Secret scan clean.

## 2026-09-26 — Behaviour-preserving simplification of generation code (Claude Code)

- Human instruction: simplify the generation implementation before the evaluator, keeping the same features and architecture (no feature cuts).
- Bug found and fixed first (separate commit af75a71): reference normalization embedded LittleCMS's timestamped sRGB profile, so identical references hashed differently every run — defeating the cross-run product-analysis cache and making recorded live runs unreplayable. The fix stops embedding the profile; regression test added. The 2026-09-26 live Ray-Ban recording predates this fix and cannot be replayed.
- Refactor: one explicit `creative_plan_invalid` code and a single replan handler, replacing two copies of the feedback block and matching on exception class names (legacy codes still accepted on resume); per-candidate work extracted into `_run_candidate` with a `Shared` holder (the seam where evaluation/selection will plug in); run and summary status from one helper; one `failure()` helper for the "never log exception text" rule; zone grid defined once (`contracts.ZONE_CELLS`, `Zone` derived from it); CLI error output via one `error_payload`.
- Validation: a content-addressed behaviour signature of a real 3-reference × 3-candidate Heineken run (20 stage fingerprints, 10 invocation hashes, 42 artifact hashes, 41 events) is byte-identical before and after; no test changed; 90 passed; ruff check/format clean; demo and replay OK; CLI error JSON unchanged. Visible difference: an invalid plan is now recorded as `creative_plan_invalid` rather than `ValueError`/`ValidationError`.
- Honest outcome: line count roughly unchanged (src 2,029 → 2,025). The agent's earlier estimate of 100–150 fewer lines did not materialize; the gain is structure and fewer fragile patterns, not size.

## 2026-09-26 — Evaluator, ranking and submission report (Claude Code)

- Human instructions: implement evaluation connected to generation with ranking; product fidelity = same-object identity (no position/orientation); local models only; store every evaluation in files for a submission bundle (report.md, results.csv/json, contact-sheet.html, images/, evidence/, requests.jsonl) with a small human-labelled subset; keep checkpoints; conserve tokens.
- Work performed (commits dbdbff6, 380f0b9, 9b89256, c54be86, c2bdf45): recorded/replayable local vision (PaddleOCR PP-OCRv6, Grounding DINO, DINOv2); text selection and rendering evaluation; visual judge and composition; pipeline integration with selection, migration 003 and `evaluate`; `adgen report`. Found and fixed an agent-introduced leak (judge prompt contained passing answers) before it shipped to a live call.
- Validation: 114 offline tests including genuine recorded OCR/detection of the live candidates (c1 passes; c2's duplicated phrase fails); demo end-to-end; offline dry run of evaluating the live run on a DB copy made only judge calls. No live judge call yet; no human labels yet; thresholds uncalibrated.

## 2026-09-26 — Regional style v2 and batch v1 plan (Claude Code)

- Human instruction: relax guardrails on styles, culture and geography so regions are distinguishable; add the region evaluator check; record only new runs from now on; plan 20 ads with a report, then human labels and an evaluation-vs-labels report.
- Work performed: policy guardrails/2, neutral per-country notes inviting a specific region, planner instruction for ≥2 regional cues, version bumps, diagnostic C-REGION check, blind labeling sheet and labels template in `adgen report`, 20 validated batch requests, resumable `scripts/run-batch.sh`, `docs/batch-v1-plan.md`.
- Validation: 118 offline tests (new: relaxed-keyword and still-banned cases, C-REGION non-decisive, blind-sheet contents); all 20 requests validated offline (schema, intake, protected phrases, Exact capacity). No live calls.

## 2026-09-26 — Jeep requests, labels removed, readable report (Claude Code)

- Human instruction: take the three new Jeep images into account and modify the requests; remove human labelling (short on time); make the compiled evaluation output easy for humans to read; only the auto-generated evaluation report remains; the submission write-up will focus on implementation and design.
- Agent disclosure: the Jeep images had already been committed unreviewed in 3acd277 by the agent's `git add -A`; they were then inspected (Unsplash, 12–25 MP, no sensitive content) and their provenance recorded. The agent now stages explicit paths.
- Work performed: provenance; four Jeep requests (2-door jeep-2 kept separate from the 4-door references); removed labels CSV, labelling sheet, template and agreement code; rewrote the report output (plain-language names, per-request ranking and reasons, evidence cards, readable CSV); P-SIM reason now shows the similarity value.
- Validation: all 20 requests valid offline; 118 tests; report rendered and inspected on the dry-evaluated live Ray-Ban run.

## 2026-09-26 — Pilot findings and evaluator/3 (Claude Code)

- Human action: Garmit ran the 2-request pilot (both evaluated; winners approved).
- Pilot review found 3 of 6 candidates falsely rejected by the evaluator (the ads were correct): overlapping OCR line boxes were not merged; a 3-line Exact block wrapped onto 4 lines exceeded the 3-line segment cap; bottle-label text sat in a detection box scored 0.49, below the 0.5 count threshold, so it counted as extra ad copy. Failure reasons also printed the check's fixed description instead of the actual problem.
- Fixes (evaluator/3): allow slightly overlapping line boxes; blocks may span up to 6 lines; label text is excluded using all raw detections; the detector prompt drops parentheticals ("beer (alcoholic lager)" → "beer"); count threshold 0.4 with overlapping boxes de-duplicated; outcome-specific reasons. Evaluation stages are now versioned (`evaluation@evaluator/3`), so existing runs are re-scored with `adgen evaluate` without regenerating.
- Validation: 123 tests, including the three genuine pilot false rejects recorded as fixtures (`tests/fixtures/pilot_false_rejects.json`).
- Methodology note: this change was made after inspecting pilot results, so the two pilot requests are development data for the evaluator, not held out; the report must say so.

## 2026-09-26 — Submission design draft (Codex)

- Human instruction: review the completed implementation and plan a concise, understandable design document while the report batch runs.
- Work: reviewed current generation/evaluation code, policy, ranking, reporting and pilot history at commit 441eff7; created root DESIGN.md as a compact draft covering decisions, evidence, challenges, limitations and coding-agent disclosure. Results remain pending and link to the generated submission bundle.
- Reporting corrections captured: planned set is 9 requests/27 images; older coverage counts are stale; pilot requests informed evaluator/3 and are not held out; no human-label accuracy claim. Documented actual product-count corroboration and OCR failure behavior rather than stronger README shorthand.
- Validation: checked technical claims against source. No pipeline/config changes, inference, batch restart or report overwrite.
