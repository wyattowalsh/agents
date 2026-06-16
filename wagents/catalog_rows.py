"""Catalog row builders and curated entry lookup for public skill indexes and docs surfaces."""

from __future__ import annotations

import re
from typing import Any

from wagents.external_skills import ExternalSkillEntry
from wagents.site_model import (
    _promotion_policy_for_external_status,
    _source_kind,
    trust_badge_for_tier,
)

CURATED_SECTION_HEADERS: tuple[str, ...] = (
    "Install Now After Trust Gate",
    "Inspect Then Install",
    "Keep Global Only Or Avoid",
)


def first_sentence(text: str) -> str:
    """Extract the first sentence, skipping abbreviation periods (e.g. ``e.g.``, ``i.e.``)."""
    if not isinstance(text, str) or not text:
        return ""
    # Matches ?, !, newline, or . followed by (space+Upper or end-of-text)
    match = re.search(r"[?!\n]|\.(?:\s+[A-Z]|\s*$)", text)
    if match:
        return text[: match.start() + 1].strip()
    return text.strip()


def curated_entry_by_name(entries: list[ExternalSkillEntry] | None, skill_id: str) -> ExternalSkillEntry | None:
    """Return the curated entry for *skill_id*, preferring ``verified-install-command`` provenance."""
    if not entries or not skill_id:
        return None
    match: ExternalSkillEntry | None = None
    for entry in entries:
        if entry.name != skill_id:
            continue
        if match is None or entry.provenance_status == "verified-install-command":
            match = entry
    return match


def entry_to_public_row(entry: ExternalSkillEntry) -> dict[str, Any]:
    """Convert an ``ExternalSkillEntry`` into the public catalog row dict shape for indexes/UI."""
    trust_badge, trust_badge_variant = trust_badge_for_tier(entry.trust_tier)
    return {
        "name": entry.name,
        "title": entry.name.replace("-", " ").title(),
        "description": entry.notes,
        "sourceType": "curated-external",
        "sourceRoot": entry.source,
        "displaySource": entry.source or "curated external source",
        "sourceKind": _source_kind(entry.source, source_type="curated-external"),
        "installSource": entry.install_source,
        "installable": bool(entry.install_command and entry.selector_mode != "unresolved"),
        "localInventoryOnly": False,
        "trustTier": entry.trust_tier,
        "trustBadge": trust_badge,
        "trustBadgeVariant": trust_badge_variant,
        "sourcePath": entry.source_path,
        "sourceUrl": entry.source_url,
        "installCommand": entry.install_command,
        "useCommand": f"/{entry.name}",
        "provenanceStatus": entry.provenance_status,
        "reviewStatus": "curated" if entry.provenance_status == "verified-install-command" else "unresolved",
        "selectorMode": entry.selector_mode,
        "unresolvedReason": entry.unresolved_reason,
        "license": "",
        "version": "",
        "author": "",
        "model": "",
        "argumentHint": "",
        "userInvocable": True,
        "status": entry.status,
        "targetAgents": list(entry.target_agents),
        "installedAgents": [],
        "riskNotes": entry.risk_notes or entry.notes,
        "promotionPolicy": entry.promotion_policy or _promotion_policy_for_external_status(entry.status),
        "provenanceEvidence": entry.provenance_evidence or entry.provenance_status,
        "knowledge": {
            "headings": [],
            "references": [],
            "scripts": [],
            "templates": [],
            "evals": [],
            "data": [],
            "resourceLinks": [entry.source_url] if entry.source_url else [],
            "wordCount": 0,
        },
    }


def merge_installed_agents(row: dict[str, Any], node_metadata: dict[str, object] | None) -> None:
    """In-place merge of installed agents (from ``_skills_installed_agents``) and related provenance into a public row.

    *node_metadata* is typically a ``CatalogNode.metadata`` dict coming from installed inventory.
    """
    if not isinstance(row, dict):
        return
    if not isinstance(node_metadata, dict):
        return

    # Agents (primary)
    current: list[str] = list(row.get("installedAgents") or [])
    added = node_metadata.get("_skills_installed_agents") or []
    merged = sorted(set(current) | {str(a) for a in added if a})
    row["installedAgents"] = merged

    # Optional supporting fields when present in the installed node's metadata
    prov = node_metadata.get("_skills_provenance_status")
    if prov:
        row.setdefault("installedProvenanceStatus", str(prov))

    src = node_metadata.get("_skills_source")
    if src and not row.get("installedExternalPath"):
        row["installedExternalPath"] = str(src)

    tier = node_metadata.get("_skills_trust_tier")
    if tier:
        row.setdefault("installedTrustTier", str(tier))
