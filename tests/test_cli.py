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
            "--budget-usd",
            "2",
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
    assert replay["status"] == "generated_unscored"
    destination = tmp_path / "export"
    assert (
        main(["--db", str(db), "export", result["run_id"], "--destination", str(destination)]) == 0
    )
    assert len(list(destination.glob("candidate-*.png"))) == 3
