"""Crash-safe local ledger. No credentials or provider exception strings are recorded."""

import fcntl
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from ..util import atomic_write, canonical, digest, fingerprint, now

MIGRATIONS = ["001_generation.sql", "002_remove_budget_cap.sql"]
SCHEMA_VERSION = len(MIGRATIONS)


class Blocked(RuntimeError):
    pass


class StageFailed(RuntimeError):
    pass


def failure(exc):
    """(status, code) for a failed step. Only our own exceptions' messages are recorded:
    SDK exception text can contain request headers or confidential copy."""
    code = str(exc) if isinstance(exc, (Blocked, StageFailed)) else type(exc).__name__
    return ("blocked" if isinstance(exc, Blocked) else "failed"), code


class State:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.root = self.path.parent
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        exists = self.db.execute(
            "SELECT 1 FROM sqlite_master WHERE name='schema_version'"
        ).fetchone()
        version = (
            self.db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
            if exists
            else 0
        )
        if not 0 <= version <= SCHEMA_VERSION:
            self.db.close()
            raise Blocked("unsupported_database_schema")
        for name in MIGRATIONS[version:]:
            sql = (Path(__file__).parent / "migrations" / name).read_text()
            # DDL is transactional, including the schema version marker.
            self.db.executescript("BEGIN IMMEDIATE;\n" + sql + "\nCOMMIT;")

    def close(self):
        self.db.close()

    def one(self, query, args=()):
        row = self.db.execute(query, args).fetchone()
        return dict(row) if row else None

    def rows(self, query, args=()):
        return [dict(row) for row in self.db.execute(query, args)]

    def write(self, query, args=()):
        with self.db:
            self.db.execute(query, args)

    def artifact(self, data: bytes, kind: str, provenance="code"):
        sha = digest(data)
        relative = f"artifacts/{sha[:2]}/{sha}"
        path = self.root / relative
        if path.exists():
            if digest(path.read_bytes()) != sha:
                raise Blocked("artifact_integrity_failure")
        else:
            atomic_write(path, data)
        self.write(
            "INSERT OR IGNORE INTO artifact VALUES(?,?,?,?,?,?,?)",
            (sha, kind, "generation/1", relative, len(data), provenance, now()),
        )
        return sha

    def read(self, sha):
        row = self.one("SELECT * FROM artifact WHERE artifact_id=?", (sha,))
        if not row:
            raise Blocked("missing_artifact_record")
        try:
            data = (self.root / row["path"]).read_bytes()
        except OSError as exc:
            raise Blocked("missing_artifact_file") from exc
        if len(data) != row["bytes"] or digest(data) != sha:
            raise Blocked("artifact_integrity_failure")
        return data

    def json(self, sha):
        return json.loads(self.read(sha))

    def link(self, exec_id, sha, direction, label):
        self.read(sha)
        self.write(
            "INSERT OR REPLACE INTO stage_artifact VALUES(?,?,?,?)",
            (exec_id, sha, direction, label),
        )

    def event(self, run_id, kind, payload, exec_id=None):
        self.write(
            "INSERT INTO event(run_id,exec_id,kind,payload,created_at) VALUES(?,?,?,?,?)",
            (run_id, exec_id, kind, canonical(payload).decode(), now()),
        )

    def create_run(self, request, request_hash, config, config_hash, mode, run_id=None):
        if run_id:
            record = self.one("SELECT * FROM run WHERE run_id=?", (run_id,))
            if not record:
                raise Blocked("run_not_found")
            if (record["request_sha256"], record["config_sha256"], record["mode"]) != (
                request_hash,
                config_hash,
                mode,
            ):
                raise Blocked("resume_inputs_config_or_mode_changed")
            return run_id
        run_id = uuid.uuid4().hex
        self.write(
            "INSERT INTO run(run_id,request_id,request_sha256,pipeline_version,config_sha256,mode,status,n_candidates,created_at,updated_at) VALUES(?,?,?,?,?,?,'pending',?,?,?)",
            (
                run_id,
                request.request_id,
                request_hash,
                config.version,
                config_hash,
                mode,
                request.n_candidates,
                now(),
                now(),
            ),
        )
        for index in range(1, request.n_candidates + 1):
            self.write(
                "INSERT INTO candidate(run_id,candidate_index,status) VALUES(?,?,'pending')",
                (run_id, index),
            )
        return run_id

    @contextmanager
    def lock(self, run_id):
        # Kernel releases flock on process death. A stale database owner can then be replaced safely.
        if not self.one("SELECT run_id FROM run WHERE run_id=?", (run_id,)):
            raise Blocked("run_not_found")
        lock_dir = self.root / "locks"
        lock_dir.mkdir(exist_ok=True)
        path = lock_dir / f"{fingerprint(run_id)}.lock"
        with path.open("a") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise Blocked("run_already_locked") from exc
            owner = f"{os.getpid()}:{uuid.uuid4().hex}"
            try:
                self.write(
                    "UPDATE run SET lock_owner=?,updated_at=? WHERE run_id=?",
                    (owner, now(), run_id),
                )
                # Dispatch was committed but no receipt was committed: outcome is uncertain.
                with self.db:
                    self.db.execute(
                        "UPDATE model_call SET status='unknown',cost_unknown=1,error_code='interrupted_after_dispatch' WHERE status='dispatched' AND exec_id IN (SELECT exec_id FROM stage_execution WHERE run_id=?)",
                        (run_id,),
                    )
                    self.db.execute(
                        "UPDATE run SET cost_unknown=1 WHERE run_id=? AND EXISTS(SELECT 1 FROM model_call m JOIN stage_execution s USING(exec_id) WHERE s.run_id=? AND m.cost_unknown=1)",
                        (run_id, run_id),
                    )
                yield
            finally:
                self.write(
                    "UPDATE run SET lock_owner=NULL,updated_at=? WHERE run_id=? AND lock_owner=?",
                    (now(), run_id, owner),
                )
                fcntl.flock(handle, fcntl.LOCK_UN)

    def finish(self, run_id, status, reason):
        self.write(
            "UPDATE run SET status=?,terminal_reason=?,updated_at=? WHERE run_id=?",
            (status, reason, now(), run_id),
        )
        self.event(run_id, "run_finished", {"status": status, "reason": reason})

    def stage(self, run_id, name, inputs, config_key, fn, *, candidate=0, attempt=1, cache=False):
        for sha in inputs.values():
            self.read(sha)
        key = fingerprint({"stage": name, "inputs": inputs, "config": config_key})
        row = self.one(
            "SELECT * FROM stage_execution WHERE run_id=? AND stage=? AND candidate_index=? AND attempt=?",
            (run_id, name, candidate, attempt),
        )
        if row:
            if row["input_fingerprint"] != key:
                raise Blocked("stage_fingerprint_changed")
            if row["status"] == "succeeded":
                return self._stage_result(row["exec_id"])
            if row["status"] == "failed":
                raise StageFailed(row["error_code"])
            if row["status"] == "blocked":
                raise Blocked(row["error_code"])
            exec_id = row["exec_id"]
        else:
            exec_id = uuid.uuid4().hex
            self.write(
                "INSERT INTO stage_execution(exec_id,run_id,stage,candidate_index,attempt,status,input_hashes,input_fingerprint,started_at) VALUES(?,?,?,?,?,'running',?,?,?)",
                (exec_id, run_id, name, candidate, attempt, canonical(inputs).decode(), key, now()),
            )
        for label, sha in inputs.items():
            self.link(exec_id, sha, "input", label)
        self.write(
            "UPDATE run SET status='running',current_stage=?,updated_at=? WHERE run_id=?",
            (name, now(), run_id),
        )
        if cache:
            other = self.one(
                "SELECT exec_id FROM stage_execution WHERE stage=? AND input_fingerprint=? AND status='succeeded' AND exec_id<>? ORDER BY ended_at DESC LIMIT 1",
                (name, key, exec_id),
            )
            if other:
                result, sha = self._stage_result(other["exec_id"])
                for artifact in self.rows(
                    "SELECT * FROM stage_artifact WHERE exec_id=? AND direction='output'",
                    (other["exec_id"],),
                ):
                    self.link(exec_id, artifact["artifact_id"], "output", artifact["label"])
                self.write(
                    "UPDATE stage_execution SET status='succeeded',reused_from=?,ended_at=? WHERE exec_id=?",
                    (other["exec_id"], now(), exec_id),
                )
                self.event(run_id, "stage_cache_hit", {"stage": name}, exec_id)
                return result, sha
        self.event(
            run_id,
            "stage_started",
            {"stage": name, "candidate": candidate, "attempt": attempt},
            exec_id,
        )
        try:
            result = fn(exec_id)
            sha = self.artifact(canonical(result), name)
            self.link(exec_id, sha, "output", "result")
            self.write(
                "UPDATE stage_execution SET status='succeeded',error_code=NULL,error_detail=NULL,ended_at=? WHERE exec_id=?",
                (now(), exec_id),
            )
            self.event(run_id, "stage_succeeded", {"stage": name}, exec_id)
            return result, sha
        except Exception as exc:
            status, code = failure(exc)
            self.write(
                "UPDATE stage_execution SET status=?,error_code=?,ended_at=? WHERE exec_id=?",
                (status, code, now(), exec_id),
            )
            self.event(run_id, "stage_failed", {"stage": name, "code": code}, exec_id)
            raise

    def _stage_result(self, exec_id):
        outputs = self.rows(
            "SELECT * FROM stage_artifact WHERE exec_id=? AND direction='output'", (exec_id,)
        )
        for output in outputs:
            self.read(output["artifact_id"])
        result = next((o for o in outputs if o["label"] == "result"), None)
        if result is None:
            raise Blocked("missing_stage_result")
        return self.json(result["artifact_id"]), result["artifact_id"]

    def inspect(self, run_id):
        run = self.one("SELECT * FROM run WHERE run_id=?", (run_id,))
        if not run:
            raise Blocked("run_not_found")
        return {
            "run": run,
            "candidates": self.rows(
                "SELECT * FROM candidate WHERE run_id=? ORDER BY candidate_index", (run_id,)
            ),
            "stages": self.rows(
                "SELECT * FROM stage_execution WHERE run_id=? ORDER BY started_at", (run_id,)
            ),
            "model_calls": self.rows(
                "SELECT m.* FROM model_call m JOIN stage_execution s USING(exec_id) WHERE s.run_id=? ORDER BY m.started_at",
                (run_id,),
            ),
            "events": self.rows("SELECT * FROM event WHERE run_id=? ORDER BY event_id", (run_id,)),
        }
