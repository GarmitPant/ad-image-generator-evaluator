import csv
import json

from adgen.cli import main


def test_report_bundle_from_evaluated_demo_with_labels(tmp_path, capsys):
    db = str(tmp_path / "state.db")
    assert main(["--db", db, "demo", "--directory", str(tmp_path / "demo")]) == 0
    run_id = json.loads(capsys.readouterr().out)["run_id"]
    labels = tmp_path / "labels.csv"
    labels.write_text(
        "run_id,candidate_index,dimension,label,labeler,note\n"
        f"{run_id[:8]},1,overall,pass,tester,looks fine\n"
        f"{run_id[:8]},2,text_rendering,fail,tester,typo the evaluator cannot see (synthetic)\n"
    )
    out = tmp_path / "submission"
    assert main(["--db", db, "report", "--out", str(out), "--labels", str(labels)]) == 0
    assert (
        json.loads(capsys.readouterr().out)["requests"] == 0
    )  # synthetic runs excluded by default
    assert (
        main(
            [
                "--db",
                db,
                "report",
                "--out",
                str(out),
                "--labels",
                str(labels),
                "--include-synthetic",
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary == {"requests": 1, "candidates": 3, "labels": 2, "out": str(out)}
    rows = list(csv.DictReader((out / "results.csv").open()))
    assert [r["candidate_index"] for r in rows] == ["1", "2", "3"] and rows[0]["winner"] == "True"
    for r in json.loads((out / "results.json").read_text()):
        assert (out / r["image"]).exists() and (out / r["evidence"]).exists()
        assert (
            r["llm_model"]
            and r["image_model"]
            and r["evaluator_version"]
            and "generation_cost_usd" in r
        )
    assert len((out / "requests.jsonl").read_text().splitlines()) == 1
    report = (out / "report.md").read_text()
    assert "## 6. Credibility check against human labels" in report
    assert (
        "| text_rendering | 1 | 0 | 0 | 0 | 1 | 0 | 0.0 |" in report
    )  # the false accept is reported
    assert "images/" in (out / "contact-sheet.html").read_text()
    sheet = (out / "labeling-sheet.html").read_text()
    assert (
        "references/" in sheet and "overall_verdict" not in sheet and "score" not in sheet
    )  # blind
    template = list(csv.DictReader((out / "labels-template.csv").open()))
    assert len(template) == 3 * 6 and {t["label"] for t in template} == {""}
