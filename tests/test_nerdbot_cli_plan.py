"""Focused tests for Nerdbot plan CLI contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

NERDBOT_ROOT = Path(__file__).resolve().parents[1] / "skills" / "nerdbot"
SRC_DIR = NERDBOT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nerdbot.cli import build_plan_payload, main  # noqa: E402
from nerdbot.contracts import VERSION  # noqa: E402


def test_query_and_audit_plan_gates_remain_read_only() -> None:
    for mode in ("query", "audit"):
        payload = build_plan_payload(mode, "./vault")
        gate_text = " ".join(payload["required_gates"]).lower()

        assert payload["read_only_default"] is True
        assert "execute" not in gate_text
        assert "destructive" not in gate_text
        assert "high-impact" not in gate_text


def test_audit_plan_guides_inventory_then_lint() -> None:
    payload = build_plan_payload("audit", "./kb with spaces")

    assert payload["suggested_next_commands"][0] == payload["suggested_next_command"]
    assert payload["suggested_next_argvs"][0] == payload["suggested_next_argv"]
    assert payload["suggested_next_argvs"] == [
        ["nerdbot", "inventory", "--root", "kb with spaces"],
        ["nerdbot", "lint", "--root", "kb with spaces", "--include-unlayered"],
    ]


def test_migrate_plan_includes_required_migration_safety_contracts() -> None:
    payload = build_plan_payload("migrate", "./legacy-vault")
    gate_text = " ".join(payload["required_gates"]).lower()

    for required in (
        "migration interview",
        "inversion",
        "rollback",
        "path consumers",
        "wikilinks",
        "aliases",
        "dataview",
        "cutover",
    ):
        assert required in gate_text


def test_plan_view_json_compact_emits_json_object(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["plan", "--mode", "audit", "--target", "./kb", "--view", "json", "--compact"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert captured.out.count("\n") == 1
    assert payload["mode"] == "audit"
    assert payload["suggested_next_argvs"][1][0:2] == ["nerdbot", "lint"]


def test_version_flag_prints_package_version(capsys) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 0
    assert captured.out == f"nerdbot {VERSION}\n"
    assert captured.err == ""


def test_invalid_plan_args_fail_without_json_stdout(capsys) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(SystemExit) as exc_info:
        main(["plan", "--mode", "not-a-mode", "--view", "json", "--compact"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "invalid choice" in captured.err
