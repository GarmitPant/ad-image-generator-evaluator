-- Evaluation records per candidate (append-only: re-evaluation adds rows) and one selection per run.
CREATE TABLE evaluation(
 evaluation_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES run(run_id),
 candidate_index INTEGER NOT NULL, image_artifact TEXT NOT NULL REFERENCES artifact(artifact_id),
 record_artifact TEXT NOT NULL REFERENCES artifact(artifact_id), evaluator_version TEXT NOT NULL,
 overall_verdict TEXT NOT NULL CHECK(overall_verdict IN ('pass','fail','unknown')),
 overall_score REAL NOT NULL, failed_required_checks INTEGER NOT NULL,
 text_selection_verdict TEXT NOT NULL, text_selection_score REAL NOT NULL,
 text_rendering_verdict TEXT NOT NULL, text_rendering_score REAL NOT NULL,
 product_verdict TEXT NOT NULL, product_score REAL NOT NULL,
 context_verdict TEXT NOT NULL, context_score REAL NOT NULL,
 execution_status TEXT NOT NULL CHECK(execution_status IN ('ok','degraded','failed')),
 created_at TEXT NOT NULL
);
CREATE INDEX evaluation_run ON evaluation(run_id, candidate_index);
CREATE TABLE selection(
 run_id TEXT PRIMARY KEY REFERENCES run(run_id), winner_index INTEGER, approved INTEGER NOT NULL,
 ranking TEXT NOT NULL, ranking_rule TEXT NOT NULL, created_at TEXT NOT NULL
);
INSERT INTO schema_version VALUES(3,strftime('%Y-%m-%dT%H:%M:%fZ','now'));
