"""Human-readable evaluation bundle built only from the state store (no model calls)."""

import csv
import html
import io
import json
import statistics
from datetime import datetime
from pathlib import Path

from ..util import atomic_write, canonical

DIMENSIONS = ("text_selection", "text_rendering", "product", "context")


def _seconds(start, end):
    try:
        return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
    except (TypeError, ValueError):
        return None


def _json(path, value):
    atomic_write(path, json.dumps(value, indent=2, ensure_ascii=False).encode() + b"\n")


def collect(state, run_ids=None, include_synthetic=False):
    """One row per requested candidate (including failed/unevaluated), plus per-request metadata."""
    runs = state.rows("SELECT * FROM run ORDER BY created_at")
    if run_ids:
        runs = [r for r in runs if any(r["run_id"].startswith(p) for p in run_ids)]
    rows, requests = [], []
    for run in runs:
        snap = state.inspect(run["run_id"])
        if not snap["evaluations"]:
            continue
        stage = {
            (s["stage"], s["candidate_index"]): s
            for s in snap["stages"]
            if s["status"] == "succeeded"
        }

        def result(name, i=0):
            if (name, i) not in stage:
                return None
            return state._stage_result(stage[(name, i)]["exec_id"])[0]

        request = state.json(
            state.one(
                "SELECT artifact_id FROM artifact a JOIN stage_artifact sa USING(artifact_id) "
                "WHERE sa.exec_id=? AND sa.label='request'",
                (stage[("intake", 0)]["exec_id"],),
            )["artifact_id"]
        )
        config = state.json(
            state.one(
                "SELECT artifact_id FROM stage_artifact WHERE exec_id=? AND label='config'",
                (stage[("intake", 0)]["exec_id"],),
            )["artifact_id"]
        )["config"]
        calls = snap["model_calls"]
        synthetic = any(c["model_returned"] == "synthetic-fixture" for c in calls)
        if synthetic and not include_synthetic:
            continue
        exec_candidate = {s["exec_id"]: s["candidate_index"] for s in snap["stages"]}

        def cost(i, purposes):
            return round(
                sum(
                    c["cost_est_usd"]
                    for c in calls
                    if exec_candidate.get(c["exec_id"]) == i and c["purpose"] in purposes
                ),
                6,
            )

        latest = {e["candidate_index"]: e for e in snap["evaluations"]}
        winner = snap["selection"]["winner_index"] if snap["selection"] else None
        text_plan = result("copy_selection")
        reference_shas = [
            r["artifact_id"]
            for r in state.rows(
                "SELECT artifact_id FROM stage_artifact WHERE exec_id=? AND direction='output' "
                "AND label LIKE 'reference_%' ORDER BY label",
                (stage[("intake", 0)]["exec_id"],),
            )
        ]
        requests.append(
            {
                "reference_renditions": reference_shas,
                "ranking": json.loads(snap["selection"]["ranking"]) if snap["selection"] else None,
                "run_id": run["run_id"],
                "request": request,
                "mode": run["mode"],
                "synthetic": synthetic,
                "generation_config": {
                    k: config[k]
                    for k in (
                        "version",
                        "llm_model",
                        "image_model",
                        "analysis_effort",
                        "extract_effort",
                        "planner_effort",
                        "review_effort",
                    )
                },
                "config_sha256": run["config_sha256"],
                "selected_copy": [b["text"] for b in text_plan["blocks"]] if text_plan else None,
                "shared_cost_usd": cost(0, {"extract", "product_analysis", "judge_selection"}),
                "run_cost_est_usd": round(run["cost_est_usd"], 6),
                "cost_unknown": bool(run["cost_unknown"]),
                "winner": winner,
                "approved": bool(snap["selection"] and snap["selection"]["approved"]),
            }
        )
        for cand in snap["candidates"]:
            i, ev = cand["candidate_index"], latest.get(cand["candidate_index"])
            record = state.json(ev["record_artifact"]) if ev else None
            gen_stages = [
                s
                for s in snap["stages"]
                if s["candidate_index"] == i and not s["stage"].startswith("evaluation")
            ]
            eval_stages = [
                s
                for s in snap["stages"]
                if s["candidate_index"] == i
                and s["stage"].startswith("evaluation")
                and s["status"] == "succeeded"
            ]
            eval_stage = max(eval_stages, key=lambda s: s["ended_at"]) if eval_stages else None
            rows.append(
                {
                    "request_id": request["request_id"],
                    "run_id": run["run_id"],
                    "candidate_id": f"{run['run_id'][:8]}-c{i}",
                    "candidate_index": i,
                    "geography": request["geography"],
                    "season": request["season"],
                    "text_mode": request["text"]["mode"],
                    "status": cand["status"],
                    "error_code": cand["error_code"],
                    "guardrail_status": cand["guardrail_status"],
                    "image_artifact": cand["image_artifact"],
                    "llm_model": config["llm_model"],
                    "image_model": config["image_model"],
                    "generation_config_version": config["version"],
                    "evaluator_version": record["evaluator_version"] if record else None,
                    "overall_verdict": record["overall_verdict"] if record else "not_evaluated",
                    "overall_score": record["overall_score"] if record else None,
                    "failed_required_checks": record["failed_required_checks"] if record else None,
                    **{
                        f"{d}_{k}": (record[d][k] if record else None)
                        for d in DIMENSIONS
                        for k in ("verdict", "score")
                    },
                    "failed_checks": [
                        f"{d}:{c['id']}: {c['reason']}"
                        for d in ("gates", *DIMENSIONS)
                        for c in (record[d]["checks"] if record else [])
                        if c["required"] and c["verdict"] == "fail"
                    ],
                    "unknown_checks": [
                        f"{d}:{c['id']}"
                        for d in ("gates", *DIMENSIONS)
                        for c in (record[d]["checks"] if record else [])
                        if c["required"] and c["verdict"] == "unknown"
                    ],
                    "region_recognisable": next(
                        (
                            c["verdict"]
                            for c in record["context"]["checks"]
                            if c["id"] == "C-REGION"
                        ),
                        None,
                    )
                    if record
                    else None,
                    "product": (result("product_analysis") or {}).get("category"),
                    "source_text": request["text"]["source_text"],
                    "selected_copy": [b["text"] for b in text_plan["blocks"]]
                    if text_plan
                    else None,
                    "dinov2_best_similarity": next(
                        (
                            c["evidence"]["similarity"]["best"]
                            for c in record["product"]["checks"]
                            if c["id"] == "P-SIM" and c["evidence"].get("similarity")
                        ),
                        None,
                    )
                    if record
                    else None,
                    "execution_status": record["execution_status"] if record else None,
                    "evaluation_errors": record["errors"] if record else [],
                    "winner": i == winner,
                    "approved": i == winner and bool(snap["selection"]["approved"]),
                    "generation_latency_s": round(
                        sum(
                            filter(
                                None, (_seconds(s["started_at"], s["ended_at"]) for s in gen_stages)
                            )
                        ),
                        2,
                    ),
                    "evaluation_latency_s": round(
                        _seconds(eval_stage["started_at"], eval_stage["ended_at"]) or 0, 2
                    )
                    if eval_stage
                    else None,
                    "generation_cost_usd": cost(i, {"plan", "review", "image"}),
                    "evaluation_cost_usd": cost(i, {"judge_visual"}),
                    "_record": record,
                }
            )
    return rows, requests


