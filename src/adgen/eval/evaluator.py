"""Evaluates one candidate from recorded evidence. Evidence failures become unknown, never pass."""

import time

from ..state import failure
from ..util import digest
from .compose import POINTS, check, compose, dimension
from .judge import (
    DIAGNOSTIC,
    SelectionJudgment,
    VisualJudgment,
    selection_prompt,
    visual_prompt,
    visual_questions,
)
from .text_eval import rendering, selection_semantic, selection_structural
from .vision import png, to_image

VERSION = "eval-record/1"


def detector_label(profile):
    return profile["category"].strip().lower().rstrip(".") + "."


def _counted(boxes, cfg):
    return sorted(
        (b for b in boxes if b["score"] >= cfg.detector_count_threshold), key=lambda b: -b["score"]
    )


def _cosine(a, b):
    return round(sum(x * y for x, y in zip(a, b)), 4)


class Evaluator:
    def __init__(self, state, llm, vision, config, policy):
        self.state, self.llm, self.vision, self.config, self.policy = (
            state,
            llm,
            vision,
            config,
            policy,
        )

    # ------------------------------------------------------------------ request level
    def selection(self, exec_id, contract, text_plan):
        checks, errors = selection_structural(contract, text_plan), []
        if contract["mode"] == "extract":
            try:
                judgment = self.llm.structured(
                    exec_id,
                    "judge_selection",
                    selection_prompt(contract, text_plan),
                    SelectionJudgment,
                    self.config.judge_effort,
                )
            except Exception as exc:
                judgment, errors = None, [failure(exc)[1]]
            checks += selection_semantic(contract, judgment)
        else:
            checks.append(
                check(
                    "S-FULL",
                    "pass",
                    "Exact mode: the whole input is the copy; no selection to judge",
                )
            )
        return {**dimension(checks), "errors": errors}

    def references(self, exec_id, reference_hashes, profile):
        """Detect, crop and embed each reference once per request."""
        out, errors = [], []
        for sha in reference_hashes:
            try:
                data = self.state.read(sha)
                boxes = _counted(
                    self.vision.run(exec_id, "detect", data, {"label": detector_label(profile)})[
                        "boxes"
                    ],
                    self.config,
                )
                crop = png(to_image(data).crop(boxes[0]["box"])) if boxes else data
                vector = self.vision.run(exec_id, "embed", crop)["vector"]
                out.append(
                    {"reference": sha, "box": boxes[0]["box"] if boxes else None, "vector": vector}
                )
            except Exception as exc:
                errors.append(failure(exc)[1])
        return {"references": out, "errors": errors}

    # ------------------------------------------------------------------ candidate level
    def candidate(
        self,
        exec_id,
        image_sha,
        *,
        profile,
        context,
        text_plan,
        selection,
        references,
        reference_hashes,
        guardrail_status,
    ):
        started, errors, cfg = (
            time.time(),
            list(selection["errors"]) + list(references["errors"]),
            self.config,
        )
        image = self.state.read(image_sha)

        def collect(fn, *args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                errors.append(failure(exc)[1])
                return None

        with to_image(image) as picture:
            width, height = picture.size
        gates = dimension(
            [
                check("G-DECODE", "pass", "image decodes", sha256=digest(image)),
                check(
                    "G-SIZE",
                    "pass" if width == height and max(width, height) <= 1024 else "fail",
                    "square and long edge <= 1024",
                    size=[width, height],
                ),
            ]
        )
        detected = collect(
            self.vision.run, exec_id, "detect", image, {"label": detector_label(profile)}
        )
        boxes = _counted(detected["boxes"], cfg) if detected else []
        ocr = collect(self.vision.run, exec_id, "ocr", image)
        if ocr is None:
            text_rendering = {
                **dimension([check("R-BLOCKS", "unknown", "OCR unavailable")], score=0.0),
                "diagnostics": {},
            }
        else:
            r_checks, r_score, r_diag = rendering(
                text_plan, ocr["lines"], [b["box"] for b in boxes], cfg
            )
            text_rendering = {**dimension(r_checks, r_score), "diagnostics": r_diag}

        # Identity similarity (diagnostic until calibrated): best match over reference crops.
        similarity = None
        if boxes and references["references"]:
            crop = png(to_image(image).crop(boxes[0]["box"]))
            embedded = collect(self.vision.run, exec_id, "embed", crop)
            if embedded:
                per_ref = {
                    r["reference"]: _cosine(embedded["vector"], r["vector"])
                    for r in references["references"]
                }
                similarity = {"best": max(per_ref.values()), "per_reference": per_ref}

        questions = visual_questions(profile, context, self.policy)
        judged = collect(
            self.llm.structured,
            exec_id,
            "judge_visual",
            visual_prompt(len(reference_hashes), questions),
            VisualJudgment,
            cfg.judge_effort,
            [*reference_hashes, image_sha],
        )
        answers = {a["question_id"]: a for a in (judged or {}).get("answers", [])}

        def from_judge(qid):
            question, passing = questions[qid]
            a = answers.get(qid)
            required = qid not in DIAGNOSTIC
            if a is None or a["answer"] == "unknown":
                reason = "judge unavailable" if judged is None else "no answer/abstained"
                return check(qid, "unknown", reason, required, question=question)
            verdict = "pass" if a["answer"] == passing else "fail"
            return check(
                qid, verdict, a["evidence"], required, question=question, answer=a["answer"]
            )

        judge_count = judged["product_count"] if judged else None
        detector_count = len(boxes) if detected else None
        if judge_count == 1 and detector_count and detector_count >= 1:
            p1 = "pass"
        elif (
            judge_count is not None
            and detector_count is not None
            and (
                (judge_count == 0 and detector_count == 0)
                or (judge_count >= 2 and detector_count >= 2)
            )
        ):
            p1 = "fail"
        else:
            p1 = "unknown"
        product_checks = [
            check(
                "P1",
                p1,
                "exactly one product; detector and judge must agree",
                judge_count=judge_count,
                detector_count=detector_count,
                boxes=boxes,
            ),
            *[from_judge(q) for q in ("P2", "P3", "P4", "P5", "P6") if q in questions],
            check(
                "P-SIM",
                "pass" if similarity else "unknown",
                f"DINOv2 cosine similarity to the closest reference: {similarity['best']}"
                if similarity
                else "no product crop to compare",
                required=False,
                similarity=similarity,
            ),
        ]
        context_checks = [from_judge(q) for q in questions if not q.startswith("P")]
        dims = {
            "gates": gates,
            "text_selection": {k: v for k, v in selection.items() if k != "errors"},
            "text_rendering": text_rendering,
            "product": dimension(product_checks),
            "context": dimension(context_checks),
        }
        failed = sum(
            c["verdict"] == "fail" and c["required"] for d in dims.values() for c in d["checks"]
        )
        scored = ("text_selection", "text_rendering", "product", "context")
        return {
            "version": VERSION,
            "evaluator_version": cfg.version,
            "image_sha256": image_sha,
            "guardrail_status": guardrail_status,
            **dims,
            "overall_verdict": compose(
                [{"verdict": d["verdict"], "required": True} for d in dims.values()]
            ),
            "overall_score": round(sum(dims[k]["score"] for k in scored) / len(scored), 4),
            "failed_required_checks": failed,
            "execution_status": "ok"
            if not errors
            else ("failed" if judged is None and ocr is None else "degraded"),
            "errors": sorted(set(errors)),
            "judge_product_count": judge_count,
            "latency_s": round(time.time() - started, 2),
            "score_definition": "per dimension: mean over required checks (pass 1, unknown 0.5, fail 0); text_rendering: mean max(0, 1-CER) per block; overall: unweighted mean. Ranking only; verdicts gate.",
            "points": POINTS,
        }
