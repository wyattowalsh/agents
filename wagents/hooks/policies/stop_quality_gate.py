"""Resolve the Stop-time quality-gate command.

The ``stop-quality-gate`` policy wraps the repo's ``verify-before-stop.sh`` shell
gate so harnesses without a native Stop hook (or that prefer the unified runner)
can reuse it. This module keeps the path/argv resolution pure so the dispatcher
can run it and tests can assert the command shape without executing anything.
"""

from __future__ import annotations

from pathlib import Path

_GATE_SCRIPT_REL = "hooks/verify-before-stop.sh"


def quality_gate_command(repo_root: str | Path) -> list[str] | None:
    """Return the argv for the Stop quality gate, or ``None`` if unavailable."""
    root = Path(repo_root)
    script = root / _GATE_SCRIPT_REL
    if not script.is_file():
        return None
    return ["bash", str(script)]