CHECK_NAMES = {
    "G-DECODE": "Image file is readable",
    "G-SIZE": "Square and at most 1024 px",
    "S-SPANS": "Selected copy is an exact excerpt of the input",
    "S-PROTECTED": "Protected phrases kept whole",
    "S-CAPACITY": "Copy fits the ad (max 4 blocks, 120 characters, 20 words)",
    "S-EXACT": "Exact mode: the whole input is the copy",
    "S-FULL": "Exact mode: nothing to select",
    "SEL-MEANING": "Meaning preserved (no lost 'not', 'up to' or conditions)",
    "SEL-OMISSION": "Nothing essential left out of the copy",
    "SEL-RELEVANCE": "Selected copy is relevant to the product or offer",
    "R-BLOCKS": "Every copy line appears once, spelled exactly",
    "R-EXTRA": "No duplicated or unplanned text",
    "R-LEGIBLE": "Text is legible (confidence and size proxy)",
    "P1": "Exactly one product visible",
    "P2": "Same type of product",
    "P3": "Same shape and silhouette",
    "P4": "Same colours and materials",
    "P5": "Distinctive parts preserved",
    "P6": "Product branding matches the reference",
    "P-SIM": "Visual similarity to the reference (diagnostic)",
    "C-SEASON": "Scene fits the season",
    "C-CONTRA": "No out-of-season elements",
    "C-SETTING": "Setting plausible for the country",
    "C-REGION": "Country recognisable from the scene (diagnostic)",
    "GR-STEREO": "No cultural caricature or costume shorthand",
    "GR-TOKEN": "No flags; landmarks only in the background",
    "GR-RELIGION": "No religious imagery",
    "GR-SEASON": "No season contradictions",
    "GR-PEOPLE": "No real people; no minors with age-restricted products",
    "GR-ALCOHOL": "Responsible depiction of alcohol",
}
DIM_NAMES = {
    "gates": "Technical checks",
    "text_selection": "Text selection (input → copy)",
    "text_rendering": "Text rendering (copy → image)",
    "product": "Product (same object)",
    "context": "Context (country, season, guardrails)",
}
MARK = {
    "pass": "PASS",
    "fail": "FAIL",
    "unknown": "UNSURE",
    "not_evaluated": "NOT EVALUATED",
    None: "-",
}


