"""Tests for curated external install pin helpers."""

from wagents.external_skills import (
    install_source_spec_has_pin,
    skills_cli_install_source_from_command,
    sync_apply_pin_satisfied,
)


def test_install_source_spec_has_pin_detects_github_ref() -> None:
    assert install_source_spec_has_pin("github:owner/repo@abc123def")
    assert not install_source_spec_has_pin("owner/repo")
    assert not install_source_spec_has_pin("")


def test_sync_apply_pin_satisfied_accepts_audited_head_without_at_ref() -> None:
    cmd = "npx skills add owner/repo --skill demo -y -g -a codex"
    assert sync_apply_pin_satisfied(install_command=cmd, audited_head="deadbeef")
    assert not sync_apply_pin_satisfied(install_command=cmd, audited_head="")


def test_sync_apply_pin_satisfied_accepts_pinned_npx_source() -> None:
    cmd = "npx skills add owner/repo@cafef00d --skill demo -y -g -a codex"
    assert sync_apply_pin_satisfied(install_command=cmd, audited_head="")
    assert skills_cli_install_source_from_command(cmd) == "owner/repo@cafef00d"