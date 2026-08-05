"""Pin-gate contract for skills sync (session RV-008 / review RV-002)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from wagents.cli import (
    _partition_missing_for_pin_gate,
    _valid_sync_selector,
    apply_dry_run_pin_gate,
)

if TYPE_CHECKING:
    from wagents.installed_inventory import InstalledSkillInventoryRow


def _fake_row(
    *,
    name: str = "floating-skill",
    pinned: bool = False,
    audited: bool = False,
) -> InstalledSkillInventoryRow:
    class _Row:
        def __init__(self) -> None:
            self.name = name
            self.install_command = (
                "npx skills add github:org/repo@abc123 --skill floating-skill"
                if pinned
                else "npx skills add github:org/repo --skill floating-skill"
            )
            self.source = "github:org/repo" if not pinned else "github:org/repo@abc123"
            self.audited_head = "abc123" if pinned or audited else ""

        def is_verified_curated(self) -> bool:
            return True

        def is_repo_skill(self) -> bool:
            return False

    return cast("InstalledSkillInventoryRow", _Row())


def test_dry_run_soft_lists_pin_blocked_without_failing() -> None:
    """Default soft dry-run leaves ok=True when only pin_blocked exists."""
    missing = [_fake_row(pinned=False)]
    kept, blocked = _partition_missing_for_pin_gate(missing, accept_floating=False)
    assert kept == []
    assert len(blocked) == 1
    report: dict[str, object] = {
        "ok": True,
        "pin_blocked_count": len(blocked),
        "pin_gate": "Install-now curated skills without an explicit @ref are blocked on apply.",
    }
    apply_dry_run_pin_gate(report, strict_pin=False, accept_floating=False)
    assert report["ok"] is True
    assert report["pin_blocked_count"] == 1
    assert "error_type" not in report


def test_strict_pin_dry_run_fails() -> None:
    """Production helper fails dry-run when strict_pin and pin_blocked_count > 0."""
    report: dict[str, object] = {
        "ok": True,
        "pin_blocked_count": 2,
        "pin_gate": "blocked floating install-now",
    }
    out = apply_dry_run_pin_gate(report, strict_pin=True, accept_floating=False)
    assert out is report
    assert report["ok"] is False
    assert report["error_type"] == "pin-gate"
    assert "blocked" in str(report.get("error") or "").lower() or "floating" in str(report.get("error") or "").lower()


def test_strict_pin_respects_accept_floating() -> None:
    report: dict[str, object] = {"ok": True, "pin_blocked_count": 2, "pin_gate": "blocked"}
    apply_dry_run_pin_gate(report, strict_pin=True, accept_floating=True)
    assert report["ok"] is True
    assert "error_type" not in report


def test_apply_still_hard_blocks_without_accept_floating() -> None:
    missing = [_fake_row(pinned=False)]
    kept, blocked = _partition_missing_for_pin_gate(missing, accept_floating=False)
    assert not kept
    assert blocked
    kept2, blocked2 = _partition_missing_for_pin_gate(missing, accept_floating=True)
    assert kept2
    assert not blocked2


def test_audited_head_does_not_authorize_a_floating_apply() -> None:
    kept, blocked = _partition_missing_for_pin_gate(
        [_fake_row(pinned=False, audited=True)],
        accept_floating=False,
    )
    assert kept == []
    assert len(blocked) == 1


@pytest.mark.parametrize("selector", ["plain-skill", "opsx:tdd", "vendor:group:skill-name"])
def test_logical_selector_accepts_only_colon_separated_kebab_segments(selector: str) -> None:
    assert _valid_sync_selector(selector)


@pytest.mark.parametrize(
    "selector",
    [
        "",
        ":opsx",
        "opsx:",
        "opsx::tdd",
        "opsx:tdd/escape",
        r"opsx:tdd\escape",
        "opsx:.tdd",
        "opsx:-tdd",
        "--skill",
        "opsx tdd",
        f"opsx:{'x' * 60}",
    ],
)
def test_logical_selector_rejects_empty_path_dot_option_and_oversized_forms(selector: str) -> None:
    assert not _valid_sync_selector(selector)
