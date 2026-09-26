"""Reproducible submission bundle built only from the state store and human labels (no model calls)."""

import csv
import html
import io
import json
import statistics
from datetime import datetime
from pathlib import Path

from ..util import atomic_write, canonical

DIMENSIONS = ("text_selection", "text_rendering", "product", "context")
LABEL_DIMENSIONS = ("overall", *DIMENSIONS, "region")
LABEL_COLUMN = {"overall": "overall_verdict", "region": "region_recognisable"}


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
                if s["candidate_index"] == i and s["stage"] != "evaluation"
            ]
            eval_stage = stage.get(("evaluation", i))
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


def read_labels(path, rows):
    if not path or not Path(path).exists():
        return []
    labels = []
    for line in csv.DictReader(Path(path).open()):
        matches = [
            r
            for r in rows
            if r["run_id"].startswith(line["run_id"])
            and r["candidate_index"] == int(line["candidate_index"])
        ]
        if (
            len(matches) == 1
            and line["dimension"] in LABEL_DIMENSIONS
            and line["label"] in {"pass", "fail"}
        ):
            labels.append({**line, "row": matches[0]})
    return labels


def agreement(labels):
    """Positive class = defect (fail). Unknown automated verdicts are abstentions, reported separately."""
    out = {}
    for dim in LABEL_DIMENSIONS:
        column = LABEL_COLUMN.get(dim, f"{dim}_verdict")
        items = [(lab["label"], lab["row"][column]) for lab in labels if lab["dimension"] == dim]
        if not items:
            continue
        tp = sum(h == "fail" and a == "fail" for h, a in items)
        fp = sum(h == "pass" and a == "fail" for h, a in items)
        fn = sum(h == "fail" and a == "pass" for h, a in items)
        tn = sum(h == "pass" and a == "pass" for h, a in items)
        n = tp + fp + fn + tn
        po = (tp + tn) / n if n else None
        pe = (((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n**2) if n else None
        kappa = round((po - pe) / (1 - pe), 3) if n and pe is not None and pe < 1 else None
        out[dim] = {
            "labelled": len(items),
            "abstained": len(items) - n,
            "tp": tp,
            "fp_false_reject": fp,
            "fn_false_accept": fn,
            "tn": tn,
            "agreement": round(po, 3) if po is not None else None,
            "cohens_kappa": kappa,
            "fail_precision": round(tp / (tp + fp), 3) if tp + fp else None,
            "fail_recall": round(tp / (tp + fn), 3) if tp + fn else None,
        }
    return out


def _count(rows, key):
    counts = {}
    for r in rows:
        counts[r[key]] = counts.get(r[key], 0) + 1
    return counts


def _median(values):
    values = [v for v in values if v is not None]
    return round(statistics.median(values), 2) if values else None


def build(state, out, run_ids=None, labels_path=None, include_synthetic=False):
    out = Path(out)
    rows, requests = collect(state, run_ids, include_synthetic)
    for r in rows:
        stem = f"{r['request_id']}__{r['candidate_id']}"
        r["image"] = f"images/{stem}.png" if r["image_artifact"] else None
        r["evidence"] = f"evidence/{stem}.json"
        if r["image_artifact"]:
            atomic_write(out / r["image"], state.read(r["image_artifact"]))
        _json(
            out / r["evidence"],
            {k: v for k, v in r.items() if k != "_record"} | {"evaluation_record": r["_record"]},
        )
    public = [{k: v for k, v in r.items() if k not in {"_record", "image_artifact"}} for r in rows]
    _json(out / "results.json", public)
    buffer = io.StringIO()
    fields = (
        [k for k in public[0] if k not in {"failed_checks", "unknown_checks", "evaluation_errors"}]
        + ["failed_checks", "unknown_checks"]
        if public
        else []
    )
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for r in public:
        writer.writerow(
            {
                **r,
                "failed_checks": " | ".join(r["failed_checks"]),
                "unknown_checks": " | ".join(r["unknown_checks"]),
            }
        )
    atomic_write(out / "results.csv", buffer.getvalue().encode())
    atomic_write(out / "requests.jsonl", b"".join(canonical(q) + b"\n" for q in requests))
    for q in requests:
        q["reference_files"] = []
        for sha in q.pop("reference_renditions"):
            atomic_write(out / "references" / f"{sha[:12]}.png", state.read(sha))
            q["reference_files"].append(f"references/{sha[:12]}.png")
    refs_by_run = {q["run_id"]: q["reference_files"] for q in requests}
    atomic_write(out / "labeling-sheet.html", labeling_sheet(public, refs_by_run).encode())
    template = io.StringIO()
    template_writer = csv.writer(template)
    template_writer.writerow(["run_id", "candidate_index", "dimension", "label", "labeler", "note"])
    for r in public:
        if r["image"]:
            for dim in LABEL_DIMENSIONS:
                template_writer.writerow([r["run_id"][:8], r["candidate_index"], dim, "", "", ""])
    atomic_write(out / "labels-template.csv", template.getvalue().encode())
    labels = read_labels(labels_path, rows)
    stats = agreement(labels)
    atomic_write(out / "contact-sheet.html", contact_sheet(public).encode())
    atomic_write(out / "report.md", report(public, requests, stats, len(labels)).encode())
    return {
        "requests": len(requests),
        "candidates": len(rows),
        "labels": len(labels),
        "out": str(out),
    }


def labeling_sheet(rows, refs_by_run):
    """Blind sheet for human labelling: inputs and images only, no automated verdicts or scores."""
    cards = []
    for r in rows:
        if not r["image"]:
            continue
        refs = "".join(f"<img class='ref' src='{p}'>" for p in refs_by_run.get(r["run_id"], []))
        copy = "".join(f"<li><code>{html.escape(t)}</code></li>" for t in r["selected_copy"] or [])
        cards.append(
            f"<div class='card'><img src='{r['image']}'><h3>{r['run_id'][:8]} · candidate {r['candidate_index']}</h3>"
            f"<p><b>{r['geography']} / {r['season']}</b> · text mode {r['text_mode']}</p>"
            f"<p>Source text:</p><pre>{html.escape(r['source_text'])}</pre><p>Copy that must appear exactly:</p><ul>{copy}</ul>"
            f"<p>Reference product:</p>{refs}</div>"
        )
    return (
        "<!doctype html><meta charset='utf-8'><title>Labeling sheet</title><style>body{font-family:system-ui;margin:16px}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:16px}.card{border:1px solid #ccc;border-radius:8px;padding:12px}"
        ".card>img{width:100%}.ref{height:90px;margin-right:6px}pre{white-space:pre-wrap;background:#f4f4f4;padding:6px}</style>"
        "<h1>Blind labeling sheet</h1><p>Label each candidate in labels.csv per dimension (overall, text_selection, "
        "text_rendering, product, context, region). Evaluator results are deliberately not shown.</p><div class='grid'>"
        + "".join(cards)
        + "</div>"
    )


def contact_sheet(rows):
    color = {"pass": "#1b7f3b", "fail": "#b3261e", "unknown": "#8a6d00", "not_evaluated": "#555"}
    cards = []
    for r in rows:
        dims = "".join(
            f"<li>{d}: <b style='color:{color.get(r[d + '_verdict'], '#555')}'>{r[d + '_verdict']}</b> ({r[d + '_score']})</li>"
            for d in DIMENSIONS
        )
        fails = "".join(f"<li>{html.escape(f)}</li>" for f in r["failed_checks"]) or "<li>none</li>"
        img = (
            f"<img src='{r['image']}' alt='{r['candidate_id']}'>"
            if r["image"]
            else f"<div class='missing'>no image: {html.escape(str(r['error_code']))}</div>"
        )
        badge = (
            "WINNER" + (" · APPROVED" if r["approved"] else " · not approved")
            if r["winner"]
            else ""
        )
        cards.append(
            f"<div class='card'>{img}<h3>{html.escape(r['request_id'])} · c{r['candidate_index']} <span class='badge'>{badge}</span></h3>"
            f"<p><b style='color:{color.get(r['overall_verdict'], '#555')}'>{r['overall_verdict'].upper()}</b> · score {r['overall_score']} · "
            f"{r['geography']}/{r['season']} · {r['text_mode']} · guardrail {r['guardrail_status']}</p><ul>{dims}</ul>"
            f"<p>Failed checks:</p><ul>{fails}</ul><p><a href='{r['evidence']}'>evidence</a></p></div>"
        )
    return (
        "<!doctype html><meta charset='utf-8'><title>Contact sheet</title><style>body{font-family:system-ui;margin:16px;background:#fafafa}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}.card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px}"
        ".card img{width:100%;border-radius:4px}.badge{font-size:12px;color:#1b5e9e}.missing{height:200px;display:flex;align-items:center;justify-content:center;background:#eee}"
        "li{font-size:13px}</style><h1>Generated candidates and evaluation results</h1><div class='grid'>"
        + "".join(cards)
        + "</div>"
    )


def _table(header, rows):
    return "\n".join(
        ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
        + ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    )


def report(rows, requests, stats, n_labels):
    evaluated = [r for r in rows if r["overall_verdict"] != "not_evaluated"]
    dim_rows = [
        [d, *(sum(r[f"{d}_verdict"] == v for r in evaluated) for v in ("pass", "fail", "unknown"))]
        for d in DIMENSIONS
    ]
    dim_rows.append(
        [
            "**overall**",
            *(
                sum(r["overall_verdict"] == v for r in evaluated)
                for v in ("pass", "fail", "unknown")
            ),
        ]
    )
    approved = sum(q["approved"] for q in requests)
    winners = [
        [
            r["request_id"],
            r["candidate_id"],
            r["overall_verdict"],
            r["overall_score"],
            "yes" if r["approved"] else "no",
            f"![]({r['image']})",
        ]
        for r in rows
        if r["winner"]
    ]
    successes = [r for r in evaluated if r["overall_verdict"] == "pass"][:3]
    failures = sorted(
        [r for r in evaluated if r["overall_verdict"] == "fail"],
        key=lambda r: -r["failed_required_checks"],
    )[:4]
    examples = (
        "\n\n".join(
            f"**{r['request_id']} · {r['candidate_id']} — {r['overall_verdict']}**\n\n![]({r['image']})\n\n"
            + (
                "Failed checks:\n" + "\n".join(f"- {f}" for f in r["failed_checks"])
                if r["failed_checks"]
                else "All required checks passed."
            )
            for r in successes + failures
        )
        or "_No evaluated candidates yet._"
    )
    label_rows = [
        [
            d,
            s["labelled"],
            s["abstained"],
            s["tp"],
            s["fp_false_reject"],
            s["fn_false_accept"],
            s["tn"],
            s["agreement"],
            s["cohens_kappa"],
        ]
        for d, s in stats.items()
    ]
    unknown_or_failed_exec = [
        r for r in rows if r["status"] != "evaluated" or r["execution_status"] != "ok"
    ]
    return f"""# Context-enriched ad generation with an automated evaluator

_Generated by `adgen report` from the local state store. Every number below is computed from `results.json`; nothing is hand-edited._

## 1. Summary

- Requests: **{len(requests)}** · candidates: **{len(rows)}** · evaluated: **{len(evaluated)}**
- Requests with an **approved** winner (winner passes every required check): **{approved}/{len(requests)}**
- Human-labelled judgments: **{n_labels}** (see §6)
- Country recognisable from the scene (diagnostic C-REGION, not a pass criterion): {_count(evaluated, "region_recognisable")}
- Median generation latency per candidate: {_median([r["generation_latency_s"] for r in rows])} s · median evaluation latency: {_median([r["evaluation_latency_s"] for r in rows])} s
- Estimated cost (report-only, from returned token usage): generation {round(sum(r["generation_cost_usd"] for r in rows), 3)} USD · evaluation judge {round(sum(r["evaluation_cost_usd"] for r in rows), 3)} USD · shared per-request {round(sum(q["shared_cost_usd"] for q in requests), 3)} USD

## 2. Architecture

Typed request (product photo(s), geography enum, season enum, freeform text with Exact/Extract policy) → reference normalization → frozen text plan (Exact in code; Extract = source spans chosen by an LLM, validated in code) → product analysis (OpenAI vision) → country/season resolution (code) → per candidate: creative plan (OpenAI; sees text roles and lengths, never the copy) → plan guardrails (keyword check + reviewer; one replan, then generate and flag) → prompt compiled in code → one Gemini 3.1 Flash Image call → output gate (square, ≤1024 px) → **evaluation** → ranking in code → best image exported. Every stage, artifact and model call is recorded in a SQLite state store, so runs resume and replay offline. Design: `docs/design/`.

## 3. Evaluation method

Verdicts are composed **in code**: any trusted required failure → fail; otherwise any unresolved check → unknown; otherwise pass. Models only supply measurements or atomic yes/no/unknown answers. Missing evidence is never a pass.

| Dimension | Required checks | Evidence |
|---|---|---|
| Text selection (source → copy) | S-SPANS, S-PROTECTED, S-CAPACITY, S-EXACT/S-FULL; Extract: SEL-MEANING, SEL-OMISSION, SEL-RELEVANCE | Code re-verification; judge failures must quote the source |
| Text rendering (copy → pixels) | R-BLOCKS (each block rendered exactly, one-to-one), R-EXTRA (no duplicated/unplanned copy), R-LEGIBLE (proxy; never fails alone) | Blind PaddleOCR PP-OCRv6; lines grouped spatially; product-label text excluded via detector box; CER/WER |
| Product (same object) | P1 exactly one (detector and judge must agree), P2 type, P3 shape, P4 colours/materials, P5 distinctive components, P6 branding (if legible in reference) | OpenAI judge sees references + ad; Grounding DINO for crop/count only; DINOv2 similarity is a non-required diagnostic. Position/orientation not scored |
| Context | C-SEASON, C-CONTRA, C-SETTING, image guardrails GR-* (C-REGION recognisability is reported, not required) | Same judge call; criteria from resolved context and static policy, never from the planner's own cues |

Scores rank candidates only: per dimension, mean over required checks (pass 1, unknown 0.5, fail 0); text rendering = mean max(0, 1 − CER); overall = unweighted mean. Ranking rule: verdict tier → failed required checks → score → guardrail status → index. A higher score never overrides a failed check.

## 4. Success criteria (set before these results)

Evaluator: (E1) no human-labelled failure is accepted (false accepts = 0); (E2) false rejects ≤ 20% of human-labelled passes; (E3) abstentions reported per dimension, not hidden. Pipeline: (G1) every published image is square and ≤1024 px (test-enforced); (G2) report approval yield and cost/latency honestly. Thresholds are provisional pilot values in `config/evaluator.toml`.

## 5. Results

{_table(["dimension", "pass", "fail", "unknown"], dim_rows)}

Execution status: {_count(evaluated, "execution_status")} · candidate status: {_count(rows, "status")} · guardrail status: {_count(rows, "guardrail_status")}

### Winners per request

{_table(["request", "candidate", "verdict", "score", "approved", "image"], winners) if winners else "_none_"}

### Representative successes and failures

{examples}

### Failures and unknowns (not hidden)

{_table(["candidate", "status", "execution", "unknown checks", "errors"], [[r["candidate_id"], r["status"], r["execution_status"], ", ".join(r["unknown_checks"]) or "-", ", ".join(r["evaluation_errors"]) or (r["error_code"] or "-")] for r in unknown_or_failed_exec]) if unknown_or_failed_exec else "_none_"}

## 6. Credibility check against human labels

Positive class = defect (fail). Unknown automated verdicts are abstentions and excluded from agreement. One annotator unless stated: no inter-rater agreement is claimed.

{_table(["dimension", "labelled", "abstained", "TP", "FP (false reject)", "FN (false accept)", "TN", "agreement", "kappa"], label_rows) if label_rows else "_No human labels supplied yet. Add rows to the labels CSV and rebuild._"}

## 7. Limitations

- Small, smoke-scale sample; counts matter more than percentages and nothing is statistically significant.
- The judge (OpenAI) is from a different family than the generator (Gemini) but the same family as the planner/reviewer; its answers are validated only against the labelled subset above.
- OCR cannot read stylised script logos; branding (P6) relies mainly on the judge.
- Thresholds (detector count, OCR confidence, legibility proxy) are provisional and not yet calibrated on a separate dev split.
- Country-level geography cues are approximations; the evaluator checks for contradictions and plausibility, not precise locale.
- Costs are estimates from returned token usage and configured list prices; provider dashboards are authoritative.

## 8. Reproducibility and agent disclosure

Inputs and settings: `requests.jsonl`. Per-candidate evidence (OCR lines, detections, judge answers, check reasons): `evidence/`. Images: `images/`. Offline replay: `adgen export-fixtures` then `adgen generate --fixtures`. Agent collaboration log: `docs/agent-collaboration.md`; decisions: `docs/decisions.md`.
"""
