import json
import sqlite3

import pytest

from adgen.contracts import AdRequest
from adgen.demo import SyntheticProvider
from adgen.pipeline import Pipeline
from adgen.state import Blocked, State


def test_foreign_keys_wal_and_future_schema_refusal(state, tmp_path):
    assert state.db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert state.db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    state.write("UPDATE schema_version SET version=99")
    with pytest.raises(Blocked, match="schema"):
        State(state.path)


def test_shared_stage_uniqueness_and_lock(run_pipeline, state):
    summary, _ = run_pipeline()
    run_id = summary["run_id"]
    row = state.one("SELECT * FROM stage_execution WHERE run_id=? AND stage='intake'", (run_id,))
    with pytest.raises(sqlite3.IntegrityError):
        state.write(
            "INSERT INTO stage_execution(exec_id,run_id,stage,candidate_index,attempt,status,input_hashes,input_fingerprint,started_at) VALUES('duplicate',?,'intake',0,1,'running','{}','x','now')",
            (run_id,),
        )
    other = State(state.path)
    with state.lock(run_id):
        with pytest.raises(Blocked, match="locked"):
            with other.lock(run_id):
                pass
    other.close()
    assert row["candidate_index"] == 0
    assert state.one("SELECT lock_owner FROM run WHERE run_id=?", (run_id,))["lock_owner"] is None


def test_dispatch_committed_before_backend_and_budget_bound(run_pipeline, state, request_data):
    class InspectingBackend(SyntheticProvider):
        def invoke(self, invocation, references):
            connection = sqlite3.connect(state.path)
            try:
                assert (
                    connection.execute(
                        "SELECT count(*) FROM model_call WHERE status='dispatched'"
                    ).fetchone()[0]
                    == 1
                )
                assert connection.execute("SELECT cost_est_usd FROM run").fetchone()[0] == 0.12
            finally:
                connection.close()
            return super().invoke(invocation, references)

    summary, backend = run_pipeline(backend=InspectingBackend(), mode="live", budget=0.13)
    assert len(backend.calls) == 1
    assert summary["status"] == "no_usable_candidates"
    assert all(c["error_code"] == "budget_reservation_exceeded" for c in summary["candidates"])
    assert state.inspect(summary["run_id"])["run"]["cost_est_usd"] == 0.12


def test_crash_after_dispatch_never_automatically_resends(
    state, config, policy, request_data, tmp_path
):
    class InterruptingBackend:
        def invoke(self, invocation, references):
            raise KeyboardInterrupt()

    pipeline = Pipeline(state, config, policy, InterruptingBackend(), "live")
    with pytest.raises(KeyboardInterrupt):
        pipeline.run(AdRequest.model_validate(request_data), tmp_path, budget=2)
    run_id = pipeline.run_id
    assert state.one("SELECT status FROM model_call")["status"] == "dispatched"
    backend = SyntheticProvider()
    with pytest.raises(Blocked, match="not_resendable"):
        Pipeline(state, config, policy, backend, "live").run(
            AdRequest.model_validate(request_data), tmp_path, budget=2, run_id=run_id
        )
    assert backend.calls == []
    assert state.one("SELECT status,cost_unknown FROM model_call") == {
        "status": "unknown",
        "cost_unknown": 1,
    }


def test_receipt_reused_after_crash_before_stage_completion(run_pipeline, state):
    summary, backend = run_pipeline()
    row = state.one(
        "SELECT exec_id FROM stage_execution WHERE run_id=? AND stage='product_analysis'",
        (summary["run_id"],),
    )
    state.write("UPDATE stage_execution SET status='running' WHERE exec_id=?", (row["exec_id"],))
    # Simulate process death after receipt commit and before validated stage result commit.
    state.write(
        "DELETE FROM stage_artifact WHERE exec_id=? AND direction='output' AND label='result'",
        (row["exec_id"],),
    )
    run_pipeline(backend=backend, run_id=summary["run_id"])
    assert len(backend.calls) == 7


def test_sensitive_provider_exception_not_logged(run_pipeline, state):
    class BadBackend:
        def invoke(self, invocation, references):
            raise RuntimeError("SECRET_API_KEY_MUST_NEVER_APPEAR")

    with pytest.raises(Blocked, match="unknown"):
        run_pipeline(backend=BadBackend(), mode="live", budget=2)
    run_id = state.one("SELECT run_id FROM run")["run_id"]
    assert "SECRET_API_KEY" not in json.dumps(state.inspect(run_id))


def test_configuration_hash_prevents_stale_resume(
    run_pipeline, state, config, policy, request_data, tmp_path
):
    summary, _ = run_pipeline()
    changed = config.model_copy(update={"planner_effort": "high"})
    with pytest.raises(Blocked, match="changed"):
        Pipeline(state, changed, policy, SyntheticProvider()).run(
            AdRequest.model_validate(request_data), tmp_path, run_id=summary["run_id"]
        )
