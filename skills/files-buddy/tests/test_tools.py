"""Versioned parser and command-boundary regressions; no native tool required."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
from files_buddy_tools import (
    ToolError,
    capability,
    observe,
    parse_json,
    parse_observation,
    run_bounded,
    validate_organize_rules,
)

FIXTURES = Path(__file__).parent / "fixtures" / "tools"
CLI = Path(__file__).resolve().parents[1] / "scripts" / "storage-audit.py"


def fixture(name: str) -> object:
    return json.loads((FIXTURES / f"{name}.json").read_text())


class AdapterTests(unittest.TestCase):
    def test_mole_partial_and_unavailable_are_not_zero_or_complete(self) -> None:
        partial = parse_observation("mole", "analyze", "1.73.0", fixture("mole-analyze-partial"))
        assert partial["coverage"] == "partial"
        assert partial["size_is_lower_bound"]
        assert partial["entries"][0]["tool_cleanable_hint"]
        assert partial["entries"][0]["action"] == "review"
        assert partial["entries"][1]["size"] is None
        unavailable = parse_observation("mole", "analyze", "1.73.0", fixture("mole-analyze-unavailable"))
        assert unavailable["logical_bytes"] is None
        assert unavailable["coverage"] == "unavailable"
        assert not unavailable["authorizes_mutation"]

    def test_mole_inconsistent_complete_downgrades(self) -> None:
        data = fixture("mole-analyze-partial")
        data["scan_status"] = "complete"
        assert parse_observation("mole", "analyze", "1.73.0", data)["coverage"] == "partial"

    def test_mole_unknown_status_or_boolean_size_is_rejected(self) -> None:
        for field, value in [("scan_status", "maybe"), ("total_size", True)]:
            data = fixture("mole-analyze-complete")
            data[field] = value
            with pytest.raises(ToolError):
                parse_observation("mole", "analyze", "1.73.0", data)

    def test_mole_nonstring_status_is_structured_cli_error(self) -> None:
        for value in ([], {}):
            for nested in (False, True):
                data = fixture("mole-analyze-complete")
                if nested:
                    data["entries"][0]["scan_status"] = value
                else:
                    data["scan_status"] = value
                process = subprocess.run(
                    [sys.executable, str(CLI), "observe", "mole", "analyze", "--version", "1.73.0", "--input", "-"],
                    input=json.dumps(data),
                    text=True,
                    capture_output=True,
                    check=False,
                )
                assert process.returncode == 1
                assert "error" in json.loads(process.stdout)
                assert "Traceback" not in process.stderr

    def test_duplicate_keys_nonfinite_and_deep_json_rejected(self) -> None:
        for raw in ('{"a": 1, "a": 2}', '{"a": NaN}', "[Infinity]", "[1e999]", "[" * 2000):
            with self.subTest(raw=raw[:30]), pytest.raises(ToolError):
                parse_json(raw)

    def test_mole_status_excludes_process_commands(self) -> None:
        result = parse_observation("mole", "status", "1.73.0", fixture("mole-status"))
        assert "sensitive command" not in json.dumps(result)
        assert result["trash_retained_bytes"] == 1024
        assert result["trash_approximate"]
        assert result["coverage"] == "unknown"

    def test_mole_history_cannot_authorize_undo(self) -> None:
        result = parse_observation("mole", "history", "1.73.0", fixture("mole-history"))
        assert not result["authorizes_mutation"]
        assert not result["deletions"][0]["restore_verified"]
        assert result["deletions"][0]["status"] == "dry-run"
        assert result["coverage"] == "partial"

    def test_fclones_current_shape_and_missing_stats(self) -> None:
        data = fixture("fclones-group")
        result = parse_observation("fclones", "group", "0.35.0", data)
        assert result["stats"]["redundant_file_size"] == 4096
        group = result["duplicates"][0]
        assert all(isinstance(path, str) for path in group["files"])
        assert group["hash_algorithm"] == "fclones-reported-unknown"
        assert group["keeper"] is None
        data["header"]["stats"] = None
        assert parse_observation("fclones", "group", "0.35.0", data)["coverage"] == "partial"

    def test_fclones_obsolete_shape_and_mismatched_header_rejected(self) -> None:
        for changed in [{"stats": {}, "groups": []}, fixture("fclones-group")]:
            if "header" in changed:
                changed["header"]["version"] = "0.18.0"
            with pytest.raises(ToolError):
                parse_observation("fclones", "group", "0.35.0", changed)

    def test_dust_is_one_display_root_with_unknown_raw_bytes(self) -> None:
        result = parse_observation("dust", "tree", "1.2.7", fixture("dust-tree"))
        assert result["directories"][0]["size_display"] == "1.0G"
        assert all(row["bytes"] is None for row in result["directories"])
        with pytest.raises(ToolError):
            parse_observation("dust", "tree", "1.2.7", [fixture("dust-tree")])

    def test_f2_conflicting_preview_cannot_be_executed(self) -> None:
        result = parse_observation("f2", "preview", "2.2.2", fixture("f2-preview"))
        assert not result["mappings"][0]["conflict"]
        assert result["mappings"][1]["conflict"]
        assert not result["authorizes_mutation"]
        with pytest.raises(ToolError, match="imports"):
            observe("f2", "preview", path="/tmp")

    def test_rclone_unknown_size_and_no_content_identity(self) -> None:
        result = parse_observation("rclone", "lsjson", "1.76.0", fixture("rclone-lsjson"))
        assert result["files"][1]["size"] is None
        assert all(not row["content_verified"] for row in result["files"])

    def test_unknown_version_and_mutating_commands_fail_closed(self) -> None:
        with pytest.raises(ToolError, match="Unqualified"):
            capability("mole", "analyze", "999.0.0")
        for command in ("clean", "purge", "uninstall", "optimize", "slim"):
            with pytest.raises(ToolError):
                capability("mole", command, "1.73.0")
        for tool, command in [("rclone", "sync"), ("fclones", "remove"), ("f2", "exec")]:
            with pytest.raises(ToolError):
                observe(tool, command)

    def test_actual_version_is_probed_before_observation(self) -> None:
        with (
            patch("files_buddy_tools.shutil.which", return_value="/opt/mo"),
            patch("files_buddy_tools.run_bounded", return_value={"stdout": "Mole 999.0.0", "exit_code": 0}) as run,
            pytest.raises(ToolError, match="Unqualified"),
        ):
            observe("mole", "status")
        run.assert_called_once()

    def test_live_mole_uses_fixed_argv_and_partial_stays_partial(self) -> None:
        receipts = [
            {"stdout": "Mole V1.73.0", "exit_code": 0},
            {
                "stdout": json.dumps(fixture("mole-analyze-partial")),
                "exit_code": 0,
                "argv": ["/opt/mo", "analyze", "--json", "/tmp"],
                "elapsed_seconds": 0.1,
                "stderr": "",
            },
        ]
        with (
            tempfile.TemporaryDirectory() as temp,
            patch("files_buddy_tools.shutil.which", return_value="/opt/mo"),
            patch("files_buddy_tools.run_bounded", side_effect=receipts) as run,
        ):
            result = observe("mole", "analyze", path=temp)
            assert run.call_args_list[1].args[0] == ["/opt/mo", "analyze", "--json", temp]
        assert result["coverage"] == "partial"

    def test_remote_on_the_fly_backend_or_control_bytes_are_rejected(self) -> None:
        for remote in (":s3:bucket", "--delete", "remote:path\nsecret"):
            with (
                patch("files_buddy_tools.shutil.which", return_value="/opt/rclone"),
                patch("files_buddy_tools.run_bounded") as run,
            ):
                with pytest.raises(ToolError):
                    observe("rclone", "lsjson", path=remote)
                run.assert_not_called()

    def test_local_scope_traversal_is_rejected_before_any_subprocess(self) -> None:
        for scope in ("/tmp/..", "/tmp/../etc"):
            with (
                self.subTest(scope=scope),
                patch("files_buddy_tools.shutil.which", return_value="/opt/mo"),
                patch("files_buddy_tools.run_bounded") as run,
            ):
                with pytest.raises(ToolError, match="traversal"):
                    observe("mole", "analyze", path=scope)
                run.assert_not_called()

    def test_subprocess_literal_argv_is_not_a_shell(self) -> None:
        marker = "$(printf should-not-execute) ; & `false`"
        result = run_bounded([sys.executable, "-c", "import sys; print(sys.argv[1])", marker])
        assert result["stdout"].strip() == marker
        assert result["exit_code"] == 0

    def test_subprocess_output_and_time_budgets(self) -> None:
        with pytest.raises(ToolError, match="byte budget"):
            run_bounded([sys.executable, "-c", "import sys; sys.stdout.write('x'*10000)"], max_output_bytes=100)
        with pytest.raises(ToolError, match="time budget"):
            run_bounded([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.1)

    def test_every_fixture_imports_through_cli(self) -> None:
        fixtures = [
            ("mole", "analyze", "1.73.0", "mole-analyze-partial"),
            ("mole", "status", "1.73.0", "mole-status"),
            ("mole", "history", "1.73.0", "mole-history"),
            ("fclones", "group", "0.35.0", "fclones-group"),
            ("dust", "tree", "1.2.7", "dust-tree"),
            ("f2", "preview", "2.2.2", "f2-preview"),
            ("rclone", "lsjson", "1.76.0", "rclone-lsjson"),
        ]
        for tool, operation, version, name in fixtures:
            with self.subTest(tool=tool, operation=operation):
                process = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "observe",
                        tool,
                        operation,
                        "--input",
                        str(FIXTURES / f"{name}.json"),
                        "--version",
                        version,
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                assert process.returncode == 0, process.stdout + process.stderr
                report = json.loads(process.stdout)
                assert report["schema_version"] == "2.0"
                assert report["savings"]["verified_reclaimed_bytes"] is None


class RuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.rules = {
            "rules": [
                {
                    "locations": [str(self.root)],
                    "filters": [{"extension": ["jpg", "png"]}],
                    "actions": [{"move": "Images/{name}.{extension}"}],
                }
            ]
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_literal_rule_validates_without_execution(self) -> None:
        result = validate_organize_rules(self.rules, self.root)
        assert result["valid"]
        assert not result["execution_allowed"]
        assert not (self.root / "Images").exists()

    def test_rule_scope_and_location_reject_parent_traversal(self) -> None:
        for root in (Path("/tmp/.."), Path("/tmp/../etc")):
            with self.subTest(root=root), pytest.raises(ToolError, match="traversal"):
                validate_organize_rules(self.rules, root)
        rules = copy.deepcopy(self.rules)
        rules["rules"][0]["locations"] = [str(self.root / "nested" / "..")]
        with pytest.raises(ToolError, match="traversal"):
            validate_organize_rules(rules, self.root)

    def test_shell_python_custom_and_simulation_actions_are_rejected(self) -> None:
        for action in ("shell", "python", "delete", "trash", "custom"):
            rules = copy.deepcopy(self.rules)
            rules["rules"][0]["actions"] = [{action: {"command": "printf unsafe", "run_in_simulation": True}}]
            with self.subTest(action=action), pytest.raises(ToolError):
                validate_organize_rules(rules, self.root)

    def test_template_expressions_and_traversal_are_rejected(self) -> None:
        for target in (
            "{name.__class__}",
            "{{ self.__init__.__globals__ }}",
            "{name!r}",
            "../outside/{name}",
            "/tmp/outside",
        ):
            rules = copy.deepcopy(self.rules)
            rules["rules"][0]["actions"] = [{"move": target}]
            with self.subTest(target=target), pytest.raises(ToolError):
                validate_organize_rules(rules, self.root)

    def test_custom_filters_multiple_roots_and_symlink_destination_are_rejected(self) -> None:
        rules = copy.deepcopy(self.rules)
        rules["rules"][0]["filters"] = [{"python": "True"}]
        with pytest.raises(ToolError):
            validate_organize_rules(rules, self.root)
        rules = copy.deepcopy(self.rules)
        rules["rules"][0]["locations"].append("/tmp")
        with pytest.raises(ToolError):
            validate_organize_rules(rules, self.root)
        (self.root / "Images").symlink_to(self.root.parent, target_is_directory=True)
        with pytest.raises(ToolError):
            validate_organize_rules(self.rules, self.root)


if __name__ == "__main__":
    unittest.main()
