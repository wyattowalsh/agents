"""Collect agent validation errors via the domain validator subprocess."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def collect_agent_errors(repo_root: Path) -> list[dict[str, str]]:
    """Run agent-conventions validate_agent.py and return parsed errors."""
    script = repo_root / "skills" / "agent-conventions" / "scripts" / "validate_agent.py"
    agents_dir = repo_root / "agents"
    has_agents = agents_dir.is_dir() and any(agents_dir.glob("*.md"))
    if not script.is_file():
        if has_agents:
            return [
                {
                    "source": str(script),
                    "message": "agent validator script not found",
                }
            ]
        return []

    result = subprocess.run(
        [sys.executable, str(script), "--format", "json", "--check-index"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout = result.stdout.strip()
    if stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            return [
                {
                    "source": "validate_agent",
                    "message": f"invalid JSON from agent validator (exit {result.returncode})",
                }
            ]
        errors = payload.get("errors", [])
        if isinstance(errors, list):
            return [item for item in errors if isinstance(item, dict)]
        return [{"source": "validate_agent", "message": "agent validator returned invalid errors list"}]

    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit code {result.returncode}"
        return [{"source": "validate_agent", "message": detail}]

    return []
