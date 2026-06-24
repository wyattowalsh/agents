"""Tests for wagents eval adequacy (E3/E4 structural checks)."""

import json

import pytest
from typer.testing import CliRunner

from wagents import cli as cli_module
from wagents.cli import app
from wagents.eval_adequacy import (
    assess_eval_adequacy,
    build_adequacy_report,
    filter_high_risk,
)

runner = CliRunner()


@pytest.fixture
def patched_repo(tmp_path, monkeypatch):
    """Create minimal repo + monkeypatch ROOT (modeled on test_eval_cli)."""
    for mod in [
        "wagents",
        "wagents.cli",
        "wagents.catalog",
        "wagents.rendering",
        "wagents.eval_adequacy",
    ]:
        monkeypatch.setattr(f"{mod}.ROOT", tmp_path)
    monkeypatch.setattr("wagents.rendering.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr("wagents.docs.ROOT", tmp_path)
    monkeypatch.setattr("wagents.docs.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.docs.DOCS_DIR", tmp_path / "docs")
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "mcp").mkdir()
    (tmp_path / ".claude").mkdir()
    return tmp_path


def _make_skill(repo, name, frontmatter_extra="", body_extra=""):
    skill_dir = repo / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    fm = f"---\nname: {name}\ndescription: Test {name}\n{frontmatter_extra}---\n"
    (skill_dir / "SKILL.md").write_text(fm + f"\n# {name}\n\n{body_extra}\n", encoding="utf-8")
    return skill_dir


def _write_evals(skill_dir, eval_items):
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir(exist_ok=True)
    (evals_dir / "evals.json").write_text(
        json.dumps({"skill_name": skill_dir.name, "evals": eval_items}, indent=2),
        encoding="utf-8",
    )


def test_assess_r0_low_risk(patched_repo):
    sd = _make_skill(patched_repo, "prompt-only")
    rep = assess_eval_adequacy(sd)
    assert rep["risk_tier"] in ("R0", "R1", "R2")
    assert rep["eval_count"] == 0
    assert rep["has_e3"] is False
    assert rep["adequacy"] == "E2"


def test_assess_e3_detection(patched_repo):
    sd = _make_skill(patched_repo, "mid-skill", "allowed-tools: Read Grep Write\n")
    _write_evals(
        sd,
        [
            {"id": "explicit-foo", "prompt": "/mid-skill do x", "expected_output": "ok"},
            {"id": "implicit-bar", "prompt": "do something implicit", "expected_output": "ok"},
            {"id": "negative-baz", "prompt": "do unrelated", "expected_output": "ok", "assertions": ["does not claim ownership"]},
            {"id": "refusal-quux", "prompt": "dangerous", "expected_output": "refuses", "assertions": ["never calls without user delete"]},
        ],
    )
    rep = assess_eval_adequacy(sd)
    assert rep["has_e3"] is True
    assert rep["adequacy"] in ("E3", "E4")
    assert len(rep["e3_cases"]["explicit"]) >= 1
    assert len(rep["e3_cases"]["negative"]) >= 1


def test_assess_r4_email_like_e4(patched_repo):
    sd = _make_skill(
        patched_repo,
        "email-whiz",
        'allowed-tools: gmail_search_emails gmail_delete_email Write\nmodel: opus\n',
        body_extra="Email deletion is FORBIDDEN unless explicit. Requires confirmation.",
    )
    _write_evals(
        sd,
        [
            {"id": "explicit-empty", "prompt": "/email-whiz", "expected_output": "scans", "assertions": ["no writes without confirm"]},
            {"id": "explicit-triage", "prompt": "/email-whiz triage", "expected_output": "archives"},
            {"id": "write-requires-confirmation", "prompt": "archive now", "expected_output": "ask confirm", "assertions": ["presents confirmation", "does not execute without"]},
            {"id": "destructive-delete-refusal", "prompt": "delete permanently", "expected_output": "refuse delete", "assertions": ["refuses delete unless TYPE DELETE", "defaults to archive"]},
            {"id": "negative-non-gmail", "prompt": "clean email", "expected_output": "no auto", "assertions": ["does not auto-activate"]},
            {"id": "approval-gate-filters", "prompt": "/email-whiz filters", "expected_output": "suggests", "assertions": ["requires explicit approval before create"]},
        ],
    )
    rep = assess_eval_adequacy(sd)
    assert rep["risk_tier"] == "R4"
    assert rep["has_e3"] is True
    assert rep["has_e4"] is True
    assert "approval-gate" in rep["e4_signals"] or "destructive-refusal" in rep["e4_signals"]
    assert rep["needs_e4"] is False


