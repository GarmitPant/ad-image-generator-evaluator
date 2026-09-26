"""Evaluator composition on genuine recorded OCR/detection evidence with scripted (synthetic) judge answers."""

import json

import pytest

from adgen.eval.compose import rank
from adgen.eval.config import EvaluatorConfig
from adgen.eval.evaluator import Evaluator
from adgen.eval.judge import visual_questions
from adgen.eval.vision import SyntheticVision, VisionGateway
from adgen.state import StageFailed

from .helpers import ROOT, open_exec
from .test_eval_text import EVIDENCE, LIVE

POLICY = __import__("adgen.config", fromlist=["load_policy"]).load_policy(
    ROOT / "policy/guardrails.yaml"
)
PROFILE = json.loads((LIVE / "product-profile.json").read_text())
CONTEXT = json.loads((LIVE / "resolved-context.json").read_text())
PLAN = json.loads((LIVE / "text-plan.json").read_text())


class ScriptedJudge:
    """Stands in for the OpenAI judge; answers are synthetic, labelled as such."""

    def __init__(self, count=1, overrides=None, fail=False):
        self.count, self.overrides, self.fail, self.calls = count, overrides or {}, fail, []

    def structured(self, exec_id, purpose, prompt, schema, effort, refs=()):
        self.calls.append((purpose, prompt, list(refs)))
        if self.fail:
            raise StageFailed("llm_incomplete_or_refused")
        questions = visual_questions(PROFILE, CONTEXT, POLICY)
        answers = [
            {"question_id": q, "answer": self.overrides.get(q, passing), "evidence": "scripted"}
            for q, (_, passing) in questions.items()
        ]
        return {"product_count": self.count, "answers": answers}


def evaluate(state, candidate, judge):
    cfg = EvaluatorConfig.load(ROOT / "config/evaluator.toml")
    exec_id = open_exec(state)
    ev = EVIDENCE["candidates"][candidate]
    lines = [(ln["text"], ln["score"], ln["box"]) for ln in ev["ocr"]["lines"]]
    vision = VisionGateway(state, SyntheticVision(lines, ev["detect"]["boxes"]), cfg)
    evaluator = Evaluator(state, judge, vision, cfg, POLICY)
    image = state.artifact((LIVE / f"candidates/{candidate}/image.png").read_bytes(), "image")
    ref = state.artifact(b"reference-rendition", "reference_rendition")
    selection = {"verdict": "pass", "score": 1.0, "checks": [], "errors": []}
    references = {
        "references": [{"reference": ref, "box": [0, 0, 1, 1], "vector": [1.0, 0.0, 0.0]}],
        "errors": [],
    }
    return evaluator.candidate(
        exec_id,
        image,
        profile=PROFILE,
        context=CONTEXT,
        text_plan=PLAN,
        selection=selection,
        references=references,
        reference_hashes=[ref],
        guardrail_status="approved",
    )


def test_good_candidate_passes_and_judge_is_blind_to_copy(state):
    judge = ScriptedJudge()
    record = evaluate(state, "c1", judge)
    assert record["overall_verdict"] == "pass" and record["failed_required_checks"] == 0
    assert record["product"]["verdict"] == "pass" and record["context"]["verdict"] == "pass"
    purpose, prompt, refs = judge.calls[0]
    assert purpose == "judge_visual" and len(refs) == 2
    assert all(
        b["text"] not in prompt for b in PLAN["blocks"]
    )  # expected copy never shown to the judge


def test_duplicated_copy_fails_overall_despite_perfect_scene(state):
    record = evaluate(state, "c2", ScriptedJudge())
    assert record["text_rendering"]["verdict"] == "fail"
    assert record["overall_verdict"] == "fail" and record["failed_required_checks"] == 1


def test_judge_outage_is_unknown_not_pass(state):
    record = evaluate(state, "c1", ScriptedJudge(fail=True))
    assert record["product"]["verdict"] == "unknown" and record["context"]["verdict"] == "unknown"
    assert record["overall_verdict"] == "unknown" and record["execution_status"] == "degraded"


@pytest.mark.parametrize("count,expected", [(0, "unknown"), (2, "unknown"), (1, "pass")])
def test_product_presence_requires_detector_and_judge_agreement(state, count, expected):
    record = evaluate(state, "c1", ScriptedJudge(count=count))
    p1 = [c for c in record["product"]["checks"] if c["id"] == "P1"][0]
    assert p1["verdict"] == expected


def test_wrong_brand_and_guardrail_violation_fail(state):
    record = evaluate(state, "c1", ScriptedJudge(overrides={"P6": "no", "GR-TOKEN": "yes"}))
    failed = {
        c["id"]
        for d in ("product", "context")
        for c in record[d]["checks"]
        if c["verdict"] == "fail"
    }
    assert failed == {"P6", "GR-TOKEN"} and record["overall_verdict"] == "fail"


def test_ranking_verdict_gates_score():
    ev = lambda v, f, s: {"overall_verdict": v, "failed_required_checks": f, "overall_score": s}  # noqa: E731
    ranked = rank(
        [
            {
                "candidate_index": 1,
                "guardrail_status": "approved",
                "evaluation": ev("fail", 1, 0.99),
            },
            {
                "candidate_index": 2,
                "guardrail_status": "approved",
                "evaluation": ev("pass", 0, 0.80),
            },
            {
                "candidate_index": 3,
                "guardrail_status": "approved",
                "evaluation": ev("unknown", 0, 0.95),
            },
            {"candidate_index": 4, "guardrail_status": "approved", "evaluation": None},
        ]
    )
    assert [r["candidate_index"] for r in ranked] == [2, 3, 1, 4]
