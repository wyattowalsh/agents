from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "review" / "scripts"


def load_script(name: str) -> ModuleType:
    path = SCRIPT_DIR / name
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_review_scripts_are_importable() -> None:
    for script in [
        "finding-formatter.py",
        "learnings-store.py",
        "project-scanner.py",
        "review-store.py",
        "sarif-uploader.py",
    ]:
        load_script(script)


def test_project_scanner_skips_virtualenv_prefixes(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\ndependencies = []\n')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def app() -> str:\n    return 'ok'\n")
    (tmp_path / ".venv-copilot" / "lib").mkdir(parents=True)
    (tmp_path / ".venv-copilot" / "lib" / "vendor.py").write_text("def vendor():\n    return None\n")

    scanner = load_script("project-scanner.py")
    result = scanner.scan(tmp_path)
    paths = {entry["path"] for entry in result["files"]}

    assert "src/app.py" in paths
    assert not any(path.startswith(".venv-copilot/") for path in paths)


def run_script(
    name: str, *args: str, input_text: str = "", env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / name), *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        env=merged_env,
    )


def test_finding_formatter_parses_source_id_and_location() -> None:
    result = run_script(
        "finding-formatter.py",
        input_text=("P1 - RV-S-005 src/session.py:45-52 Correctness\n  Confidence: 0.9\n  Description: Missing lock\n"),
    )

    assert result.returncode == 0, result.stderr
    findings = json.loads(result.stdout)
    assert findings[0]["id"] == "RV-S-001"
    assert findings[0]["source_id"] == "RV-S-005"
    assert findings[0]["location"] == "src/session.py:45-52"
    assert findings[0]["category"] == "Correctness"
    assert findings[0]["confidence"] == 0.9


def test_finding_formatter_sarif_uses_priority_and_missing_confidence_default() -> None:
    payload = json.dumps([
        {"priority": "P0", "location": "src/a.py:1", "description": "critical", "confidence": 0.9},
        {"priority": "P1", "location": "src/b.py:2", "description": "warning"},
        {"priority": "P2", "location": "src/c.py:3", "description": "note"},
    ])
    result = run_script("finding-formatter.py", "--input", "-", "--format", "sarif", input_text=payload)

    assert result.returncode == 0, result.stderr
    results = json.loads(result.stdout)["runs"][0]["results"]
    assert [item["level"] for item in results] == ["error", "warning", "note"]
    assert results[1]["rank"] == 50


def test_finding_formatter_json_schema_outputs_schema() -> None:
    result = run_script("finding-formatter.py", "--format", "json-schema", input_text="[]")

    assert result.returncode == 0, result.stderr
    schema = json.loads(result.stdout)
    assert schema["title"] == "ReviewFinding"
    assert "properties" in schema


def test_learnings_store_does_not_suppress_same_prefix_different_file(tmp_path: Path) -> None:
    env = {"HOME": str(tmp_path)}
    add = run_script(
        "learnings-store.py",
        "add",
        "--project",
        "p",
        "--finding-id",
        "RV-S-001",
        "--pattern",
        "old issue",
        "--reason",
        "false positive",
        "--file-path",
        "src/old.py",
        "--category",
        "old",
        env=env,
    )
    assert add.returncode == 0, add.stderr

    payload = json.dumps([
        {
            "id": "RV-S-999",
            "location": "src/new.py:10",
            "category": "new",
            "description": "old issue",
            "confidence": 0.8,
        }
    ])
    check = run_script("learnings-store.py", "check", "--project", "p", input_text=payload, env=env)

    assert check.returncode == 0, check.stderr
    findings = json.loads(check.stdout)
    assert findings[0]["confidence"] == 0.8
    assert "suppressed_by" not in findings[0]


def test_learnings_store_check_is_read_only_unless_record_match(tmp_path: Path) -> None:
    env = {"HOME": str(tmp_path)}
    add = run_script(
        "learnings-store.py",
        "add",
        "--project",
        "p",
        "--finding-id",
        "RV-S-001",
        "--pattern",
        "missing lock",
        "--reason",
        "false positive",
        "--file-path",
        "src/session.py",
        "--category",
        "correctness",
        env=env,
    )
    assert add.returncode == 0, add.stderr

    learnings_path = tmp_path / ".claude" / "reviews" / "learnings" / "p.json"
    before = learnings_path.read_text()
    payload = json.dumps([
        {
            "id": "RV-S-999",
            "location": "src/session.py:45-52",
            "category": "correctness",
            "description": "missing lock around session update",
            "confidence": 0.8,
        }
    ])

    check = run_script("learnings-store.py", "check", "--project", "p", input_text=payload, env=env)

    assert check.returncode == 0, check.stderr
    findings = json.loads(check.stdout)
    assert findings[0]["confidence"] == 0.5
    assert findings[0]["suppressed_by"] == "L-001"
    assert learnings_path.read_text() == before

    recorded = run_script(
        "learnings-store.py",
        "check",
        "--project",
        "p",
        "--record-match",
        input_text=payload,
        env=env,
    )

    assert recorded.returncode == 0, recorded.stderr
    assert json.loads(learnings_path.read_text())[0]["match_count"] == 1


