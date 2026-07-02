"""MCP server: changelog-digest.

Later-tier stub for read-only changelog digest summaries from repo history markers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from wagents import ROOT

mcp = FastMCP("Changelog Digest")

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def _recent_changelog_paths(limit: int = 5) -> list[str]:
    candidates = [
        ROOT / "CHANGELOG.md",
        ROOT / "docs" / "src" / "content" / "docs" / "reports" / "index.mdx",
    ]
    paths: list[str] = []
    for path in candidates:
        if path.is_file():
            paths.append(str(path.relative_to(ROOT)))
        if len(paths) >= limit:
            break
    return paths


@mcp.tool(annotations=_READ_ONLY)
def digest_status() -> dict[str, Any]:
    """Report stub status and candidate changelog source paths."""
    return {
        "status": "stub",
        "message": "Automated changelog digest is planned (W13).",
        "candidate_paths": _recent_changelog_paths(),
    }


@mcp.tool(annotations=_READ_ONLY)
def read_changelog_excerpt(max_lines: int = 40) -> str:
    """Read the first lines of CHANGELOG.md when present (read-only)."""
    path = ROOT / "CHANGELOG.md"
    if not path.is_file():
        return "CHANGELOG.md not found in repository root."
    lines = path.read_text(encoding="utf-8").splitlines()[: max(1, min(max_lines, 200))]
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
