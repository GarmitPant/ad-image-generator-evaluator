import json

from adgen.cli import main


def test_live_without_spend_flag_never_contacts_provider(tmp_path, capsys):
    code = main(
        [
            "--db",
            str(tmp_path / "state.db"),
            "generate",
            "--request",
            "unused.json",
            "--mode",
            "live",
        ]
    )
    assert code == 2
    assert "allow_paid" in capsys.readouterr().out


def test_replay_needs_explicit_fixture_dir(tmp_path, capsys):
    code = main(["--db", str(tmp_path / "state.db"), "generate", "--request", "unused.json"])
    assert code == 2
    assert "fixture_directory" in capsys.readouterr().out


def test_demo_then_cli_replay_and_export(tmp_path, capsys):
    db = tmp_path / "runs/state.db"
    demo_dir = tmp_path / "demo"
    assert main(["--db", str(db), "demo", "--directory", str(demo_dir)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["synthetic"] is True
    assert (
        main(
            [
                "--db",
                str(tmp_path / "replay/state.db"),
                "generate",
                "--request",
                str(demo_dir / "request.json"),
                "--fixtures",
                str(demo_dir / "fixtures"),
            ]
        )
        == 0
    )
    replay = json.loads(capsys.readouterr().out)
    # Evaluation is on by default: every candidate scored, ranked and a winner exported.
    assert replay["status"] == "evaluated" and replay["evaluation_performed"] is True
    assert replay["winner"] == 1 and replay["approved"] is True
    assert [r["overall_verdict"] for r in replay["ranking"]] == ["pass"] * 3
    assert replay["ranking"] == result["ranking"]  # replay reproduces the demo exactly
    destination = tmp_path / "export"
    assert (
        main(["--db", str(db), "export", result["run_id"], "--destination", str(destination)]) == 0
    )
    assert len(list(destination.glob("candidate-*.png"))) == 3
    assert (destination / "best.png").exists()
    assert len(list((destination / "evaluations").glob("candidate-*.json"))) == 3


def test_skip_evaluation_keeps_generation_only_behaviour(tmp_path, capsys):
    demo_dir = tmp_path / "demo"
    assert main(["--db", str(tmp_path / "a.db"), "demo", "--directory", str(demo_dir)]) == 0
    capsys.readouterr()
    code = main(
        [
            "--db",
            str(tmp_path / "b.db"),
            "generate",
            "--request",
            str(demo_dir / "request.json"),
            "--fixtures",
            str(demo_dir / "fixtures"),
            "--skip-evaluation",
        ]
    )
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["status"] == "generated_unscored" and out["winner"] is None
