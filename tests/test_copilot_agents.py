"""Tests for GitHub Copilot agent corpus parity with canonical agents."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COPILOT_AGENTS_DIR = ROOT / "platforms" / "copilot" / "agents"
CANONICAL_AGENTS_DIR = ROOT / "agents"

CANONICAL_AGENT_NAMES = sorted(
    path.stem for path in CANONICAL_AGENTS_DIR.glob("*.md") if path.name != "README.md"
)

COPILOT_ONLY_SPECIALISTS = {
    "codebase-oracle",
    "dependency-checker",
    "git-workflow",
    "spec-writer",
    "test-writer",
}


def _load_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    block = text.split("---", 2)[1]
    data = yaml.safe_load(block)
    assert isinstance(data, dict)
    return data


def test_copilot_canonical_agents_present() -> None:
    copilot_names = {path.stem.removesuffix(".agent") for path in COPILOT_AGENTS_DIR.glob("*.agent.md")}
    missing = set(CANONICAL_AGENT_NAMES) - copilot_names
    assert not missing, f"Copilot corpus missing canonical agents: {sorted(missing)}"


def test_copilot_agent_names_match_filenames() -> None:
    for path in sorted(COPILOT_AGENTS_DIR.glob("*.agent.md")):
        frontmatter = _load_frontmatter(path)
        expected = path.stem.removesuffix(".agent")
        assert frontmatter.get("name") == expected, f"{path.name}: name field must be {expected!r}"


def test_copilot_specialists_are_documented_extensions() -> None:
    copilot_names = {path.stem.removesuffix(".agent") for path in COPILOT_AGENTS_DIR.glob("*.agent.md")}
    specialists = copilot_names - set(CANONICAL_AGENT_NAMES)
    assert specialists == COPILOT_ONLY_SPECIALISTS


def test_copilot_read_only_agents_disallow_write() -> None:
    read_only = {"code-reviewer", "orchestrator", "planner", "researcher", "security-auditor"}
    for name in read_only:
        path = COPILOT_AGENTS_DIR / f"{name}.agent.md"
        frontmatter = _load_frontmatter(path)
        disallowed = frontmatter.get("disallowedTools", "")
        assert "Write" in disallowed, f"{name} must disallow Write"
        assert "Edit" in disallowed, f"{name} must disallow Edit"