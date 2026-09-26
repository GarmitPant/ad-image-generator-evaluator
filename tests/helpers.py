from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def open_exec(state, run_id="r", exec_id="e"):
    """Minimal run + running stage so artifacts can be linked in unit tests."""
    state.write(
        "INSERT OR IGNORE INTO run(run_id,request_id,request_sha256,pipeline_version,config_sha256,mode,status,n_candidates,created_at,updated_at) VALUES(?,'x','h','v','c','replay','running',1,'t','t')",
        (run_id,),
    )
    state.write(
        "INSERT OR IGNORE INTO stage_execution(exec_id,run_id,stage,candidate_index,attempt,status,input_hashes,input_fingerprint,started_at) VALUES(?,?,'evaluation',1,1,'running','{}','f','t')",
        (exec_id, run_id),
    )
    return exec_id
