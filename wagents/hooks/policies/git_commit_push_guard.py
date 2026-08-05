"""Block high-risk git commit/push side effects and agent attribution trailers.

The agent stack policy is: never rewrite published history, never force-push to a
protected branch, never bypass commit hooks unless a human explicitly opted in,
and never sign commits with automated agent attribution trailers (Cursor, etc.).
This guard inspects a normalized shell command string and returns an actionable
reason when the command crosses one of those lines.
"""

from __future__ import annotations

import re

_PROTECTED_BRANCHES = ("main", "master")

_FORCE_PUSH_RE = re.compile(r"\bgit\s+push\b[^\n|;&]*\s(?:--force\b(?!-with-lease)|-f\b)")
_PUSH_RE = re.compile(r"\bgit\s+push\b")
_HARD_RESET_RE = re.compile(r"\bgit\s+reset\s+--hard\b")
_HISTORY_REWRITE_RE = re.compile(r"\bgit\s+(?:rebase\b|filter-branch\b|filter-repo\b)")
_NO_VERIFY_RE = re.compile(r"\bgit\s+(?:commit|push)\b[^\n|;&]*\s--no-verify\b")
_NO_GPG_RE = re.compile(r"\bgit\s+commit\b[^\n|;&]*\s--no-gpg-sign\b")
_COMMIT_RE = re.compile(r"\bgit\s+commit\b", re.I)

# Agent attribution fingerprints (never-sign policy).
_CURSOR_COAUTHOR_RE = re.compile(
    r"Co-authored-by\s*:\s*.*\bCursor\b",
    re.I,
)
_CURSOR_MADE_WITH_RE = re.compile(
    r"Made-with\s*:\s*Cursor\b",
    re.I,
)
_CURSOR_GENERATED_RE = re.compile(
    r"(?:Generated-by|Signed-off-by)\s*:\s*.*\bCursor\b",
    re.I,
)


def _targets_protected_branch(command: str) -> bool:
    return any(re.search(rf"\b{branch}\b", command) for branch in _PROTECTED_BRANCHES)


def _agent_attribution_reason(command: str) -> str | None:
    """Return a deny reason when a commit command embeds agent attribution trailers."""
    if not _COMMIT_RE.search(command):
        return None
    if (
        _CURSOR_COAUTHOR_RE.search(command)
        or _CURSOR_MADE_WITH_RE.search(command)
        or _CURSOR_GENERATED_RE.search(command)
    ):
        return (
            "Agent attribution trailer detected (Cursor Co-authored-by / Made-with). "
            "Never sign or add self-attribution; strip the trailer and retry the commit."
        )
    return None


def evaluate_git_commit_push(command: str) -> str | None:
    """Return a deny reason for a dangerous git commit/push command, else ``None``."""
    if not command or "git" not in command:
        return None

    attribution = _agent_attribution_reason(command)
    if attribution:
        return attribution

    if _FORCE_PUSH_RE.search(command):
        if _targets_protected_branch(command):
            return (
                "Force-pushing to a protected branch (main/master) rewrites shared history. "
                "Use a feature branch and open a PR, or request explicit approval for a force push."
            )
        return (
            "Force push detected. Prefer 'git push --force-with-lease' and confirm the branch is "
            "not shared before overwriting remote history."
        )

    if _NO_VERIFY_RE.search(command):
        return (
            "Skipping git hooks with --no-verify bypasses pre-commit/pre-push safety gates. "
            "Run the hooks, or request explicit approval to bypass them."
        )

    if _NO_GPG_RE.search(command):
        return (
            "Skipping commit signing with --no-gpg-sign is not allowed by default. "
            "Request explicit approval before disabling signing."
        )

    if _HISTORY_REWRITE_RE.search(command) and _targets_protected_branch(command):
        return (
            "Rewriting history on a protected branch (main/master) is destructive. Operate on a feature branch instead."
        )

    if _HARD_RESET_RE.search(command) and _PUSH_RE.search(command):
        return "Combining 'git reset --hard' with a push can destroy work. Split the operations and confirm intent."

    return None
