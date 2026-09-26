CREATE TABLE schema_version(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE run(
 run_id TEXT PRIMARY KEY, request_id TEXT NOT NULL, request_sha256 TEXT NOT NULL,
 pipeline_version TEXT NOT NULL, config_sha256 TEXT NOT NULL,
 mode TEXT NOT NULL CHECK(mode IN ('live','replay')),
 status TEXT NOT NULL CHECK(status IN ('pending','running','succeeded','failed','blocked')),
 current_stage TEXT, terminal_reason TEXT, n_candidates INTEGER NOT NULL CHECK(n_candidates BETWEEN 1 AND 4),
 budget_cap_usd REAL NOT NULL CHECK(budget_cap_usd>=0), cost_est_usd REAL NOT NULL DEFAULT 0,
 cost_unknown INTEGER NOT NULL DEFAULT 0, lock_owner TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE stage_execution(
 exec_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES run(run_id), stage TEXT NOT NULL,
 candidate_index INTEGER NOT NULL DEFAULT 0 CHECK(candidate_index BETWEEN 0 AND 4),
 attempt INTEGER NOT NULL CHECK(attempt IN (1,2)), status TEXT NOT NULL,
 input_hashes TEXT NOT NULL, input_fingerprint TEXT NOT NULL,
 reused_from TEXT REFERENCES stage_execution(exec_id), error_code TEXT, error_detail TEXT,
 started_at TEXT NOT NULL, ended_at TEXT,
 UNIQUE(run_id,stage,candidate_index,attempt)
);
CREATE INDEX stage_cache ON stage_execution(stage,input_fingerprint,status);
CREATE TABLE artifact(
 artifact_id TEXT PRIMARY KEY, kind TEXT NOT NULL, schema_version TEXT NOT NULL,
 path TEXT NOT NULL, bytes INTEGER NOT NULL, provenance TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE stage_artifact(
 exec_id TEXT NOT NULL REFERENCES stage_execution(exec_id), artifact_id TEXT NOT NULL REFERENCES artifact(artifact_id),
 direction TEXT NOT NULL CHECK(direction IN ('input','output')), label TEXT NOT NULL,
 PRIMARY KEY(exec_id,direction,label)
);
CREATE TABLE model_call(
 call_id TEXT PRIMARY KEY, exec_id TEXT NOT NULL REFERENCES stage_execution(exec_id),
 provider TEXT NOT NULL, model_requested TEXT NOT NULL, model_returned TEXT,
 purpose TEXT NOT NULL, invocation_sha256 TEXT NOT NULL, prompt_sha256 TEXT NOT NULL,
 request_path TEXT NOT NULL, response_path TEXT, request_artifact TEXT NOT NULL REFERENCES artifact(artifact_id),
 response_artifact TEXT REFERENCES artifact(artifact_id), status TEXT NOT NULL,
 reservation_usd REAL NOT NULL, cost_est_usd REAL NOT NULL, cost_unknown INTEGER NOT NULL DEFAULT 0,
 usage_json TEXT, error_code TEXT, started_at TEXT NOT NULL, ended_at TEXT,
 UNIQUE(exec_id,invocation_sha256)
);
CREATE TABLE candidate(
 run_id TEXT NOT NULL REFERENCES run(run_id), candidate_index INTEGER NOT NULL CHECK(candidate_index BETWEEN 1 AND 4),
 status TEXT NOT NULL, guardrail_status TEXT, image_artifact TEXT REFERENCES artifact(artifact_id),
 error_code TEXT, PRIMARY KEY(run_id,candidate_index)
);
CREATE TABLE event(
 event_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES run(run_id),
 exec_id TEXT REFERENCES stage_execution(exec_id), kind TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL
);
INSERT INTO schema_version VALUES(1,strftime('%Y-%m-%dT%H:%M:%fZ','now'));
