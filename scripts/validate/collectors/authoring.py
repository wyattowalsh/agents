"""Collect catalog authoring validation errors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from _toolkit import ensure_validate_importable

ensure_validate_importable()

from wagents.external_skills import curated_external_authoring_errors, is_external_authoring_source_kind
from wagents.parsing import parse_frontmatter

if TYPE_CHECKING:
    from pathlib import Path


def collect_authoring_errors(repo_root: Path) -> list[dict[str, str]]:
    """Return validation errors for catalog authoring frontmatter."""
    authoring_dir = repo_root / "docs" / "src" / "authoring" / "skills"
    if not authoring_dir.is_dir():
        return []

    errors: list[dict[str, str]] = []
    for path in sorted(authoring_dir.glob("*.mdx")):
        try:
            frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append({"source": str(path), "message": f"Invalid authoring frontmatter: {exc}"})
            continue
        if is_external_authoring_source_kind(frontmatter.get("source_kind")):
            errors.extend(curated_external_authoring_errors(str(path), frontmatter))
    return errors
