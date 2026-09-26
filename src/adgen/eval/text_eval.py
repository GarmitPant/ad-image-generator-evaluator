"""Text evaluation: source -> selected copy (selection) and selected copy -> pixels (rendering)."""

from .compose import check
from .judge import SELECTION_QUESTIONS


def ws(text):
    return " ".join(text.split())


def levenshtein(a, b):
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def cer(expected, observed):
    return levenshtein(ws(expected), ws(observed)) / max(1, len(ws(expected)))


def wer(expected, observed):
    return levenshtein(ws(expected).split(), ws(observed).split()) / max(
        1, len(ws(expected).split())
    )


# ---------------------------------------------------------------- selection (source -> copy)


def selection_structural(contract, text_plan):
    """Independent re-verification of the frozen TextPlan against the stored source."""
    source, blocks = contract["source_text"], text_plan["blocks"]
    cursor, spans_ok = 0, True
    for b in blocks:
        if (
            b["start"] < cursor
            or b["end"] > len(source)
            or source[b["start"] : b["end"]] != b["text"]
        ):
            spans_ok = False
        cursor = b["end"]
    uncovered = [
        source[s["start"] : s["end"]]
        for s in contract["protected_spans"]
        if not any(b["start"] <= s["start"] and b["end"] >= s["end"] for b in blocks)
    ]
    visible = sum(sum(not c.isspace() for c in b["text"]) for b in blocks)
    words = sum(len(b["text"].split()) for b in blocks)
    cap = contract["capacity"]
    checks = [
        check(
            "S-SPANS",
            "pass" if spans_ok else "fail",
            "every block is an exact, ordered source span",
        ),
        check(
            "S-PROTECTED",
            "fail" if uncovered else "pass",
            "protected phrases kept whole",
            uncovered=uncovered,
        ),
        check(
            "S-CAPACITY",
            "pass"
            if len(blocks) <= cap["blocks"]
            and visible <= cap["visible_chars"]
            and words <= cap["words"]
            else "fail",
            "within rendering capacity",
            blocks=len(blocks),
            visible_chars=visible,
            words=words,
        ),
    ]
    if contract["mode"] == "exact":
        full = len(blocks) == 1 and blocks[0]["text"] == source
        checks.append(
            check("S-EXACT", "pass" if full else "fail", "Exact mode keeps the entire input")
        )
    return checks


def selection_semantic(contract, judgment):
    """Extract mode only. A failing answer must quote the source, else it is ungrounded -> unknown."""
    if judgment is None:
        return [check(q, "unknown", "judge unavailable") for q in SELECTION_QUESTIONS]
    answers = {a["question_id"]: a for a in judgment["answers"]}
    checks = []
    for qid, (_, passing) in SELECTION_QUESTIONS.items():
        a = answers.get(qid)
        if a is None or a["answer"] == "unknown":
            checks.append(check(qid, "unknown", "no answer" if a is None else "judge abstained"))
        elif a["answer"] == passing:
            checks.append(check(qid, "pass", "judge answered " + a["answer"]))
        elif a["evidence_quote"] and a["evidence_quote"] in contract["source_text"]:
            checks.append(
                check(qid, "fail", "judge answered " + a["answer"], quote=a["evidence_quote"])
            )
        else:
            checks.append(
                check(
                    qid,
                    "unknown",
                    "failing answer without a verifiable source quote",
                    quote=a["evidence_quote"],
                )
            )
    return checks


# ---------------------------------------------------------------- rendering (copy -> pixels)


def _inside(line, boxes):
    x = (line["box"][0] + line["box"][2]) / 2
    y = (line["box"][1] + line["box"][3]) / 2
    return any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in boxes)


def classify_lines(lines, product_boxes, cfg):
    ad, label, noise = [], [], []
    for line in lines:
        if _inside(line, product_boxes):
            label.append(line)  # product's own branding: judged under product fidelity
        elif line["score"] < cfg.ocr_noise:
            noise.append(line)
        else:
            ad.append(line)
    return ad, label, noise