def _count(rows, key):
    """Readable tally, e.g. 'PASS 3 · FAIL 1'; missing values show as 'not recorded'."""
    counts = {}
    for r in rows:
        label = MARK.get(r[key], r[key]) if key.endswith(("_verdict", "recognisable")) else r[key]
        label = "not recorded" if r[key] is None else label
        counts[label] = counts.get(label, 0) + 1
    return " · ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])) or "-"


def _median(values):
    values = [v for v in values if v is not None]
    return round(statistics.median(values), 2) if values else None


def _table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(
        lines + ["| " + " | ".join(str(c).replace("|", "/") for c in row) + " |" for row in rows]
    )


def _reasons(record, verdicts=("fail",)):
    """Plain-language reasons for required checks with the given verdicts."""
    out = []
    for dim in ("gates", *DIMENSIONS):
        for c in record[dim]["checks"] if record else []:
            if c["required"] and c["verdict"] in verdicts:
                out.append(f"{CHECK_NAMES.get(c['id'], c['id'])}: {c['reason']}")
    return out


def evidence_card(r):
    """One readable Markdown card per candidate, next to the full JSON evidence."""
    rec = r["_record"]
    head = f"# {r['request_id']} · candidate {r['candidate_index']}\n\n"
    if not rec:
        return head + f"**Not evaluated** (status `{r['status']}`, error `{r['error_code']}`).\n"
    parts = [
        head,
        f"![candidate](../{r['image']})\n\n" if r["image"] else "",
        f"**Verdict: {MARK[rec['overall_verdict']]}** · score {rec['overall_score']} · "
        f"{'**winner**' + (' (approved)' if r['approved'] else ' (not approved)') if r['winner'] else 'not selected'}\n\n",
        f"{r['geography']} / {r['season']} · {r['text_mode']} mode · plan guardrails: {r['guardrail_status']} · "
        f"evaluation {rec['execution_status']}{' (' + ', '.join(rec['errors']) + ')' if rec['errors'] else ''}\n",
    ]
    for dim in ("gates", *DIMENSIONS):
        d = rec[dim]
        rows = [
            [
                CHECK_NAMES.get(c["id"], c["id"]),
                MARK[c["verdict"]] + ("" if c["required"] else " (info)"),
                c["reason"],
            ]
            for c in d["checks"]
        ]
        parts.append(
            f"\n## {DIM_NAMES[dim]}: {MARK[d['verdict']]} (score {d['score']})\n\n"
            + _table(["Check", "Result", "Why"], rows)
            + "\n"
        )
    blocks = next(
        (
            c["evidence"]["blocks"]
            for c in rec["text_rendering"]["checks"]
            if c["id"] == "R-BLOCKS" and "blocks" in c["evidence"]
        ),
        [],
    )
    if blocks:
        parts.append(
            "\n## Copy: expected vs read by OCR\n\n"
            + _table(
                ["Expected", "Read in image", "Result", "Character error rate"],
                [
                    [
                        f"`{b['expected']}`",
                        f"`{b['observed']}`" if b["observed"] else "(not found)",
                        b["reason"],
                        b["cer"],
                    ]
                    for b in blocks
                ],
            )
            + "\n"
        )
    return "".join(parts)


