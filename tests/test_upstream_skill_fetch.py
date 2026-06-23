"""Mocked tests for wagents.upstream_skill_fetch."""

from __future__ import annotations

from unittest import mock

from wagents.external_skills import ExternalSkillEntry
from wagents.upstream_skill_fetch import (
    _candidate_paths,
    _parse_github_source,
    _redact_local_paths,
    fetch_upstream_skill,
)


def _curated_entry(name: str, install_source: str, source: str = "") -> ExternalSkillEntry:
    return ExternalSkillEntry(
        name=name,
        source=source or install_source,
        install_source=install_source,
        status="install-now-after-trust-gate",
        trust_tier="low",
        provenance_status="verified-install-command",
        install_command=f"npx skills add {install_source} --skill {name} -y -g",
        target_agents=("claude-code", "opencode"),
        source_url="",
        notes=f"Test curated {name}",
    )


def test_parse_github_source_variants():
    assert _parse_github_source("example-org/example-skills") == ("example-org", "example-skills")
    assert _parse_github_source("github:PaulRBerg/agent-skills@d3f5540") == ("PaulRBerg", "agent-skills")
    assert _parse_github_source("backnotprop/plannotator/apps/skills/core") == ("backnotprop", "plannotator")
    assert _parse_github_source("https://example.com") is None
    assert _parse_github_source("") is None


def test_candidate_paths_includes_skills_and_fallbacks():
    c = _candidate_paths("demo-skill", "example-org/example-skills")
    assert any("skills/demo-skill/SKILL.md" in p for p in c)
    assert any(p.endswith("/SKILL.md") for p in c)
    assert "SKILL.md" in c


def test_redact_local_paths():
    txt = "See /Users/ww/dev/foo and /home/user/bar and normal https://github.com"
    red = _redact_local_paths(txt)
    assert "[REDACTED_LOCAL_PATH]" in red
    assert "/Users/ww" not in red
    assert "https://github.com" in red


def test_fetch_upstream_skill_writes_redacted_on_success(tmp_path, monkeypatch):
    monkeypatch.setattr("wagents.upstream_skill_fetch.DOCS_DIR", tmp_path / "docs")
    # re-compute UPSTREAM_DIR? import after? patch the constant
    import wagents.upstream_skill_fetch as mod

    mod.UPSTREAM_DIR = tmp_path / "docs" / "src" / "skill-upstream"
    entry = _curated_entry("demo-skill", "example/demo-repo")

    fake_content = "# Demo Skill\n\nProblem: does X.\nLocal path: /Users/secret/should/redact\n"
    fake_resp = mock.Mock()
    fake_resp.status = 200
    fake_resp.read.return_value = fake_content.encode("utf-8")
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = lambda *a: False

    with mock.patch("urllib.request.urlopen", return_value=fake_resp) as urlopen:
        result = fetch_upstream_skill("demo-skill", entry)

    assert result is not None
    assert result.exists()
    assert result.parent == (tmp_path / "docs" / "src" / "skill-upstream")
    text = result.read_text(encoding="utf-8")
    assert "skill: demo-skill" in text or "demo-skill" in text
    assert "[REDACTED_LOCAL_PATH]" in text
    assert "/Users/secret" not in text
    assert urlopen.called


def test_fetch_upstream_skill_returns_none_for_non_github(tmp_path, monkeypatch):
    monkeypatch.setattr("wagents.upstream_skill_fetch.DOCS_DIR", tmp_path / "docs")
    import wagents.upstream_skill_fetch as mod

    mod.UPSTREAM_DIR = tmp_path / "docs" / "src" / "skill-upstream"
    entry = _curated_entry("localish", "/abs/local/path")
    result = fetch_upstream_skill("localish", entry)
    assert result is None


def test_fetch_upstream_skill_none_when_all_404(monkeypatch, tmp_path):
    monkeypatch.setattr("wagents.upstream_skill_fetch.DOCS_DIR", tmp_path / "docs")
    import wagents.upstream_skill_fetch as mod

    mod.UPSTREAM_DIR = tmp_path / "docs" / "src" / "skill-upstream"
    entry = _curated_entry("missing", "ghost/repo")

    def fake_open(url, **kw):
        raise Exception("404 simulated")

    with mock.patch("urllib.request.urlopen", side_effect=fake_open):
        assert fetch_upstream_skill("missing", entry) is None
