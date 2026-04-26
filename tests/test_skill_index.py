"""Tests for local skill indexing and routing."""

import json
from pathlib import Path

from typer.testing import CliRunner

from wagents.cli import app
from wagents.skill_index import collect_skill_records, doctor_report, read_skill, search_skills

runner = CliRunner()


def _write_skill(base: Path, name: str, description: str, body: str = "Body text.") -> Path:
    skill_dir = base / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{body}\n"
    )
    return skill_dir


def test_collect_skill_records_scans_known_roots_and_sources(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    _write_skill(repo / "skills", "repo-skill", "Use when working in the repo.")
    _write_skill(home / ".agents" / "skills", "global-skill", "Use when installed globally.")
    _write_skill(home / ".codex" / "skills", "codex-skill", "Use when installed for Codex.")
    _write_skill(
        home / ".codex" / "plugins" / "cache" / "openai-curated" / "demo" / "skills",
        "plugin-skill",
        "Use when plugin skills are needed.",
    )

    records = collect_skill_records(root=repo, home=home, cwd=repo)

    by_name = {record.name: record for record in records}
    assert by_name["repo-skill"].source == "repo"
    assert by_name["repo-skill"].trust_tier == "repo"
    assert by_name["global-skill"].source == "global"
    assert by_name["codex-skill"].source == "codex"
    assert by_name["plugin-skill"].source == "plugin"
    assert by_name["plugin-skill"].trust_tier == "openai-plugin"


def test_search_prefers_exact_and_description_matches(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    _write_skill(repo / "skills", "skill-router", "Use when choosing skills for an agent task.")
    _write_skill(repo / "skills", "python-conventions", "Use when editing Python code.")

    results = search_skills("skill-router", root=repo, home=home, cwd=repo)

    assert results[0].record.name == "skill-router"
    assert "name" in results[0].matched_fields
    assert results[0].score > 50


def test_read_skill_accepts_name_and_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    skill_dir = _write_skill(repo / "skills", "files-buddy", "Use when working with files.", "Read and edit files.")

    by_name = read_skill("files-buddy", root=repo, home=home, cwd=repo)
    by_path = read_skill(str(skill_dir / "SKILL.md"), root=repo, home=home, cwd=repo)

    assert by_name.body.startswith("# files-buddy")
    assert by_path.name == "files-buddy"


def test_doctor_report_counts_roots_and_warnings(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    skill_dir = _write_skill(repo / "skills", "scripted-skill", "Use when scripts exist.")
    (skill_dir / "scripts").mkdir()

    report = doctor_report(root=repo, home=home, cwd=repo)

    assert report["skill_count"] == 1
    assert report["warning_count"] == 1
    assert any(row["source"] == "repo" and row["skill_count"] == 1 for row in report["roots"])


def test_skills_search_cli_json(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    _write_skill(repo / "skills", "skill-router", "Use when routing to the right skill.")

    monkeypatch.setattr("wagents.skill_index.ROOT", repo)
    monkeypatch.setattr("wagents.skill_index.Path.home", lambda: home)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["skills", "search", "routing", "--source", "repo", "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["count"] == 1
    assert payload["skills"][0]["name"] == "skill-router"


def test_skills_context_cli_includes_body(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    _write_skill(repo / "skills", "skill-router", "Use when routing to the right skill.", "Route with context.")

    monkeypatch.setattr("wagents.skill_index.ROOT", repo)
    monkeypatch.setattr("wagents.skill_index.Path.home", lambda: home)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["skills", "context", "routing", "--source", "repo"])

    assert result.exit_code == 0, result.output
    assert "Skill context for 'routing'" in result.output
    assert "Route with context." in result.output