def build(state, out, run_ids=None, include_synthetic=False):
    out = Path(out)
    rows, requests = collect(state, run_ids, include_synthetic)
    for r in rows:
        stem = f"{r['request_id']}__{r['candidate_id']}"
        r["image"] = f"images/{stem}.png" if r["image_artifact"] else None
        r["evidence"] = f"evidence/{stem}.json"
        r["evidence_card"] = f"evidence/{stem}.md"
        r["why_failed"] = _reasons(r["_record"])
        r["unsure_about"] = _reasons(r["_record"], ("unknown",))
        if r["image_artifact"]:
            atomic_write(out / r["image"], state.read(r["image_artifact"]))
        _json(
            out / r["evidence"],
            {k: v for k, v in r.items() if k != "_record"} | {"evaluation_record": r["_record"]},
        )
        atomic_write(out / r["evidence_card"], evidence_card(r).encode())
    for q in requests:
        q["reference_files"] = []
        for sha in q.pop("reference_renditions"):
            atomic_write(out / "references" / f"{sha[:12]}.png", state.read(sha))
            q["reference_files"].append(f"references/{sha[:12]}.png")
    public = [{k: v for k, v in r.items() if k not in {"_record", "image_artifact"}} for r in rows]
    _json(out / "results.json", public)
    columns = {
        "request": "request_id",
        "candidate": "candidate_index",
        "product": "product",
        "country": "geography",
        "season": "season",
        "text mode": "text_mode",
        "verdict": "overall_verdict",
        "score": "overall_score",
        "winner": "winner",
        "approved": "approved",
        "text selection": "text_selection_verdict",
        "text rendering": "text_rendering_verdict",
        "product match": "product_verdict",
        "context": "context_verdict",
        "country recognisable": "region_recognisable",
        "plan guardrails": "guardrail_status",
        "why it failed": "why_failed",
        "unsure about": "unsure_about",
        "generation s": "generation_latency_s",
        "evaluation s": "evaluation_latency_s",
        "generation USD": "generation_cost_usd",
        "evaluation USD": "evaluation_cost_usd",
        "image": "image",
        "evidence": "evidence_card",
        "run id": "run_id",
    }
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for r in public:
        values = []
        for key in columns.values():
            v = r.get(key)
            if key.endswith("_verdict") or key == "region_recognisable":
                v = MARK.get(v, v)
            elif isinstance(v, list):
                v = " | ".join(v)
            elif isinstance(v, bool):
                v = "yes" if v else "no"
            values.append(v)
        writer.writerow(values)
    atomic_write(out / "results.csv", buffer.getvalue().encode())
    atomic_write(out / "requests.jsonl", b"".join(canonical(q) + b"\n" for q in requests))
    atomic_write(out / "contact-sheet.html", contact_sheet(public).encode())
    atomic_write(out / "report.md", report(public, requests).encode())
    return {"requests": len(requests), "candidates": len(rows), "out": str(out)}


