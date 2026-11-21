"""Exercise the supported observation-to-dashboard CLI path as one contract."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

SKILL = Path(__file__).resolve().parents[1]


def invoke(script: str, *arguments: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *arguments],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_scan_duplicate_review_and_dashboard_share_report_contract(tmp_path: Path) -> None:
    scope = tmp_path / "scope"
    scope.mkdir()
    payload = b"identical fixture content"
    for name in ("-leading\nnewline.txt", "unicode-\u00e9.txt"):
        (scope / name).write_bytes(payload)
    database = tmp_path / "inventory.sqlite"
    schema = json.loads((SKILL / "assets" / "report.schema.json").read_text(encoding="utf-8"))
    outputs = (
        invoke("storage-audit.py", "scan", str(scope), "--database", str(database)),
        invoke("storage-audit.py", "dedupe", "--database", str(database), "--read-content"),
    )
    for index, report in enumerate(outputs):
        jsonschema.Draft202012Validator(schema).validate(report)
        assert report["savings"]["verified_reclaimed_bytes"] is None
        assert report["savings"]["acted_bytes"] == 0
        report_path = tmp_path / f"report-{index}.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        html = tmp_path / f"dashboard-{index}.html"
        rendered = invoke("dashboard-renderer.py", "--data", str(report_path), "--output", str(html))
        assert rendered["output"] == str(html)
        assert html.is_file()
    assert outputs[0]["counts"]["files_seen"] == 2
    assert outputs[1]["savings"]["candidate_bytes"] == len(payload)
    assert outputs[1]["duplicates"][0]["keeper"] is None
    assert sorted(path.read_bytes() for path in scope.iterdir()) == [payload, payload]
