import json

import pytest

from wagents.context import reset_cli_context


@pytest.fixture(autouse=True)
def _reset_wagents_cli_context():
    """Prevent CliRunner/bootstrap_cli_context repo_root from leaking across tests."""
    yield
    reset_cli_context()


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    """Temporary repo structure with ROOT monkeypatched."""
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "mcp").mkdir()
    (tmp_path / "config").mkdir(exist_ok=True)
    pyproject = '[project]\nname = "wagents"\nrequires-python = ">=3.13"\n'
    (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    (tmp_path / "planning/manifests").mkdir(parents=True, exist_ok=True)
    candidate_manifest_dir = tmp_path / "planning/manifests/candidate-corpus-jul2026"
    candidate_manifest_dir.mkdir(parents=True, exist_ok=True)
    runtime_artifacts = []
    for kind, total, accepted in (("cli", 30, 30), ("library", 1, 1), ("mcp", 17, 15), ("plugin", 17, 8)):
        runtime_artifacts.extend(
            {
                "artifact_id": f"fixture-{kind}-{index}",
                "kind": kind,
                "status": "accepted" if index < accepted else "incomplete",
            }
            for index in range(total)
        )
    (candidate_manifest_dir / "runtime-activation-assurance.json").write_text(
        json.dumps({
            "source_target_count": 289,
            "runtime_artifact_count": len(runtime_artifacts),
            "minimum_runtime_artifact_count": 65,
            "requested_full_usability": False,
            "artifacts": runtime_artifacts,
            "totals": {
                "status_counts": {"accepted": 54, "incomplete": 11},
                "kind_counts": {"cli": 30, "library": 1, "mcp": 17, "plugin": 17},
            },
            "active_blockers": [
                {"artifact_id": artifact["artifact_id"]}
                for artifact in runtime_artifacts
                if artifact["status"] == "incomplete"
            ],
        }),
        encoding="utf-8",
    )
    (tmp_path / "config/harness-surface-registry.json").write_text('{"harnesses": []}', encoding="utf-8")
    (tmp_path / "planning/manifests/harness-fixture-support.json").write_text('{"records": []}', encoding="utf-8")
    monkeypatch.setattr("wagents.ROOT", tmp_path)
    monkeypatch.setattr("wagents.DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr("wagents.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    # Patch module-level ROOT imports in submodules
    monkeypatch.setattr("wagents.catalog.ROOT", tmp_path)
    monkeypatch.setattr("wagents.cli.ROOT", tmp_path)
    monkeypatch.setattr("wagents.rendering.ROOT", tmp_path)
    monkeypatch.setattr("wagents.rendering.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.site_model.ROOT", tmp_path)
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", tmp_path / "docs/src/authoring/skills")
    monkeypatch.setattr(
        "wagents.skill_index.CATALOG_INDEX_PATH",
        tmp_path / "docs/public/generated-registries/skills-catalog-index.json",
    )
    monkeypatch.setattr(
        "wagents.skill_index.CATALOG_BROWSER_INDEX_PATH",
        tmp_path / "docs/public/generated-registries/skills-catalog-browser-index.json",
    )
    monkeypatch.setattr("wagents.authoring_sync.AUTHORING_SKILLS_DIR", tmp_path / "docs/src/authoring/skills")
    monkeypatch.setattr("wagents.docs.ROOT", tmp_path)
    monkeypatch.setattr("wagents.docs.DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr("wagents.docs.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.docs_catalog.ROOT", tmp_path)
    monkeypatch.setattr("wagents.docs_catalog.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.docs_catalog.CATALOG_CONTENT_DIR", tmp_path / "docs/src/content/docs/catalog")
    monkeypatch.setattr(
        "wagents.docs_catalog.ARCHITECTURE_CONTENT_DIR",
        tmp_path / "docs/src/content/docs/architecture",
    )
    return tmp_path


@pytest.fixture
def sample_skill_content():
    """Valid SKILL.md content string."""
    return "---\nname: test-skill\ndescription: A test skill\n---\n\n# Test Skill\n\nBody here.\n"
