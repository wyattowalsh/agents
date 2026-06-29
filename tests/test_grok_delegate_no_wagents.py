"""Ensure grok-delegate preflight path has zero wagents dependency."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "skills" / "grok-delegate" / "scripts"

FORBIDDEN = ("wagents", "uv run")

TARGETS = (
    SCRIPT_DIR / "preflight.sh",
    SCRIPT_DIR / "doctor.py",
    SCRIPT_DIR / "auth_lib.py",
    SCRIPT_DIR / "auth_verify.sh",
)


def test_no_wagents_in_preflight_scripts() -> None:
    violations: list[str] = []
    for path in TARGETS:
        text = path.read_text(encoding="utf-8")
        for needle in FORBIDDEN:
            if needle in text:
                violations.append(f"{path.name}: contains {needle!r}")
    assert not violations, "\n".join(violations)