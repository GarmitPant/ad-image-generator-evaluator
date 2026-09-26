import copy
import json

import pytest

from adgen.contracts import CopySelection, TextInput
from adgen.eval.config import EvaluatorConfig
from adgen.eval.text_eval import cer, rendering, selection_semantic, selection_structural
from adgen.text import freeze_selection, source_contract

from .helpers import ROOT

LIVE = ROOT / "data/live-runs/2026-09-26-rayban-au-summer-extract"
EVIDENCE = json.loads((ROOT / "tests/fixtures/rayban_live_evidence.json").read_text())


@pytest.fixture
def cfg():
    return EvaluatorConfig.load(ROOT / "config/evaluator.toml")


@pytest.fixture
def plan():
    return json.loads((LIVE / "text-plan.json").read_text())


def render(candidate, plan, cfg, mutate=None):
    ev = copy.deepcopy(EVIDENCE["candidates"][candidate])
    if mutate:
        mutate(ev["ocr"]["lines"])
    boxes = [b["box"] for b in ev["detect"]["boxes"] if b["score"] >= cfg.detector_count_threshold]
    checks, score, diag = rendering(plan, ev["ocr"]["lines"], boxes, cfg)
    return {c["id"]: c for c in checks}, score, diag


def test_live_positive_candidate_passes_with_wrapped_lines(plan, cfg):
    checks, score, diag = render("c1", plan, cfg)
    assert {k: c["verdict"] for k, c in checks.items()} == {
        "R-BLOCKS": "pass",
        "R-EXTRA": "pass",
        "R-LEGIBLE": "pass",
    }
    assert score == 1.0
    # "Built for" / "bright days." are two OCR lines of one block; the script logo is product branding.
    assert [ln["text"] for ln in diag["ocr_lines"]["product_label"]] == ["PorBum P"]


def test_live_duplicated_copy_is_caught(plan, cfg):
    checks, score, _ = render("c2", plan, cfg)
    assert checks["R-BLOCKS"]["verdict"] == "pass"
    assert checks["R-EXTRA"]["verdict"] == "fail"
    assert checks["R-EXTRA"]["evidence"]["duplicates"] == ["Built for bright days."]


def test_confident_numeric_substitution_fails(plan, cfg):
    def swap(lines):
        for ln in lines:
            ln["text"] = ln["text"].replace("30 days", "31 days")

    checks, score, _ = render("c1", plan, cfg, swap)
    assert checks["R-BLOCKS"]["verdict"] == "fail"
    block = [b for b in checks["R-BLOCKS"]["evidence"]["blocks"] if b["block_id"] == "t4"][0]
    assert block["reason"] == "altered" and 0 < block["cer"] < 0.05 and score < 1


def test_low_confidence_difference_is_unknown_not_fail(plan, cfg):
    def blur(lines):
        for ln in lines:
            if ln["text"].startswith("Free"):
                ln["text"], ln["score"] = ln["text"].replace("30", "3O"), 0.6

    checks, _, _ = render("c1", plan, cfg, blur)
    assert checks["R-BLOCKS"]["verdict"] == "unknown"


def test_missing_block_fails_and_one_line_cannot_serve_two_blocks(plan, cfg):
    doubled = copy.deepcopy(plan)
    doubled["blocks"].append({**doubled["blocks"][2], "block_id": "t5"})  # needs two occurrences
    checks, _, _ = render("c1", doubled, cfg)
    missing = [b for b in checks["R-BLOCKS"]["evidence"]["blocks"] if b["reason"] == "missing"]
    assert checks["R-BLOCKS"]["verdict"] == "fail" and len(missing) == 1
    checks2, _, _ = render("c2", doubled, cfg)  # c2 really shows it twice
    assert checks2["R-BLOCKS"]["verdict"] == "pass" and checks2["R-EXTRA"]["verdict"] == "pass"


def test_cer_is_not_clipped():
    assert cer("ab", "abcdef") == 2.0


def contract_and_plan(mode, text, protected=(), blocks=None):
    contract = source_contract(
        TextInput(mode=mode, source_text=text, protected_phrases=list(protected))
    )
    selection = CopySelection(
        blocks=blocks or [{"start": 0, "end": len(text), "text": text, "role": "tagline"}]
    )
    return contract, freeze_selection(contract, selection)


def test_selection_structural_detects_tampered_plan():
    contract, plan = contract_and_plan(
        "extract",
        "Not waterproof. Great grip.",
        ["Great grip."],
        [{"start": 16, "end": 27, "text": "Great grip.", "role": "tagline"}],
    )
    assert all(c["verdict"] == "pass" for c in selection_structural(contract, plan))
    tampered = copy.deepcopy(plan)
    tampered["blocks"][0]["text"] = "Great grips"
    verdicts = {c["id"]: c["verdict"] for c in selection_structural(contract, tampered)}
    assert verdicts["S-SPANS"] == "fail"


def test_semantic_failure_needs_a_real_source_quote():
    contract, _ = contract_and_plan("extract", "Not waterproof. Great grip.")
    judged = {
        "answers": [
            {"question_id": "SEL-MEANING", "answer": "no", "evidence_quote": "Not waterproof"},
            {"question_id": "SEL-OMISSION", "answer": "yes", "evidence_quote": "invented words"},
            {"question_id": "SEL-RELEVANCE", "answer": "yes", "evidence_quote": ""},
        ]
    }
    verdicts = {c["id"]: c["verdict"] for c in selection_semantic(contract, judged)}
    assert verdicts == {"SEL-MEANING": "fail", "SEL-OMISSION": "unknown", "SEL-RELEVANCE": "pass"}
    assert {c["verdict"] for c in selection_semantic(contract, None)} == {"unknown"}
