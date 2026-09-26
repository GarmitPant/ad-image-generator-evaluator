import csv
import json

from adgen.cli import main


def test_readable_report_bundle_from_evaluated_demo(tmp_path, capsys):
    db = str(tmp_path / "state.db")
    assert main(["--db", db, "demo", "--directory", str(tmp_path / "demo")]) == 0
    capsys.readouterr()
    out = tmp_path / "submission"
    assert main(["--db", db, "report", "--out", str(out)]) == 0
    assert (
        json.loads(capsys.readouterr().out)["requests"] == 0
    )  # synthetic runs excluded by default
    assert main(["--db", db, "report", "--out", str(out), "--include-synthetic"]) == 0
    assert json.loads(capsys.readouterr().out) == {"requests": 1, "candidates": 3, "out": str(out)}
    rows = list(csv.DictReader((out / "results.csv").open()))
    assert [r["candidate"] for r in rows] == ["1", "2", "3"]
    assert (
        rows[0]["verdict"] == "PASS"
        and rows[0]["winner"] == "yes"
        and rows[0]["text rendering"] == "PASS"
    )
    for r in json.loads((out / "results.json").read_text()):
        assert (out / r["image"]).exists() and (out / r["evidence"]).exists()
        card = (out / r["evidence_card"]).read_text()
        assert (
            "Every copy line appears once, spelled exactly" in card
            and "expected vs read by OCR" in card
        )
    report = (out / "report.md").read_text()
    assert "## 4. Per request" in report and "| 1 | 1 | PASS |" in report
    assert (
        "human label" in report.lower()
    )  # limitation stated: accuracy not measured against human labels
    assert "full evaluation" in (out / "contact-sheet.html").read_text()