def contact_sheet(rows):
    color = {"pass": "#1b7f3b", "fail": "#b3261e", "unknown": "#8a6d00", "not_evaluated": "#555"}
    cards = []
    for r in rows:
        dims = "".join(
            f"<li>{DIM_NAMES[d]}: <b style='color:{color.get(r[d + '_verdict'], '#555')}'>{MARK[r[d + '_verdict']]}</b></li>"
            for d in DIMENSIONS
        )
        why = (
            "".join(f"<li>{html.escape(f)}</li>" for f in r["why_failed"])
            or "<li>nothing failed</li>"
        )
        img = (
            f"<img src='{r['image']}' alt='{r['candidate_id']}'>"
            if r["image"]
            else f"<div class='missing'>no image: {html.escape(str(r['error_code']))}</div>"
        )
        badge = (
            ("WINNER · APPROVED" if r["approved"] else "WINNER · not approved")
            if r["winner"]
            else ""
        )
        cards.append(
            f"<div class='card'>{img}<h3>{html.escape(r['request_id'])} · candidate {r['candidate_index']} <span class='badge'>{badge}</span></h3>"
            f"<p><b style='color:{color.get(r['overall_verdict'], '#555')}'>{MARK[r['overall_verdict']]}</b> · score {r['overall_score']} · "
            f"{html.escape(str(r['product']))} · {r['geography']}/{r['season']} · {r['text_mode']}</p><ul>{dims}</ul>"
            f"<p>Why it failed:</p><ul>{why}</ul><p><a href='{r['evidence_card']}'>full evaluation</a></p></div>"
        )
    return (
        "<!doctype html><meta charset='utf-8'><title>Contact sheet</title><style>body{font-family:system-ui;margin:16px;background:#fafafa}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}.card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px}"
        ".card img{width:100%;border-radius:4px}.badge{font-size:12px;color:#1b5e9e}.missing{height:200px;display:flex;align-items:center;justify-content:center;background:#eee}"
        "li{font-size:13px}</style><h1>Generated ads and their evaluations</h1><div class='grid'>"
        + "".join(cards)
        + "</div>"
    )


