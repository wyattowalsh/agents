"""Agent least-privilege: orchestrator + performance-profiler must not allow Bash."""

from __future__ import annotations

from pathlib import Path

from wagents.parsing import parse_frontmatter

REPO = Path(__file__).resolve().parents[1]


def test_orchestrator_and_profiler_disallow_bash() -> None:
    for rel in ("agents/orchestrator.md", "agents/performance-profiler.md"):
        text = (REPO / rel).read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
        tools = str(fm.get("tools") or "")
        disallowed = str(fm.get("disallowedTools") or fm.get("disallowed_tools") or "")
        assert "Bash" not in tools.split(","), f"{rel} still lists Bash in tools"
        assert "Bash" in disallowed or "bash" in disallowed.lower(), f"{rel} should disallowedTools Bash"
