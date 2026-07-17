"""Unit tests for validate collectors."""

from __future__ import annotations

from pathlib import Path

from scripts.validate.collectors.quarantine import (
    _status_is_hard_blocked,
    collect_quarantine_errors,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_collect_quarantine_errors_returns_list() -> None:
    issues = collect_quarantine_errors(REPO_ROOT)
    assert isinstance(issues, list)


def test_status_is_hard_blocked_prefixes() -> None:
    assert _status_is_hard_blocked("hard-blocked-quarantine")
    assert _status_is_hard_blocked("global-only")
    assert _status_is_hard_blocked("avoid")
    assert not _status_is_hard_blocked("install-now-after-trust-gate")
    assert not _status_is_hard_blocked("")


def test_collect_quarantine_flags_hard_blocked_install_command(tmp_path: Path) -> None:
    """Authoring hard-blocked rows with install_command are policy errors."""
    import json

    from scripts.validate.collectors import quarantine as q

    register = {
        "quarantine_triggers": ["malware"],
        "external_repo_records": [],
    }
    reg_path = tmp_path / "planning/manifests/security-quarantine-register.json"
    reg_path.parent.mkdir(parents=True)
    reg_path.write_text(json.dumps(register), encoding="utf-8")
    authoring = tmp_path / "docs/src/authoring/skills"
    authoring.mkdir(parents=True)
    (authoring / "bad-skill.mdx").write_text(
        "---\n"
        "name: bad-skill\n"
        "description: test\n"
        "status: hard-blocked-quarantine\n"
        'install_command: "npx skills add github:evil/repo --skill bad"\n'
        "---\n"
        "body\n",
        encoding="utf-8",
    )
    issues = q.collect_quarantine_errors(tmp_path)
    assert any(
        "install_command" in i.get("message", "") and "hard-blocked" in i.get("message", "")
        for i in issues
    ), issues
