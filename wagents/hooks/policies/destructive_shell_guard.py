"""Pure destructive shell command guard."""
from __future__ import annotations

import re


def evaluate_destructive_shell(command: str) -> str | None:
    if not command:
        return None
    checks = [
        (
            r"(sudo\s+)?rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\s+(/|~|\$HOME|/Users|/System|/Library|/etc|/var|/usr|\.\.|\./?$)",
            "rm -rf on a critical path is blocked.",
        ),
        (r"\bgit\s+reset\s+--hard\b", "git reset --hard is blocked because it destroys uncommitted work."),
        (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean -f is blocked because it permanently removes untracked files."),
        (r"\b(curl|wget)\b.*\|\s*(ba)?sh\b", "Piping a remote script to shell is blocked."),
        (
            r"\bgit\s+push\b(?=.*\s(--force(\s|$)|-f(\s|$)))(?=.*\s(main|master)(\s|$))(?!.*--force-with-lease)",
            "Force push to main/master is blocked. Use --force-with-lease after review.",
        ),
    ]
    for pattern, reason in checks:
        if re.search(pattern, command):
            return reason
    return None