def report(rows, requests):
    evaluated = [r for r in rows if r["overall_verdict"] != "not_evaluated"]
    dim_rows = [
        [
            DIM_NAMES[d],
            *(sum(r[f"{d}_verdict"] == v for r in evaluated) for v in ("pass", "fail", "unknown")),
        ]
        for d in DIMENSIONS
    ]
    dim_rows.append(
        [
            "**Overall**",
            *(
                sum(r["overall_verdict"] == v for r in evaluated)
                for v in ("pass", "fail", "unknown")
            ),
        ]
    )
    approved = sum(q["approved"] for q in requests)
    failures = {}
    for r in evaluated:
        for reason in r["why_failed"]:
            name = reason.split(":")[0]
            failures[name] = failures.get(name, 0) + 1
    by_request = {}
    for r in rows:
        by_request.setdefault(r["run_id"], []).append(r)
    sections = []
    for q in requests:
        cands = sorted(
            by_request.get(q["run_id"], []), key=lambda r: (not r["winner"], r["candidate_index"])
        )
        ranking = {c["candidate_index"]: i + 1 for i, c in enumerate(q.get("ranking") or [])}
        req = q["request"]
        winner = next((r for r in cands if r["winner"]), None)
        table = _table(
            ["Rank", "Candidate", "Verdict", "Score", "Why"],
            [
                [
                    ranking.get(r["candidate_index"], "-"),
                    r["candidate_index"],
                    MARK[r["overall_verdict"]],
                    r["overall_score"],
                    "; ".join(r["why_failed"])
                    or (
                        "unsure: " + "; ".join(r["unsure_about"])
                        if r["unsure_about"]
                        else "all required checks passed"
                    ),
                ]
                for r in sorted(cands, key=lambda r: ranking.get(r["candidate_index"], 99))
            ],
        )
        sections.append(
            f"### {req['request_id']}\n\n"
            f"{cands[0]['product'] if cands else ''} · **{req['geography']} / {req['season']}** · {req['text']['mode']} mode · "
            f"copy: {' / '.join(f'`{t}`' for t in (q['selected_copy'] or []))}\n\n{table}\n\n"
            + (
                f"Winner (candidate {winner['candidate_index']}, {'approved' if winner['approved'] else 'not approved'}):\n\n![]({winner['image']})\n"
                if winner and winner["image"]
                else "No winner.\n"
            )
        )
    return f"""# Evaluation report: generated display ads

_Generated by `adgen report` from the pipeline's state store. Every number is computed from `results.json`; nothing is hand-edited. Per-candidate details: `evidence/*.md`. Visual overview: `contact-sheet.html`._

## 1. Summary

| | |
|---|---|
| Requests / candidates / evaluated | {len(requests)} / {len(rows)} / {len(evaluated)} |
| Requests whose winner is **approved** (passes every required check) | {approved} / {len(requests)} |
| Candidates passing every required check | {sum(r["overall_verdict"] == "pass" for r in evaluated)} / {len(evaluated)} |
| Country recognisable from the scene (diagnostic) | {_count(evaluated, "region_recognisable")} |
| Plan guardrail outcomes | {_count(rows, "guardrail_status")} |
| Evaluation completeness | {_count(evaluated, "execution_status")} |
| Median seconds per candidate: generation / evaluation | {_median([r["generation_latency_s"] for r in rows])} / {_median([r["evaluation_latency_s"] for r in rows])} |
| Estimated cost USD: generation / evaluation judge / shared per request | {round(sum(r["generation_cost_usd"] for r in rows), 3)} / {round(sum(r["evaluation_cost_usd"] for r in rows), 3)} / {round(sum(q["shared_cost_usd"] for q in requests), 3)} |

## 2. How each ad is judged

Each candidate gets PASS, FAIL or UNSURE per dimension. A candidate **passes** only if every required check passes. A single failed check fails it, and an unresolved check makes it UNSURE. Missing evidence never counts as a pass. The code makes these decisions; the AI models only supply measurements (OCR text, detections, similarity) or yes/no answers to single, specific questions.

| Dimension | What is checked | How |
|---|---|---|
| {DIM_NAMES["text_selection"]} | Copy is an exact excerpt; protected phrases intact; fits the ad; in Extract mode, meaning kept and nothing essential dropped | Code re-verification; AI judge (its FAIL counts only if it quotes the input) |
| {DIM_NAMES["text_rendering"]} | Each copy line appears once, spelled exactly; no duplicated or extra text; legible | OCR reads the image **without** being told the expected text; text on the product itself is ignored |
| {DIM_NAMES["product"]} | Exactly one product; same type, shape, colours, distinctive parts, branding | AI judge compares references with the ad; object detector used to crop and count; position and angle are not judged |
| {DIM_NAMES["context"]} | Season fits; nothing out of season; plausible for the country; no flags, caricature, religious imagery or irresponsible alcohol depiction | Same judge call; criteria come from the country/season inputs and the fixed policy, never from the generator's own plan |

Scores (0–1) only break ties between candidates: a higher score never beats a failed check. Ranking: verdict → fewer failed checks → score → plan guardrail outcome → candidate number.

## 3. Results

{_table(["Dimension", "PASS", "FAIL", "UNSURE"], dim_rows)}

Most common failure reasons:

{_table(["Check", "Candidates failing"], sorted(failures.items(), key=lambda x: -x[1])) if failures else "_none_"}

## 4. Per request

{chr(10).join(sections) if sections else "_No evaluated requests._"}

## 5. Limitations

- Small sample: counts matter more than percentages, and nothing here is statistically significant.
- The evaluator's accuracy has **not** been measured against human labels. Its behaviour is tested on recorded real evidence (for example, a genuinely duplicated headline is caught) and on constructed cases, but its judgments across this batch are unverified.
- The AI judge (OpenAI) is from a different model family than the image generator (Gemini), but the same family as the planner and reviewer.
- OCR cannot read stylised logos, so branding relies mainly on the judge. The text-rendering score reflects spelling, not duplicates; duplicates still fail the verdict.
- Thresholds (detector count, OCR confidence, legibility) are provisional and were not tuned on these results.
- Costs are estimates from returned token usage and list prices; provider dashboards are authoritative.
"""
