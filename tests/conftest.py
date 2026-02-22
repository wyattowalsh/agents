import pytest


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    """Temporary repo structure with ROOT monkeypatched."""
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "mcp").mkdir()
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
