import pytest


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    """Temporary repo structure with ROOT monkeypatched."""
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "mcp").mkdir()
    (tmp_path / "config").mkdir(exist_ok=True)
    (tmp_path / "planning/manifests").mkdir(parents=True, exist_ok=True)
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
    monkeypatch.setattr("wagents.docs.ROOT", tmp_path)
    monkeypatch.setattr("wagents.docs.DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr("wagents.docs.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    return tmp_path


@pytest.fixture
def sample_skill_content():
    """Valid SKILL.md content string."""
    return "---\nname: test-skill\ndescription: A test skill\n---\n\n# Test Skill\n\nBody here.\n"
