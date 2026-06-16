"""Ensure skill directories do not depend on the wagents CLI."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

ALLOWED_PATH_FRAGMENTS = (
    "skills/skill-creator/scripts/package.py",
    "skills/skill-creator/scripts/generate_check.py",
    "skills/skill-creator/scripts/asset_toolkit/validate_hooks.py",
)

# Portable skills must not import or shell out to the repo wagents CLI.
WAGENTS_VIOLATION_RES = (
    re.compile(r"^\s*(?:from|import)\s+wagents\b", re.IGNORECASE),
    re.compile(r"\buv\s+run\s+wagents\b", re.IGNORECASE),
    re.compile(r"\bwagents\.[a-z_]+\b", re.IGNORECASE),
)


def _is_allowed(path: Path) -> bool:
    posix = path.as_posix()
    return any(fragment in posix for fragment in ALLOWED_PATH_FRAGMENTS)


def test_skills_have_no_wagents_references() -> None:
    violations: list[str] = []
    for path in sorted(SKILLS_DIR.rglob("*")):
        if not path.is_file():
            continue
        if _is_allowed(path):
            continue
        if path.suffix not in {".md", ".py", ".json", ".html", ".mdx"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(pat.search(line) for pat in WAGENTS_VIOLATION_RES):
                violations.append(f"{path.relative_to(ROOT)}:{line_no}: {line.strip()}")
    assert not violations, "wagents references under skills/:\n" + "\n".join(violations)