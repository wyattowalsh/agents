"""Block high-risk git commit/push side effects.

The agent stack policy is: never rewrite published history, never force-push to a
protected branch, and never bypass commit hooks unless a human explicitly opted
in. This guard inspects a normalized shell command string and returns an
actionable reason when the command crosses one of those lines.
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


def _targets_protected_branch(command: str) -> bool:
    return any(re.search(rf"\b{branch}\b", command) for branch in _PROTECTED_BRANCHES)


def evaluate_git_commit_push(command: str) -> str | None:
    """Return a deny reason for a dangerous git commit/push command, else ``None``."""
    if not command or "git" not in command:
        return None

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
            "Rewriting history on a protected branch (main/master) is destructive. "
            "Operate on a feature branch instead."
        )

    if _HARD_RESET_RE.search(command) and _PUSH_RE.search(command):
        return (
            "Combining 'git reset --hard' with a push can destroy work. "
            "Split the operations and confirm intent."
        )

    return None
