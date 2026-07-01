"""Namer CLI split: availability.py + standard check.py."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_namer_availability_script_exists() -> None:
    path = ROOT / "skills" / "namer" / "scripts" / "availability.py"
    assert path.is_file(), "namer must ship scripts/availability.py for CLI checks"


def test_namer_check_is_validator() -> None:
    text = (ROOT / "skills" / "namer" / "scripts" / "check.py").read_text(encoding="utf-8")
    assert "def _portable_ci" in text
    assert "typer" not in text.lower()


def test_namer_skill_references_availability() -> None:
    body = (ROOT / "skills" / "namer" / "SKILL.md").read_text(encoding="utf-8")
    assert "availability.py" in body


def test_namer_availability_usage_references_availability_script() -> None:
    text = (ROOT / "skills" / "namer" / "scripts" / "availability.py").read_text(encoding="utf-8")
    assert "skills/namer/scripts/availability.py check-all" in text
    assert "skills/namer/scripts/check.py check-" not in text


def test_namer_catalog_references_availability() -> None:
    mdx = ROOT / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "custom" / "namer.mdx"
    if mdx.is_file():
        assert "availability.py" in mdx.read_text(encoding="utf-8")
