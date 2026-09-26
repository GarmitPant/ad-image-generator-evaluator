import json

import pytest

from adgen.contracts import AdRequest
from adgen.demo import SyntheticProvider
from adgen.pipeline import Pipeline
from adgen.providers import ProviderResult, ReplayProvider
from adgen.state import Blocked
from adgen.util import canonical


class MutatingProvider(SyntheticProvider):
    def __init__(self, mutation):
        super().__init__()
        self.mutation = mutation
        self.counts = {}

    def invoke(self, invocation, references):
        result = super().invoke(invocation, references)
        purpose = invocation["purpose"]
        self.counts[purpose] = self.counts.get(purpose, 0) + 1
        return self.mutation(purpose, self.counts[purpose], result)


def test_end_to_end_exact_all_candidates_saved_and_resume_no_calls(run_pipeline, state, tmp_path):
    result, backend = run_pipeline()
    assert result["evaluation_performed"] is False and result["winner"] is None
    assert result["synthetic"] is True
    assert len(backend.calls) == 7  # profile + 2 x (plan, review, image); no Exact call
    directory = state.root / "exports" / result["run_id"]
    assert len(list(directory.glob("candidate-*.png"))) == 2
    assert not (directory / "best.png").exists()
    snapshot = json.loads((directory / "state-snapshot.json").read_text())
    assert snapshot["run"]["status"] == "succeeded"
    resumed, _ = run_pipeline(backend=backend, run_id=result["run_id"])
    assert resumed == result
    assert len(backend.calls) == 7
    assert all(c["status"] == "generated_unscored" for c in result["candidates"])
    tables = {r["name"] for r in state.rows("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "evaluation" not in tables and "selection" not in tables


def test_extract_and_multireference_order(run_pipeline, request_data, state):
    request_data["text"]["mode"] = "extract"
    request_data["product_images"] = ["ref3.png", "ref1.png", "ref2.png"]
    result, backend = run_pipeline(data=request_data)
    assert [x["purpose"] for x in backend.calls].count("extract") == 1
    image_calls = [x for x in backend.calls if x["purpose"] == "image"]
    assert all(len(x["reference_hashes"]) == 3 for x in image_calls)
    profile_call = next(x for x in backend.calls if x["purpose"] == "product_analysis")
    assert profile_call["reference_hashes"] == sorted(image_calls[0]["reference_hashes"])
    intake = state.one(
        "SELECT exec_id FROM stage_execution WHERE run_id=? AND stage='intake'", (result["run_id"],)
    )
    records, _ = state._stage_result(intake["exec_id"])
    assert image_calls[0]["reference_hashes"] == [
        r["rendition_sha256"] for r in records["references"]
    ]


def test_planner_never_sees_copy_compiler_keeps_literal(run_pipeline, request_data):
    request_data["text"]["source_text"] = "PURPLE_UNICORN_9382"
    _, backend = run_pipeline(data=request_data)
    for call in backend.calls:
        if call["purpose"] == "plan":
            assert "PURPLE_UNICORN_9382" not in call["prompt"]
        if call["purpose"] == "image":
            assert "PURPLE_UNICORN_9382" in call["prompt"]
            assert "Synthetic fixture only; not a real creative decision." not in call["prompt"]


def test_replay_record_match_and_no_fallback(
    run_pipeline, tmp_path, state, config, policy, request_data
):
    fixture_dir = tmp_path / "fixtures"
    result, _ = run_pipeline(backend=SyntheticProvider(fixture_dir))
    # A separate store ensures every call is served by exact-match disk fixtures, not stage caching.
    from adgen.state import State

    other = State(tmp_path / "other/state.db")
    try:
        replayed = Pipeline(other, config, policy, ReplayProvider(fixture_dir)).run(
            AdRequest.model_validate(request_data), tmp_path
        )
        assert replayed["status"] == result["status"]
        assert replayed["synthetic"]
    finally:
        other.close()
    with pytest.raises(Blocked, match="missing"):
        ReplayProvider(tmp_path / "empty").invoke({"anything": "different"}, [])


def test_one_candidate_failure_does_not_stop_others(run_pipeline):
    def mutation(purpose, count, result):
        if purpose == "image" and count == 1:
            return ProviderResult(
                metadata={"error_code": "image_refused", "provenance": "synthetic"}
            )
        return result

    result, _ = run_pipeline(backend=MutatingProvider(mutation))
    assert [c["status"] for c in result["candidates"]] == ["failed", "generated_unscored"]


def test_keyword_overrides_approval_replan_then_generate_flagged(run_pipeline, request_data):
    request_data["n_candidates"] = 1

    def mutation(purpose, count, result):
        if purpose == "plan":
            plan = json.loads(result.text)
            plan["setting"] = "A tabletop near a temple"
            result.text = canonical(plan).decode()
        return result

    backend = MutatingProvider(mutation)
    result, _ = run_pipeline(backend=backend, data=request_data)
    assert backend.counts == {"product_analysis": 1, "plan": 2, "review": 2, "image": 1}
    assert result["candidates"][0]["guardrail_status"] == "rejected_after_replan"
    assert result["candidates"][0]["status"] == "generated_unscored"


def test_rejected_first_plan_can_be_approved_after_replan(run_pipeline, request_data):
    request_data["n_candidates"] = 1

    def mutation(purpose, count, result):
        if purpose == "review" and count == 1:
            result.text = canonical(
                {
                    "verdict": "reject",
                    "reasons": [{"rule_id": "GR-STEREO", "explanation": "Change the setting"}],
                }
            ).decode()
        return result

    result, backend = run_pipeline(backend=MutatingProvider(mutation), data=request_data)
    assert result["candidates"][0]["guardrail_status"] == "approved"
    assert backend.counts["plan"] == 2


def test_invalid_plan_twice_never_generates(run_pipeline, request_data):
    request_data["n_candidates"] = 1

    def mutation(purpose, count, result):
        if purpose == "plan":
            result.text = '{"invalid":"schema"}'
        return result

    result, backend = run_pipeline(backend=MutatingProvider(mutation), data=request_data)
    assert backend.counts == {"product_analysis": 1, "plan": 2}
    assert result["candidates"][0]["error_code"] == "creative_plan_invalid_twice"
    resumed, _ = run_pipeline(backend=backend, data=request_data, run_id=result["run_id"])
    assert resumed == result


def test_bad_extraction_aborts_before_analysis(run_pipeline, request_data):
    request_data["text"]["mode"] = "extract"

    def mutation(purpose, count, result):
        result.text = canonical(
            {"blocks": [{"start": 0, "end": 2, "text": "NO", "role": "tagline"}]}
        ).decode()
        return result

    backend = MutatingProvider(mutation)
    with pytest.raises(ValueError):
        run_pipeline(backend=backend, data=request_data)
    assert len(backend.calls) == 1


def test_reference_set_cache_is_order_independent(run_pipeline, request_data):
    request_data["product_images"] = ["ref1.png", "ref2.png"]
    _, backend = run_pipeline(data=request_data)
    request_data["product_images"].reverse()
    _, second = run_pipeline(data=request_data)
    assert any(c["purpose"] == "product_analysis" for c in backend.calls)
    assert not any(c["purpose"] == "product_analysis" for c in second.calls)


def test_artifact_corruption_blocks_resume(run_pipeline, state):
    result, backend = run_pipeline()
    sha = result["candidates"][0]["image_artifact"]
    path = state.root / state.one("SELECT path FROM artifact WHERE artifact_id=?", (sha,))["path"]
    path.write_bytes(b"corrupted")
    with pytest.raises(Blocked):
        run_pipeline(backend=backend, run_id=result["run_id"])


def test_changed_request_cannot_resume(run_pipeline, request_data):
    result, _ = run_pipeline()
    request_data["season"] = "winter"
    with pytest.raises(Blocked, match="changed"):
        run_pipeline(data=request_data, run_id=result["run_id"])


def test_resume_partial_failure_does_not_resend(run_pipeline):
    def mutation(purpose, count, result):
        if purpose == "image" and count == 1:
            return ProviderResult(
                metadata={"error_code": "image_refused", "provenance": "synthetic"}
            )
        return result

    backend = MutatingProvider(mutation)
    result, _ = run_pipeline(backend=backend)
    count = len(backend.calls)
    resumed, _ = run_pipeline(backend=backend, run_id=result["run_id"])
    assert resumed == result
    assert len(backend.calls) == count


def test_keyword_does_not_scan_avoid_or_rationale(run_pipeline, request_data):
    request_data["n_candidates"] = 1

    def mutation(purpose, count, result):
        if purpose == "plan":
            plan = json.loads(result.text)
            plan["avoid"] = ["snow", "temple", "flags"]
            plan["rationale"] = "Avoid temple and flags. No snow."
            result.text = canonical(plan).decode()
        return result

    result, backend = run_pipeline(backend=MutatingProvider(mutation), data=request_data)
    assert backend.counts["plan"] == 1
    assert result["candidates"][0]["guardrail_status"] == "approved"


def test_no_live_backend_allowed_in_replay(state, config, policy):
    from adgen.providers import LiveProvider

    with pytest.raises(Blocked, match="forbidden"):
        Pipeline(state, config, policy, LiveProvider(config), "replay")


def test_nonfinite_budget_rejected(run_pipeline):
    with pytest.raises(Blocked, match="finite"):
        run_pipeline(budget=float("nan"))


def test_invalid_plan_can_recover_on_second_attempt(run_pipeline, request_data):
    request_data["n_candidates"] = 1

    def mutation(purpose, count, result):
        if purpose == "plan" and count == 1:
            plan = json.loads(result.text)
            plan["text_layout"][0]["zone"] = plan["product_placement"]["zone"]
            result.text = canonical(plan).decode()
        return result

    result, backend = run_pipeline(backend=MutatingProvider(mutation), data=request_data)
    assert backend.counts == {"product_analysis": 1, "plan": 2, "review": 1, "image": 1}
    assert result["candidates"][0]["status"] == "generated_unscored"


def test_export_receipts_can_replay_identical_candidate_prompts(
    run_pipeline, state, tmp_path, config, policy, request_data
):
    from adgen.providers import export_fixtures
    from adgen.state import State

    result, _ = run_pipeline()
    directory = tmp_path / "exported-fixtures"
    assert export_fixtures(state, result["run_id"], directory) == 7
    assert len(list(directory.glob("*.json"))) == 7
    other = State(tmp_path / "fresh/state.db")
    try:
        replay = Pipeline(other, config, policy, ReplayProvider(directory)).run(
            AdRequest.model_validate(request_data), tmp_path
        )
        assert replay["status"] == "generated_unscored"
    finally:
        other.close()


def test_cached_synthetic_analysis_provenance_propagates(run_pipeline, state, tmp_path):
    from adgen.providers import export_fixtures

    run_pipeline()

    def mutation(purpose, count, response):
        response.metadata["provenance"] = "recorded"
        return response

    result, backend = run_pipeline(backend=MutatingProvider(mutation))
    assert not any(c["purpose"] == "product_analysis" for c in backend.calls)
    assert result["synthetic"] is True
    assert export_fixtures(state, result["run_id"], tmp_path / "with-cached-analysis") == 7