def group_lines(lines, cfg):
    """Union lines that are vertically adjacent (gap <= k x height) and horizontally overlapping."""
    lines = sorted(lines, key=lambda ln: (ln["box"][1], ln["box"][0]))
    parent = list(range(len(lines)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(lines):
        for j in range(i + 1, len(lines)):
            b = lines[j]
            (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = a["box"], b["box"]
            gap = max(by0 - ay1, ay0 - by1)
            height = min(ay1 - ay0, by1 - by0)
            # Tall display type often yields slightly overlapping line boxes (negative gap).
            if -0.5 * height <= gap <= cfg.line_merge_gap * height and min(ax1, bx1) > max(
                ax0, bx0
            ):
                parent[find(j)] = find(i)
    groups = {}
    for i in range(len(lines)):
        groups.setdefault(find(i), []).append(lines[i])
    return [sorted(g, key=lambda ln: ln["box"][1]) for g in groups.values()]


def segments(groups, max_lines):
    out = []
    for g in groups:
        for start in range(len(g)):
            for end in range(start + 1, min(len(g), start + max_lines) + 1):
                run = g[start:end]
                out.append(
                    {
                        "lines": [id(ln) for ln in run],
                        "run": run,
                        "text": " ".join(ln["text"] for ln in run),
                    }
                )
    return out


def match(expected, segs, max_cer=0.5):
    """One-to-one assignment of expected blocks to disjoint line runs minimizing total CER."""
    options = [
        [
            (cer(e["text"], s["text"]), k)
            for k, s in enumerate(segs)
            if cer(e["text"], s["text"]) <= max_cer
        ]
        for e in expected
    ]
    best = [float("inf"), None]

    def dfs(i, used, cost, chosen):
        if cost >= best[0]:
            return
        if i == len(expected):
            best[:] = [cost, list(chosen)]
            return
        for c, k in sorted(options[i]):
            ids = set(segs[k]["lines"])
            if not ids & used:
                dfs(i + 1, used | ids, cost + c, chosen + [k])
        dfs(i + 1, used, cost + 1.0, chosen + [None])  # block missing

    dfs(0, frozenset(), 0.0, [])
    return best[1]


def rendering(text_plan, ocr_lines, product_boxes, cfg):
    expected = text_plan["blocks"]
    ad, label, noise = classify_lines(ocr_lines, product_boxes, cfg)
    segs = segments(group_lines(ad, cfg), cfg.max_block_lines)
    assignment = match(expected, segs)
    used, blocks = set(), []
    for block, k in zip(expected, assignment):
        if k is None:
            blocks.append(
                {
                    "block_id": block["block_id"],
                    "expected": block["text"],
                    "observed": None,
                    "cer": None,
                    "verdict": "fail",
                    "reason": "missing",
                }
            )
            continue
        run = segs[k]["run"]
        used |= set(segs[k]["lines"])
        observed = segs[k]["text"]
        c, confident = (
            cer(block["text"], observed),
            min(ln["score"] for ln in run) >= cfg.ocr_confident,
        )
        verdict = "pass" if c == 0 else ("fail" if confident else "unknown")
        blocks.append(
            {
                "block_id": block["block_id"],
                "expected": block["text"],
                "observed": observed,
                "cer": round(c, 4),
                "wer": round(wer(block["text"], observed), 4),
                "exact_strict": block["text"] == "\n".join(ln["text"] for ln in run),
                "min_score": min(ln["score"] for ln in run),
                "min_height_px": min(ln["box"][3] - ln["box"][1] for ln in run),
                "verdict": verdict,
                "reason": "exact (whitespace-equivalent)"
                if c == 0
                else ("altered" if confident else "low-confidence read"),
            }
        )
    leftovers = [
        ln for ln in ad if id(ln) not in used and sum(ch.isalnum() for ch in ln["text"]) >= 2
    ]
    extra_fail = [ln for ln in leftovers if ln["score"] >= cfg.ocr_confident]
    extra_unsure = [ln for ln in leftovers if ln["score"] < cfg.ocr_confident]
    duplicates = [
        ln["text"] for ln in extra_fail if any(cer(b["text"], ln["text"]) <= 0.2 for b in expected)
    ]
    block_verdicts = [b["verdict"] for b in blocks]
    matched = [b for b in blocks if b["observed"] is not None]
    legible = matched and all(
        b["min_score"] >= cfg.ocr_confident and b["min_height_px"] >= cfg.min_text_height_px
        for b in matched
    )
    checks = [
        check(
            "R-BLOCKS",
            "fail"
            if "fail" in block_verdicts
            else ("unknown" if "unknown" in block_verdicts else "pass"),
            "; ".join(
                f"'{b['expected']}' not found"
                if b["observed"] is None
                else f"expected '{b['expected']}', read '{b['observed']}' ({b['reason']})"
                for b in blocks
                if b["verdict"] != "pass"
            )
            or f"all {len(blocks)} copy block(s) found exactly once",
            blocks=blocks,
        ),
        check(
            "R-EXTRA",
            "fail" if extra_fail else ("unknown" if extra_unsure else "pass"),
            ("duplicated copy: " + "; ".join(duplicates))
            if duplicates
            else ("unplanned text: " + "; ".join(ln["text"] for ln in extra_fail))
            if extra_fail
            else ("uncertain extra text: " + "; ".join(ln["text"] for ln in extra_unsure))
            if extra_unsure
            else "no unplanned ad text",
            extra=[ln["text"] for ln in extra_fail],
            uncertain=[ln["text"] for ln in extra_unsure],
            duplicates=duplicates,
        ),
        check(
            "R-LEGIBLE",
            "pass" if legible else "unknown",
            "legibility proxy: confident reads and text height >= min_text_height_px (never fails on its own)",
        ),
    ]
    score = sum(max(0.0, 1 - b["cer"]) if b["cer"] is not None else 0.0 for b in blocks) / max(
        1, len(blocks)
    )
    diagnostics = {
        "exact_match_rate": sum(b["verdict"] == "pass" for b in blocks) / max(1, len(blocks)),
        "ocr_lines": {"ad": ad, "product_label": label, "noise": noise},
    }
    return checks, score, diagnostics
