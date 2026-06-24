"""Collect external-skill quarantine policy violations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def _quarantine_register_path(repo_root: Path) -> Path:
    return repo_root / "planning/manifests/security-quarantine-register.json"


def _load_quarantine_register(repo_root: Path) -> tuple[Path, dict | None, list[dict[str, str]]]:
    path = _quarantine_register_path(repo_root)
    if not path.is_file():
        return path, None, []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exercised through integration tests
        return path, None, [{"source": str(path), "message": f"Invalid quarantine register JSON: {exc}"}]
    if not isinstance(payload, dict):
        return path, None, [{"source": str(path), "message": "Invalid quarantine register JSON: expected object"}]
    return path, payload, []


def _quarantined_repo_slugs(payload: dict) -> set[str]:
    slugs: set[str] = set()
    for record in payload.get("external_repo_records", []):
        if not isinstance(record, dict):
            continue
        if record.get("default_action") != "quarantine":
            continue
        repo = str(record.get("repo") or "").strip()
        if repo:
            slugs.add(repo)
    return {s.lower() for s in slugs}


def _register_policy_errors(path: Path, payload: dict) -> list[dict[str, str]]:
    triggers = {str(t).strip() for t in payload.get("quarantine_triggers", []) if str(t).strip()}
    errors: list[dict[str, str]] = []
    for record in payload.get("external_repo_records", []):
        if not isinstance(record, dict):
            continue
        trigger = str(record.get("trigger") or "").strip()
        record_id = str(record.get("id") or record.get("repo") or "?")
        if not trigger:
            errors.append({
                "source": str(path),
                "message": f"Quarantine record {record_id} is missing a trigger",
            })
        elif trigger not in triggers:
            errors.append({
                "source": str(path),
                "message": f"Quarantine record {record_id} uses undeclared trigger '{trigger}'",
            })
    return errors


def collect_quarantine_errors(repo_root: Path) -> list[dict[str, str]]:
    """Fail when curated external skill sources reference hard-quarantined repos.

    Dual-read (W2): scan catalog index JSON entry fields (install_source, source, name, camel variants)
    + legacy md.
    """
    _register_path, payload, errors = _load_quarantine_register(repo_root)
    if payload is None:
        return errors

    errors.extend(_register_policy_errors(_register_path, payload))
    slugs = sorted(_quarantined_repo_slugs(payload))
    if not slugs:
        return errors

    # legacy md
    external_path = repo_root / "config/external-skills.md"
    if external_path.is_file():
        text = external_path.read_text(encoding="utf-8").lower()
        for slug in slugs:
            if slug in text:
                errors.append({
                    "source": "config/external-skills.md",
                    "message": f"Hard-quarantined source '{slug}' must not appear in curated external skills",
                })

    # catalog index JSON (dual-read)
    cat_index = repo_root / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
    if cat_index.is_file():
        try:
            data = json.loads(cat_index.read_text(encoding="utf-8"))
            for key in ("externalSkillIndex", "allSkillIndex", "customSkillIndex"):
                rows = data.get(key) or []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    for fld in ("install_source", "source", "name", "installSource", "sourceRoot", "source_url"):
                        val = str(row.get(fld) or "").lower()
                        for slug in slugs:
                            if slug and slug in val:
                                name = row.get("name") or row.get("id") or "?"
                                errors.append({
                                    "source": str(cat_index),
                                    "message": (
                                        f"Hard-quarantined source '{slug}' must not appear in catalog index entry "
                                        f"{name} (field {fld})"
                                    ),
                                })
        except Exception:
            pass

    # dedupe identical messages
    seen_msgs: set[str] = set()
    deduped: list[dict[str, str]] = []
    for e in errors:
        msg = e["message"]
        if msg not in seen_msgs:
            seen_msgs.add(msg)
            deduped.append(e)
    return deduped
