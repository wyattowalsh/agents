"""Collect external-skill quarantine policy violations."""

from __future__ import annotations

import json
from pathlib import Path


def _quarantined_repo_slugs(repo_root: Path) -> set[str]:
    path = repo_root / "planning/manifests/security-quarantine-register.json"
    if not path.is_file():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    slugs: set[str] = set()
    for record in payload.get("external_repo_records", []):
        if not isinstance(record, dict):
            continue
        if record.get("default_action") != "quarantine":
            continue
        repo = str(record.get("repo") or "").strip()
        if repo:
            slugs.add(repo.lower())
    return slugs


def collect_quarantine_errors(repo_root: Path) -> list[dict[str, str]]:
    """Fail when curated external skill sources reference hard-quarantined repos."""
    external_path = repo_root / "config/external-skills.md"
    if not external_path.is_file():
        return []

    text = external_path.read_text(encoding="utf-8").lower()
    errors: list[dict[str, str]] = []
    for slug in sorted(_quarantined_repo_slugs(repo_root)):
        if slug in text:
            errors.append({
                "source": "config/external-skills.md",
                "message": f"Hard-quarantined source '{slug}' must not appear in curated external skills",
            })
    return errors
