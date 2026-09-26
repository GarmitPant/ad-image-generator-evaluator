import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from .config import PipelineConfig, load_policy
from .contracts import AdRequest
from .demo import SyntheticProvider, prepare_demo
from .pipeline import Pipeline, export_run
from .providers import LiveProvider, ReplayProvider, export_fixtures
from .state import SCHEMA_VERSION, Blocked, StageFailed, State


def parser():
    root = argparse.ArgumentParser(
        description="Generation-only ad pipeline. No evaluation or winner selection."
    )
    root.add_argument("--db", default=os.getenv("ADGEN_STATE_DB", "runs/state.db"))
    root.add_argument("--config", default="config/pipeline.toml")
    root.add_argument("--policy", default="policy/guardrails.yaml")
    commands = root.add_subparsers(dest="command", required=True)
    generation = commands.add_parser("generate")
    generation.add_argument("--request", required=True, type=Path)
    generation.add_argument("--mode", choices=["replay", "live"], default="replay")
    generation.add_argument("--fixtures", type=Path)
    generation.add_argument(
        "--run-id",
        help="Resume this immutable run; same request, references, config and mode required",
    )
    generation.add_argument(
        "--allow-paid",
        action="store_true",
        help="Explicit authorization for paid live inference; spend limits are set on the provider accounts",
    )
    demo = commands.add_parser(
        "demo", help="Offline synthetic fixtures, visibly labeled; never calls providers"
    )
    demo.add_argument("--directory", type=Path, default=Path("runs/demo"))
    state = commands.add_parser("state")
    states = state.add_subparsers(dest="state_command", required=True)
    states.add_parser("init")
    show = states.add_parser("show")
    show.add_argument("run_id")
    export = commands.add_parser("export")
    export.add_argument("run_id")
    export.add_argument("--destination", type=Path)
    fixtures = commands.add_parser(
        "export-fixtures", help="Export recorded call responses for exact-match offline replay"
    )
    fixtures.add_argument("run_id")
    fixtures.add_argument("--destination", required=True, type=Path)
    return root


def error_payload(exc, run_id):
    if isinstance(exc, (Blocked, StageFailed)):
        return {"error": str(exc), "run_id": run_id}
    if isinstance(exc, ValidationError):
        # No input values in diagnostics (source text may be confidential).
        details = [
            {"location": list(e["loc"]), "type": e["type"]}
            for e in exc.errors(include_input=False, include_url=False)
        ]
        return {"error": "validation_failed", "details": details, "run_id": run_id}
    return {
        "error": type(exc).__name__,
        "run_id": run_id,
        "hint": "Check input files, image limits, protected spans and text capacity; no exception payload is logged.",
    }


def main(argv=None):
    args = parser().parse_args(argv)
    state = None
    pipeline = None
    try:
        state = State(args.db)
        if args.command == "state":
            print(
                json.dumps(
                    {"database": str(state.path), "schema_version": SCHEMA_VERSION}
                    if args.state_command == "init"
                    else state.inspect(args.run_id),
                    indent=2,
                )
            )
            return 0
        if args.command == "export-fixtures":
            with state.lock(args.run_id):
                count = export_fixtures(state, args.run_id, args.destination)
            print(
                json.dumps(
                    {"recorded_calls": count, "fixture_directory": str(args.destination.resolve())}
                )
            )
            return 0
        if args.command == "export":
            with state.lock(args.run_id):
                path = export_run(state, args.run_id, args.destination)
            print(json.dumps({"export_directory": str(path.resolve())}))
            return 0
        config = PipelineConfig.load(args.config)
        policy = load_policy(args.policy)
        if args.command == "demo":
            request_path = prepare_demo(args.directory)
            backend = SyntheticProvider(args.directory / "fixtures")
            mode, run_id = "replay", None
        else:
            request_path = args.request
            mode, run_id = args.mode, args.run_id
            if mode == "live":
                if not args.allow_paid:
                    raise Blocked("live_requires_allow_paid")
                load_dotenv(Path.cwd() / ".env", override=False)
                if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("GEMINI_API_KEY"):
                    raise Blocked("missing_provider_credentials")
                backend = LiveProvider(config)
            else:
                if not args.fixtures:
                    raise Blocked("replay_requires_explicit_fixture_directory")
                backend = ReplayProvider(args.fixtures)
        request = AdRequest.model_validate_json(request_path.read_text())
        pipeline = Pipeline(state, config, policy, backend, mode)
        summary = pipeline.run(request, request_path.resolve().parent, run_id=run_id)
        print(
            json.dumps(
                {
                    "run_id": summary["run_id"],
                    "status": summary["status"],
                    "synthetic": summary["synthetic"],
                    "candidates": summary["candidates"],
                    "export_directory": str(state.root / "exports" / summary["run_id"]),
                    "evaluation_performed": False,
                },
                indent=2,
            )
        )
        if summary["status"] != "generated_unscored":
            return 2
        return 0 if all(c["status"] == "generated_unscored" for c in summary["candidates"]) else 3
    except (Blocked, StageFailed, OSError, ValueError) as exc:
        print(json.dumps(error_payload(exc, getattr(pipeline, "run_id", None))))
        return 2
    finally:
        if state:
            state.close()


if __name__ == "__main__":
    raise SystemExit(main())
