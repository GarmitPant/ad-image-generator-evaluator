# Batch v1: 20 ads, evaluation report and human-label check

Status: ready to run. Requests are in [`data/requests/batch-v1/`](../data/requests/batch-v1/): 20 requests × 3 candidates = 60 evaluated images and 20 ranked winners. Only runs recorded **after** the regional-style change (policy `guardrails/2`, prompts `generation/2`, evaluator `evaluator/2`) count.

## Coverage (by design)

| Axis | Distribution |
|---|---|
| Countries | IN 3, JP 3, DE 3, BR 3, AU 2, US 2, GB 2, AE 2 |
| Seasons | summer 7, winter 6, autumn 4, spring 3 (both hemispheres; tropical and arid climates) |
| Products | Heineken 6 (1, 2 and 3 references), sunglasses 5, water bottle 5, Modelo 4 |
| Text modes | 10 Exact, 10 Extract (8 with protected phrases) |
| Hard text cases | negation (04 "Not dishwasher safe"), qualifiers (06 "Up to … selected stores", 15 "Not valid with other offers"), currency and numbers (08 €1.49, 10 ¥8,000 and 100%), symbols (14 "500 ml • 24 h"), German copy (19), irrelevant prose (11), legal-age text (16) |
| Guardrail probe | 12: alcohol in AE (country note) — expect plan-review rejections or a `rejected_after_replan` flag |

## Estimated cost and time

About **$0.35 per request** (3 Gemini images at about $0.068, plus about 8–12 OpenAI calls including 3 visual-judge calls), so about **$6–9 for 20**, with ±50% uncertainty because reasoning tokens vary. About 3–4 minutes per request, so about **70 minutes** end to end. Set spend limits on both provider accounts first; the pipeline has no local cap.

## Steps

1. **Preconditions.** Keys in `.env`; `pip install -e ".[eval]"` and the weights are present (runbook §7); `pytest -q` passes. The batch uses its own state DB (`runs/batch-v1/state.db`), so earlier development runs never enter the report.
2. **Pilot (2 requests).** Run `scripts/run-batch.sh data/requests/batch-v1 2`. Inspect `runs/batch-v1/exports/<run_id>/` (best.png, candidates, `evaluations/*.json`). Go/no-go: generation works, verdicts look sane, C-REGION is populated.
   - If anything in code, prompts, policy or thresholds changes after the pilot, delete `runs/batch-v1/` and start again, so all 20 runs share one configuration. Pilot findings are recorded in the collaboration log.
3. **Freeze.** Record the commit hash and config versions in `docs/implementation-status.md`. No threshold or prompt tuning happens after this point. All 20 runs are reported as a single held-out set with provisional, uncalibrated thresholds, and the report says so.
4. **Run the batch.** Run `scripts/run-batch.sh data/requests/batch-v1`. It resumes safely: completed requests are skipped, and a failed request is logged while the batch continues.
5. **Automated report.** Run `ADGEN_STATE_DB=runs/batch-v1/state.db adgen report --out submission`. Commit `submission/` (images, evidence, results, contact sheet, report).
6. **Blind human labelling.** Open `submission/labeling-sheet.html`. It shows the inputs, the reference product and the copy that must appear, with no evaluator results. Copy `submission/labels-template.csv` to `data/labels.csv` and fill `label` with pass/fail, plus `labeler` and a `note` for failures. Do not open `contact-sheet.html` or `report.md` before labelling. Minimum: `overall` and `text_rendering` for all 60 candidates, and all six dimensions for the 20 winners. Everything else is optional. Format: `data/LABELS.md`.
7. **Final report with the credibility check.** Run `ADGEN_STATE_DB=runs/batch-v1/state.db adgen report --out submission --labels data/labels.csv`. Section 6 then shows, per dimension, the counts of false accepts and false rejects, abstentions, agreement and kappa, measured against the success criteria stated in §4. Commit.
8. **Write-up.** Use `submission/report.md` as the results core. The narrative and the agent disclosure link `docs/agent-collaboration.md` and `docs/decisions.md`.

## Honesty rules for the report

Twenty requests (60 images) is a smoke-scale demonstration. Report counts beside percentages. There is one annotator, so no inter-rater agreement is claimed. Thresholds were set before these results and not tuned on them. Unknowns and failed generations remain in every table.