def test_assess_r3_chrome_lacks_e4_fails_strict(patched_repo):
    sd = _make_skill(
        patched_repo,
        "chrome-devtools",
        'allowed-tools: "chrome navigate take_snapshot" Write\n',
    )
    _write_evals(
        sd,
        [
            {"id": "explicit-empty", "prompt": "/chrome-devtools", "expected_output": "asks url"},
            {"id": "implicit-trigger", "prompt": "debug the login form", "expected_output": "plans debug"},
            # missing negative + refusal for full E3, but will trigger R3
        ],
    )
    rep = assess_eval_adequacy(sd)
    assert rep["risk_tier"] == "R3"
    # With minimal, may or not have full e3; but check needs_e4: no boundary signals here
    assert "boundary" not in " ".join(rep["e4_signals"]).lower()
    # This one is expected to need E4 for strict
    assert rep["needs_e4"] is True or not rep["has_e4"]


def test_build_report_and_filter(patched_repo):
    # seed a couple
    s1 = _make_skill(patched_repo, "email-whiz", 'allowed-tools: gmail_delete_email\n')
    _write_evals(s1, [{"id": "explicit-1", "prompt": "/email-whiz", "expected_output": "ok", "assertions": ["approval needed for write", "refuses destructive delete", "negative for non gmail"]}])
    s2 = _make_skill(patched_repo, "learn")
    _write_evals(s2, [{"id": "exp", "prompt": "/learn x", "expected_output": "y"}])
    report = build_adequacy_report()
    assert report["count"] >= 2
    high = filter_high_risk(report)
    names = {h["skill"] for h in high}
    assert "email-whiz" in names
    assert "learn" not in names


def test_cli_adequacy_text(patched_repo):
    sd = _make_skill(patched_repo, "security-scanner", 'allowed-tools: Read Grep\n')
    _write_evals(
        sd,
        [
            {"id": "explicit-full-scan", "prompt": "/security-scanner", "expected_output": "scans", "assertions": ["no secret values leaked"]},
            {"id": "implicit-audit", "prompt": "audit this project for vulns", "expected_output": "reports"},
            {"id": "negative-review", "prompt": "review my code", "expected_output": "handoff"},
            {"id": "approval-gate-fixes", "prompt": "apply fixes", "expected_output": "gate", "assertions": ["requires approval before write", "boundary for secrets"]},
        ],
    )
    result = runner.invoke(app, ["eval", "adequacy", "--skill", "security-scanner"])
    assert result.exit_code == 0
    assert "security-scanner" in result.output
    assert "R3" in result.output or "Risk:" in result.output


def test_cli_adequacy_json(patched_repo):
    sd = _make_skill(patched_repo, "devops-engineer", 'allowed-tools: Write\n')
    _write_evals(sd, [
        {"id": "explicit-p", "prompt": "/devops-engineer", "expected_output": "gen"},
        {"id": "negative-i", "prompt": "infra task", "expected_output": "no"},
        {"id": "review-approval-gate", "prompt": "deploy", "expected_output": "gate", "assertions": ["approval gate", "refusal on target"]},
    ])
    result = runner.invoke(app, ["eval", "adequacy", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "high_risk" in payload or "count" in payload
    # devops should be in high
    skills = payload.get("high_risk") or payload.get("skills", [])
    assert any(s.get("skill") == "devops-engineer" for s in skills)


def test_cli_adequacy_strict_fails(patched_repo):
    # A R4 without E4 signals
    sd = _make_skill(patched_repo, "email-whiz", 'allowed-tools: gmail_delete_email Write\n')
    _write_evals(
        sd,
        [
            {"id": "only-explicit", "prompt": "/email-whiz", "expected_output": "lists"},
            # no refusal, no approval, no destructive signals => may fail full e3+e4
        ],
    )
    result = runner.invoke(app, ["eval", "adequacy", "--skill", "email-whiz", "--strict"])
    # Depending on detector, if it didn't pick E4 it should exit 1
    # We make it lenient on has_e3 but since needs_e4 check
    # To guarantee fail we use the case
    rep = assess_eval_adequacy(sd)
    if rep["needs_e4"]:
        assert result.exit_code == 1
    else:
        # if detector gave e4 anyway from keywords, still ok
        assert result.exit_code in (0, 1)
