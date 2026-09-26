# Batch v1: 20 ads, evaluation report and human-label check

Status: reduced for time (2026-09-26): **9 requests × 3 candidates = 27 evaluated images** (pilot 01–02 plus 03, 04, 06, 07, 12, 18, 20). The other 11 requests are parked in `data/requests/batch-v1-unused/`. Requests are in [`data/requests/batch-v1/`](../data/requests/batch-v1/). **Human labelling was dropped for time (2026-09-26); the deliverable is the automated evaluation report.** Only runs recorded **after** the regional-style change (policy `guardrails/2`, prompts `generation/2`, evaluator `evaluator/2`) count.

## Coverage (by design)

| Axis | Distribution |
|---|---|
| Countries | IN 3, JP 3, DE 3, BR 3, AU 2, US 2, GB 2, AE 2 |
| Seasons | summer 7, winter 6, autumn 4, spring 3 (both hemispheres; tropical and arid climates) |
| Products | Heineken 5 (1, 2 and 3 references), sunglasses 4, water bottle 4, Jeep 4 (07 and 13 use two 4-door references; 09 single; 18 uses the 2-door snowy reference in a summer request as a season-leakage probe), Modelo 3 |
| Text modes | 8 Exact, 12 Extract (10 with protected phrases) |
| Hard text cases | negation (04 "Not dishwasher safe"), qualifiers (06 "Up to … selected stores", 15 "Not valid with other offers"), currency and numbers (08 €1.49, 10 ¥8,000 and 100%, 09 0% financing / 36 months, "Terms apply."), symbols (14 "500 ml • 24 h"), German copy (19), irrelevant prose (11), legal-age text (16) |
| Guardrail probe | 12: alcohol in AE (country note) — expect plan-review rejections or a `rejected_after_replan` flag |

## Estimated cost and time

About **$0.35 per request** (3 Gemini images at about $0.068, plus about 8–12 OpenAI calls including 3 visual-judge calls), so about **$6–9 for 20**, with ±50% uncertainty because reasoning tokens vary. About 3–4 minutes per request, so about **70 minutes** end to end. Set spend limits on both provider accounts first; the pipeline has no local cap.

## Steps

1. **Preconditions.** Keys in `.env`; `pip install -e ".[eval]"` and the weights are present (runbook §7); `pytest -q` passes. The batch uses its own state DB (`runs/batch-v1/state.db`), so earlier development runs never enter the report.
2. **Pilot (2 requests).** Run `scripts/run-batch.sh data/requests/batch-v1 2`. Inspect `runs/batch-v1/exports/<run_id>/` (best.png, candidates, `evaluations/*.json`). Go/no-go: generation works, verdicts look sane, C-REGION is populated.
   - If anything in code, prompts, policy or thresholds changes after the pilot, delete `runs/batch-v1/` and start again, so all 20 runs share one configuration. Pilot findings are recorded in the collaboration log.
3. **Freeze.** Record the commit hash and config versions in `docs/implementation-status.md`. No threshold or prompt tuning happens after this point. All 20 runs are reported as a single held-out set with provisional, uncalibrated thresholds, and the report says so.
4. **Run the batch.** Run `scripts/run-batch.sh data/requests/batch-v1`. It resumes safely: completed requests are skipped, and a failed request is logged while the batch continues.
5. **Automated report.** Run `ADGEN_STATE_DB=runs/batch-v1/state.db adgen report --out submission` and commit `submission/`. Reading order for humans:
   - `report.md`: summary, how ads are judged, results, a per-request ranking with plain-language reasons, limitations;
   - `contact-sheet.html`: every image with its verdicts;
   - `evidence/*.md`: one card per candidate listing every check with its reason, plus expected copy vs OCR-read copy;
   - `results.csv`: one readable row per image;
   - `results.json` and `evidence/*.json`: full machine-readable detail.
6. **Write-up.** Build the submission document around the implementation and design (`docs/design/`), citing `submission/report.md` for results, and link `docs/agent-collaboration.md` and `docs/decisions.md` for the agent disclosure.

## Honesty rules for the report

Twenty requests (60 images) is a smoke-scale demonstration. Report counts beside percentages. The evaluator's accuracy is not measured against human labels; the report says so. Thresholds were set before these results and not tuned on them. Unknowns and failed generations remain in every table.
