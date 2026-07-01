"""Context injected when a subagent starts (Cursor ``subagentStart`` surface)."""

from __future__ import annotations


def subagent_start_context(git_context: str, *, source: str = "config/hook-registry.json") -> str:
    """Return the additional-context string for a starting subagent.

    ``git_context`` is a short repo-state summary computed by the dispatcher.
    """
    git_context = git_context.strip() or "no repository context available"
    return (
        f"Subagent session context: {git_context}; managed hooks source={source}. "
        "Inherit repository conventions: use uv for Python, prefer absolute imports, "
        "and validate changes before reporting completion."
    )
