"""Behavioral regression tests for report contracts and the portable renderer."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from files_buddy_report import (  # noqa: E402 - packaged script path
    ReportError,
    load_report,
    new_report,
    normalize_report,
)


class TestReportContract:
    def test_zero_verified_does_not_become_completed_or_reclaimed(self) -> None:
        result = normalize_report(
            {"schema_version": "1.1", "savings": {"completed_local_bytes": 2**30, "verified_local_bytes": 0}}
        )
        assert result["savings"]["acted_bytes"] == 2**30
        assert result["savings"]["legacy_verified_local_bytes"] == 0
        assert result["savings"]["verified_reclaimed_bytes"] is None
        native = new_report("storage-audit", ["/Users/example/Downloads"])
        native["savings"].update({"acted_bytes": 2**30, "verified_reclaimed_bytes": 0})
        assert normalize_report(native)["savings"]["verified_reclaimed_bytes"] == 0

    def test_cloud_duplicate_is_only_evidence(self) -> None:
        result = normalize_report(
            {"duplicates": [{"files": ["~/Library/CloudStorage/a", "~/Library/CloudStorage/b"], "size": 12}]}
        )
        assert result["recommendations"] == []
        assert result["duplicates"][0]["risk"] == "unknown"
        assert "restore_path" not in result["duplicates"][0]
        assert result["savings"]["cloud_bytes_affected"] is None

    def test_legacy_offload_field_has_one_normalized_value(self) -> None:
        result = normalize_report({"recommendations": [{"action": "offload", "local_bytes_saved": 4096}]})
        assert result["recommendations"][0]["local_bytes"] == 4096
        assert result["recommendations"][0]["restore_path"] is None
        assert result["recommendations"][0]["risk"] == "unknown"

    def test_bad_shape_version_number_and_enum_are_rejected(self) -> None:
        cases = [
            None,
            [],
            {"files": {}},
            {"files": [None]},
            {"schema_version": "9"},
            {"savings": {"completed_local_bytes": -1}},
            {"savings": {"completed_local_bytes": 1.5}},
            {"savings": {"completed_local_bytes": True}},
            {"savings": {"made_up_bytes": 3}},
            {"status": {}},
            {"coverage": {"status": []}},
            {"counts": {"files_seen": -1}},
            {"recommendations": [{"risk": "probably fine"}]},
            {"duplicates": [{"kind": {}}]},
            {"updated_at": "2026-11-20T12:00:00"},
            {"updated_at": "2026-11-20 12:00:00+00:00"},
            {"updated_at": "20261120T120000+0000"},
            {"scope": 12},
            {"manifest": 12},
            {"schema_version": "2.0"},
            {"files": [{"allocated_bytes": float("nan")}]},
        ]
        for value in cases:
            with pytest.raises(ReportError):
                normalize_report(value)

    def test_negative_free_space_delta_is_valid(self) -> None:
        result = new_report("storage-audit", "/Users/example")
        result["savings"]["observed_free_space_delta_bytes"] = -4096
        assert normalize_report(result)["savings"]["observed_free_space_delta_bytes"] == -4096

    @pytest.mark.parametrize("run_id", [".", "..", ".hidden", "../outside", "/tmp", "a/b", "a\\b", "a\x00b"])
    def test_run_id_is_a_single_safe_directory_component(self, run_id: str) -> None:
        report = new_report("storage-audit", ["/Users/example"])
        report["run_id"] = run_id
        with pytest.raises(ReportError, match="run_id"):
            normalize_report(report)

    def test_normalization_is_idempotent_and_refreshes_digest(self) -> None:
        result = normalize_report({"files": []})
        assert normalize_report(result) == result
        result["files"].append({"path": "new", "size": 1})
        assert normalize_report(result)["source_digest"] != result["source_digest"]

    def test_manifest_path_and_legacy_shape_remain_explicit(self) -> None:
        result = normalize_report({"manifest": {"path": "/state/a.json", "status": "partial"}})
        assert result["manifest"]["path"] == "/state/a.json"
        assert normalize_report({"manifest": "/state/a.json"})["manifest"] == {"path": "/state/a.json"}

    def test_duplicate_json_keys_and_nonfinite_values_fail(self) -> None:
        for value in ['{"files": [], "files": {}}', '{"size":NaN}', "{"]:
            with pytest.raises(ReportError):
                load_report(value)

    @pytest.mark.skipif(not importlib.util.find_spec("jsonschema"), reason="development schema checker is unavailable")
    def test_normalized_reports_match_published_schema(self) -> None:
        import jsonschema

        schema = json.loads((SKILL / "assets" / "report.schema.json").read_text())
        for data in (
            {},
            {"manifest": "/state/a.json"},
            {"recommendations": [{"action": "offload", "local_bytes_saved": 2}]},
        ):
            jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(
                normalize_report(data)
            )


class TestRenderer:
    def invoke(self, data: object, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "dashboard-renderer.py"), "--data", "-", *args],
            input=json.dumps(data),
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "HOME": str(home)},
        )

    def test_renderer_rejects_invalid_shapes_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            for data in (None, {"files": {}}, {"schema_version": "3.0"}):
                result = self.invoke(data, home)
                assert result.returncode == 1, result.stderr
                assert "error" in json.loads(result.stdout)
            assert list(home.iterdir()) == []

    def test_renderer_rejects_traversal_run_ids_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            for run_id in (".", "..", "../outside"):
                result = self.invoke({"run_id": run_id}, home)
                assert result.returncode == 1
                assert "run_id" in json.loads(result.stdout)["error"]
            assert list(home.iterdir()) == []

    @pytest.mark.parametrize("component", [".files-buddy", "runs", "safe-run"])
    def test_default_output_rejects_existing_parent_symlinks(self, component: str) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            home = base / "home"
            outside = base / "outside"
            home.mkdir()
            outside.mkdir()
            parent = home
            for part in (".files-buddy", "runs", "safe-run"):
                path = parent / part
                if part == component:
                    path.symlink_to(outside, target_is_directory=True)
                    break
                path.mkdir()
                parent = path
            result = self.invoke({"run_id": "safe-run"}, home)
            assert result.returncode == 1
            assert list(outside.iterdir()) == []

    def test_unique_reports_escaped_data_and_no_clobber(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            data = {"files": [{"path": "</script><img src=x onerror=alert(1)>\u2028&", "size": 12}]}
            first = self.invoke(data, home)
            second = self.invoke(data, home)
            assert first.returncode == 0, first.stderr + first.stdout
            assert second.returncode == 0, second.stderr + second.stdout
            paths = [Path(json.loads(item.stdout)["output"]) for item in (first, second)]
            assert paths[0] != paths[1]
            html = paths[0].read_text()
            assert "</script><img src=x" not in html
            assert "\\u003c/script\\u003e" in html
            assert paths[0].stat().st_mode & 511 == 384
            original = paths[0].read_bytes()
            collision = self.invoke({}, home, "--output", str(paths[0]))
            assert collision.returncode == 1
            assert paths[0].read_bytes() == original

    def test_source_schema_is_embedded_without_network_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = self.invoke({}, Path(temp))
            html = Path(json.loads(result.stdout)["output"]).read_text()
            assert '"title": "Files Buddy normalized report 2.0"' in html
            assert "<script src=" not in html
            assert "fetch(" not in html
            assert "connect-src 'none'" in html
            assert "prefers-reduced-motion" in html
            assert "showOpenFilePicker" in html
