from adgen.contracts import AdRequest
from adgen.demo import SyntheticProvider
from adgen.eval.config import EvaluatorConfig
from adgen.eval.vision import SyntheticVision
from adgen.pipeline import Pipeline, export_run
from adgen.state import StageFailed

from .helpers import ROOT

GENERATION_PURPOSES = {"product_analysis", "extract", "plan", "review", "image"}


def evaluation(ocr_text="Fresh every day"):
    config = EvaluatorConfig.load(ROOT / "config/evaluator.toml")
    return config, SyntheticVision([(ocr_text, 0.99, (100, 40, 900, 120))])


def run(state, config, policy, request_data, tmp_path, backend=None, evaluate=True, **kwargs):
    backend = backend or SyntheticProvider()
    pipe = Pipeline(state, config, policy, backend, "replay", evaluation() if evaluate else None)
    return pipe.run(AdRequest.model_validate(request_data), tmp_path, **kwargs), backend


def test_every_candidate_evaluated_ranked_and_best_exported(
    state, config, policy, request_data, tmp_path
):
    summary, backend = run(state, config, policy, request_data, tmp_path)
    assert summary["status"] == "evaluated" and summary["winner"] == 1 and summary["approved"]
    assert [c["status"] for c in summary["candidates"]] == ["evaluated", "evaluated"]
    snapshot = state.inspect(summary["run_id"])
    assert len(snapshot["evaluations"]) == 2 and snapshot["selection"]["winner_index"] == 1
    judges = [c["purpose"] for c in backend.calls if c["purpose"].startswith("judge")]
    assert judges == ["judge_visual", "judge_visual"]  # Exact mode: no selection judge call
    assert (state.root / "exports" / summary["run_id"] / "best.png").exists()


def test_existing_generation_only_run_is_evaluated_without_regenerating(
    state, config, policy, request_data, tmp_path
):
    first, backend = run(state, config, policy, request_data, tmp_path, evaluate=False)
    assert first["status"] == "generated_unscored"
    generation_calls = len(backend.calls)
    second, _ = run(
        state, config, policy, request_data, tmp_path, backend=backend, run_id=first["run_id"]
    )
    new = [c["purpose"] for c in backend.calls[generation_calls:]]
    assert new and not GENERATION_PURPOSES & set(new)  # only judge calls were made
    assert second["status"] == "evaluated" and second["winner"] is not None
    export_run(state, first["run_id"])  # evaluated export is preferred over the older one


def test_failed_candidate_ranks_last(state, config, policy, request_data, tmp_path):
    class FailFirstImage(SyntheticProvider):
        def invoke(self, invocation, references):
            if invocation["purpose"] == "image" and invocation["sample"]["candidate_index"] == 1:
                raise StageFailed("image_refused")
            return super().invoke(invocation, references)

    summary, _ = run(state, config, policy, request_data, tmp_path, backend=FailFirstImage())
    assert summary["winner"] == 2
    assert [r["candidate_index"] for r in summary["ranking"]] == [2, 1]
    assert summary["ranking"][1]["overall_verdict"] is None


def test_evaluator_crash_keeps_image_and_marks_evaluation_failed(
    state, config, policy, request_data, tmp_path, monkeypatch
):
    def boom(*args, **kwargs):
        raise RuntimeError("bug")

    monkeypatch.setattr("adgen.eval.evaluator.Evaluator.candidate", boom)
    summary, _ = run(state, config, policy, request_data, tmp_path)
    assert {c["status"] for c in summary["candidates"]} == {"evaluation_failed"}
    assert all(c["image_artifact"] for c in summary["candidates"])
    assert summary["winner"] is None and summary["approved"] is False
