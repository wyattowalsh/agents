"""Tests for local skill indexing and routing."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from wagents.cli import app

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_INDEX_SCRIPT = REPO_ROOT / "skills" / "skill-router" / "scripts" / "skill_index.py"

runner = CliRunner()


def _load_skill_index_module():
    spec = importlib.util.spec_from_file_location("skill_router_index", SKILL_INDEX_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


skill_index = _load_skill_index_module()


def _write_skill(base: Path, name: str, description: str, body: str = "Body text.") -> Path:
    skill_dir = base / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{body}\n")
    return skill_dir


def _run_skill_index(
    *args: str,
    repo: Path,
    home: Path,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SKILL_INDEX_SCRIPT),
        *args,
        "--repo-root",
        str(repo),
        "--home",
        str(home),
    ]
    if cwd is not None:
        command.extend(["--cwd", str(cwd)])
    return subprocess.run(command, check=False, text=True, capture_output=True, cwd=repo)


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

    records = skill_index.collect_skill_records(root=repo, home=home, cwd=repo)

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

    results = skill_index.search_skills("skill-router", root=repo, home=home, cwd=repo)

    assert results[0].record.name == "skill-router"
    assert "name" in results[0].matched_fields
    assert results[0].score > 50


def test_read_skill_accepts_name_and_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    skill_dir = _write_skill(repo / "skills", "files-buddy", "Use when working with files.", "Read and edit files.")

    by_name = skill_index.read_skill("files-buddy", root=repo, home=home, cwd=repo)
    by_path = skill_index.read_skill(str(skill_dir / "SKILL.md"), root=repo, home=home, cwd=repo)

    assert by_name.body.startswith("# files-buddy")
    assert by_path.name == "files-buddy"


def test_doctor_report_counts_roots_and_warnings(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    skill_dir = _write_skill(repo / "skills", "scripted-skill", "Use when scripts exist.")
    (skill_dir / "scripts").mkdir()

    report = skill_index.doctor_report(root=repo, home=home, cwd=repo)

    assert report["skill_count"] == 1
    assert report["warning_count"] == 1
    assert any(row["source"] == "repo" and row["skill_count"] == 1 for row in report["roots"])


def test_skill_index_search_cli_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    _write_skill(repo / "skills", "skill-router", "Use when routing to the right skill.")

    result = _run_skill_index(
        "search", "routing", "--source", "repo", "--format", "json", repo=repo, home=home, cwd=repo
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["count"] == 1
    assert payload["skills"][0]["name"] == "skill-router"


def test_skill_index_context_cli_includes_body(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    _write_skill(repo / "skills", "skill-router", "Use when routing to the right skill.", "Route with context.")

    result = _run_skill_index("context", "routing", "--source", "repo", repo=repo, home=home, cwd=repo)

    assert result.returncode == 0, result.stderr or result.stdout
    assert "Skill context for 'routing'" in result.stdout
    assert "Route with context." in result.stdout


def test_wagents_skills_search_cli_json(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    _write_skill(repo / "skills", "skill-router", "Use when routing to the right skill.")

    monkeypatch.setattr("wagents.ROOT", repo)
    monkeypatch.setattr("wagents.cli.ROOT", repo)
    monkeypatch.setattr("wagents.cli.Path.home", lambda: home)
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["skills", "search", "routing", "--source", "repo", "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["count"] == 1
    assert payload["skills"][0]["name"] == "skill-router"
    script_results = skill_index.search_skills("routing", root=repo, home=home, cwd=repo, source="repo")
    assert script_results[0].record.name == "skill-router"