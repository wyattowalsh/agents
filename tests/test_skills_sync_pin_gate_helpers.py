"""Pin-gate contract for skills sync (session RV-008 / review RV-002)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from wagents.cli import _partition_missing_for_pin_gate, apply_dry_run_pin_gate

if TYPE_CHECKING:
    from wagents.installed_inventory import InstalledSkillInventoryRow


def _fake_row(*, name: str = "floating-skill", pinned: bool = False) -> InstalledSkillInventoryRow:
    class _Row:
        def __init__(self) -> None:
            self.name = name
            self.install_command = (
                "npx skills add github:org/repo@abc123 --skill floating-skill"
                if pinned
                else "npx skills add github:org/repo --skill floating-skill"
            )
            self.source = "github:org/repo" if not pinned else "github:org/repo@abc123"
            self.audited_head = "" if not pinned else "abc123"

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
        "pin_gate": "Install-now curated skills without @ref pin or audited_head are blocked on apply.",
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