def test_review_store_keeps_same_day_reviews_and_avoids_id_collision(tmp_path: Path) -> None:
    env = {"HOME": str(tmp_path)}
    first = json.dumps([{"id": "RV-S-001", "location": "src/old.py:1", "category": "old", "description": "old issue"}])
    second = json.dumps([
        {"id": "RV-S-001", "location": "src/new.py:200", "category": "new", "description": "new issue"}
    ])

    save1 = run_script(
        "review-store.py",
        "save",
        "--project",
        "p",
        "--date",
        "2026-06-22",
        "--run-id",
        "one",
        input_text=first,
        env=env,
    )
    save2 = run_script(
        "review-store.py",
        "save",
        "--project",
        "p",
        "--date",
        "2026-06-22",
        "--run-id",
        "two",
        input_text=second,
        env=env,
    )
    assert save1.returncode == 0, save1.stderr
    assert save2.returncode == 0, save2.stderr

    review_files = sorted((tmp_path / ".claude" / "reviews").glob("*.json"))
    assert [path.name for path in review_files] == [
        "2026-06-22-p-session-one.json",
        "2026-06-22-p-session-two.json",
    ]

    store = load_script("review-store.py")
    diff = store.diff_findings(json.loads(first), json.loads(second))
    assert len(diff["new"]) == 1
    assert len(diff["recurring"]) == 0


def test_review_store_treats_nearby_ranges_as_recurring() -> None:
    store = load_script("review-store.py")
    old_findings = [
        {
            "id": "RV-S-001",
            "location": "src/session.py:45-52",
            "category": "correctness",
            "description": "missing lock",
        }
    ]
    new_findings = [
        {
            "id": "RV-S-002",
            "location": "src/session.py:47-54",
            "category": "correctness",
            "description": "missing session lock",
        }
    ]

    diff = store.diff_findings(old_findings, new_findings)

    assert diff["new"] == []
    assert diff["resolved"] == []
    assert diff["recurring"] == new_findings


def test_source_audit_redacts_credentials_and_avoids_keyword_false_positive(tmp_path: Path) -> None:
    skill = tmp_path / "candidate"
    skill.mkdir()
    (skill / "SKILL.md").write_text("Use explicit audit keyword but no secret here\nAPI_KEY=abcdef123456\n")

    result = run_script("source-audit.py", str(skill))

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    credential_findings = [item for item in report["findings"] if item["kind"] == "credential"]
    assert len(credential_findings) == 1
    assert "[REDACTED]" in credential_findings[0]["excerpt"]
    assert "abcdef123456" not in credential_findings[0]["excerpt"]


def test_sarif_uploader_validates_without_upload() -> None:
    sarif = json.dumps({"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "review"}}, "results": []}]})
    result = run_script("sarif-uploader.py", input_text=sarif)

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["status"] == "validated"
    assert output["upload"] is False


def test_read_only_review_agents_do_not_allow_bash() -> None:
    for rel in [
        "agents/code-reviewer.md",
        "agents/security-auditor.md",
        "platforms/copilot/agents/code-reviewer.agent.md",
        "platforms/copilot/agents/security-auditor.agent.md",
    ]:
        text = (ROOT / rel).read_text()
        frontmatter = text.split("---", 2)[1]
        assert "tools:" in frontmatter
        assert "Bash" not in frontmatter


def test_legacy_review_skills_are_removed_from_installable_surfaces() -> None:
    for name in ["honest-review", "simplify", "external-skill-auditor"]:
        assert not (ROOT / "skills" / name).exists()
        assert not (ROOT / "docs" / "src" / "authoring" / "skills" / f"{name}.mdx").exists()
        assert not (
            ROOT / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "custom" / f"{name}.mdx"
        ).exists()
        assert not (ROOT / "docs" / "src" / "skill-research" / f"{name}.md").exists()
