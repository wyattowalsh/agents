"""Authoring catalog index for skills: load mdx entries, build public index, and convert to catalog models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import wagents
from wagents.catalog import CatalogNode
from wagents.external_skills import ExternalSkillEntry
from wagents.parsing import parse_frontmatter, to_title

AUTHORING_SKILLS_DIR = wagents.ROOT / "docs" / "src" / "authoring" / "skills"
CATALOG_INDEX_PATH = wagents.ROOT / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"


@dataclass(frozen=True)
class CatalogAuthoringEntry:
    """Parsed entry from an authoring mdx under docs/src/authoring/skills.

    Captures projected frontmatter fields plus raw frontmatter, body, and source path.
    """

    name: str
    description: str = ""
    title: str = ""
    body: str = ""
    path: str = ""  # relative path under repo or absolute filesystem path to the mdx
    source_kind: str = "custom"  # "custom" | "curated-external" | "installed" (authoring is typically custom/curated)
    # Curated-external projected fields (populated for curated-external source_kind)
    source: str = ""
    install_source: str = ""
    status: str = ""
    trust_tier: str = ""
    provenance_status: str = ""
    install_command: str = ""
    target_agents: tuple[str, ...] = ()
    source_url: str = ""
    notes: str = ""
    risk_notes: str = ""
    promotion_policy: str = ""
    provenance_evidence: str = ""
    selector_mode: str = "named"
    unresolved_reason: str = ""
    unsupported_target_agents: tuple[str, ...] = ()
    # Raw frontmatter for extensibility (any extra keys)
    frontmatter: dict[str, Any] = field(default_factory=dict)


def _frontmatter_get(fm: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for k in keys:
        if k in fm and fm[k] not in (None, ""):
            return fm[k]
    return default


def _as_tuple_strs(v: Any) -> tuple[str, ...]:
    if v is None:
        return ()
    if isinstance(v, (list, tuple)):
        return tuple(str(x) for x in v)
    if isinstance(v, str):
        # Allow comma or space separated in frontmatter for convenience
        parts = [p.strip() for p in v.replace(",", " ").split() if p.strip()]
        return tuple(parts)
    return (str(v),)


def load_authoring_entries(dir_path: Path | None = None) -> list[CatalogAuthoringEntry]:
    """Glob *.mdx under the authoring skills dir and parse frontmatter into entries."""
    base = dir_path or AUTHORING_SKILLS_DIR
    if not base.exists():
        return []
    entries: list[CatalogAuthoringEntry] = []
    for mdx in sorted(base.glob("*.mdx")):
        try:
            content = mdx.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(content)
        except Exception:
            # Skip unparsable authoring files (non-fatal; authoring may be partial)
            continue
        name = str(fm.get("name") or mdx.stem)
        description = str(fm.get("description") or "")
        title = str(fm.get("title") or to_title(name))
        source_kind = str(fm.get("source_kind") or fm.get("sourceKind") or "custom")

        entry = CatalogAuthoringEntry(
            name=name,
            description=description,
            title=title,
            body=body,
            path=str(mdx.relative_to(wagents.ROOT)) if mdx.is_relative_to(wagents.ROOT) else str(mdx),
            source_kind=source_kind,
            source=str(_frontmatter_get(fm, "source", "sourceRoot", default="")),
            install_source=str(_frontmatter_get(fm, "install_source", "installSource", default="")),
            status=str(_frontmatter_get(fm, "status", default="")),
            trust_tier=str(_frontmatter_get(fm, "trust_tier", "trustTier", default="")),
            provenance_status=str(_frontmatter_get(fm, "provenance_status", "provenanceStatus", default="")),
            install_command=str(_frontmatter_get(fm, "install_command", "installCommand", default="")),
            target_agents=_as_tuple_strs(_frontmatter_get(fm, "target_agents", "targetAgents", default=())),
            source_url=str(_frontmatter_get(fm, "source_url", "sourceUrl", default="")),
            notes=str(_frontmatter_get(fm, "notes", default="")),
            risk_notes=str(_frontmatter_get(fm, "risk_notes", "riskNotes", default="")),
            promotion_policy=str(_frontmatter_get(fm, "promotion_policy", "promotionPolicy", default="")),
            provenance_evidence=str(_frontmatter_get(fm, "provenance_evidence", "provenanceEvidence", default="")),
            selector_mode=str(_frontmatter_get(fm, "selector_mode", "selectorMode", default="named")),
            unresolved_reason=str(_frontmatter_get(fm, "unresolved_reason", "unresolvedReason", default="")),
            unsupported_target_agents=_as_tuple_strs(
                _frontmatter_get(fm, "unsupported_target_agents", "unsupportedTargetAgents", default=())
            ),
            frontmatter=dict(fm),
        )
        entries.append(entry)
    return entries


def build_catalog_index(entries: list[CatalogAuthoringEntry]) -> dict[str, Any]:
    """Build a serializable catalog index dict from authoring entries.

    Shape is intentionally aligned with site_model skill indexes for downstream consumers.
    """
    custom_rows: list[dict[str, Any]] = []
    external_rows: list[dict[str, Any]] = []
    for e in entries:
        row: dict[str, Any] = {
            "name": e.name,
            "title": e.title or to_title(e.name),
            "description": e.description,
            "sourceType": (
                "custom"
                if e.source_kind == "custom"
                else ("curated-external" if e.source_kind == "curated-external" else e.source_kind)
            ),
            "sourceRoot": e.source or (wagents.ROOT.name if e.source_kind == "custom" else ""),
            "displaySource": e.source or ("repo" if e.source_kind == "custom" else e.source),
            "sourceKind": e.source_kind,
            "installSource": e.install_source,
            "installable": bool(e.install_command) or e.source_kind == "custom",
            "localInventoryOnly": False,
            "trustTier": e.trust_tier or ("repo" if e.source_kind == "custom" else ""),
            "trustBadge": (
                "Repo-owned"
                if e.source_kind == "custom"
                else ("Curated" if e.trust_tier in ("curated-trust-gated", "") else "External")
            ),
            "trustBadgeVariant": "tip" if e.source_kind == "custom" else "note",
            "sourcePath": e.path,
            "sourceUrl": e.source_url,
            "installCommand": e.install_command,
            "useCommand": f"/{e.name}",
            "provenanceStatus": e.provenance_status or ("repo-owned" if e.source_kind == "custom" else ""),
            "status": e.status or ("repo-owned" if e.source_kind == "custom" else e.status),
            "reviewStatus": (
                "reviewed"
                if e.source_kind == "custom"
                else ("curated" if e.provenance_status == "verified-install-command" else "unresolved")
            ),
            "targetAgents": list(e.target_agents),
            "installedAgents": [],
            "riskNotes": e.risk_notes or e.notes,
            "promotionPolicy": e.promotion_policy,
            "provenanceEvidence": e.provenance_evidence or ("repo-owned" if e.source_kind == "custom" else ""),
            "selectorMode": e.selector_mode,
            "unresolvedReason": e.unresolved_reason,
            "license": e.frontmatter.get("license", ""),
            "version": e.frontmatter.get("version", ""),
            "author": e.frontmatter.get("author", ""),
            "model": e.frontmatter.get("model", ""),
            "argumentHint": e.frontmatter.get("argument-hint", e.frontmatter.get("argumentHint", "")),
            "userInvocable": (
                e.frontmatter.get("user-invocable", True)
                if "user-invocable" in e.frontmatter or "userInvocable" in e.frontmatter
                else True
            ),
            "knowledge": {
                "headings": [],
                "references": [],
                "scripts": [],
                "templates": [],
                "evals": [],
                "data": [],
                "resourceLinks": [e.source_url] if e.source_url else [],
                "wordCount": len((e.body or "").split()),
            },
        }
        if e.source_kind == "custom":
            custom_rows.append(row)
        else:
            external_rows.append(row)

    custom_rows.sort(key=lambda r: str(r.get("name", "")))
    external_rows.sort(
        key=lambda r: (str(r.get("status", "")), str(r.get("sourceRoot", "")), str(r.get("name", "")))
    )
    all_rows = sorted(
        [*custom_rows, *external_rows],
        key=lambda r: (str(r.get("sourceType", "")), str(r.get("name", ""))),
    )

    return {
        "customSkillIndex": custom_rows,
        "externalSkillIndex": external_rows,
        "allSkillIndex": all_rows,
    }


def write_catalog_index(index: dict[str, Any], path: Path | None = None) -> Path:
    """Write the catalog index JSON to *path* (defaults to CATALOG_INDEX_PATH)."""
    out = path or CATALOG_INDEX_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
    return out


def read_catalog_index(path: Path | None = None) -> dict[str, Any] | None:
    """Read the catalog index JSON if present."""
    p = path or CATALOG_INDEX_PATH
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def entry_to_external_skill_entry(entry: CatalogAuthoringEntry) -> ExternalSkillEntry:
    """Convert an authoring entry (source_kind curated-external) into an ExternalSkillEntry.

    Non-curated entries will still produce an ExternalSkillEntry with best-effort fields populated.
    """
    # Map authoring source_kind/status to external entry status values when possible
    status = entry.status or (
        "install-now-after-trust-gate"
        if entry.trust_tier == "curated-trust-gated"
        else ("inspect-then-install" if entry.trust_tier == "needs-inspection" else "installed-external")
    )
    trust_tier = entry.trust_tier or (
        "curated-trust-gated" if status == "install-now-after-trust-gate" else "needs-inspection"
    )
    provenance_status = entry.provenance_status or (
        "verified-install-command" if entry.install_command else "explicit-unresolved"
    )
    return ExternalSkillEntry(
        name=entry.name,
        source=entry.source,
        install_source=entry.install_source or entry.source,
        status=status,
        trust_tier=trust_tier,
        provenance_status=provenance_status,
        install_command=entry.install_command,
        target_agents=entry.target_agents,
        source_url=entry.source_url,
        notes=entry.notes or entry.description,
        risk_notes=entry.risk_notes or entry.notes,
        promotion_policy=entry.promotion_policy,
        provenance_evidence=entry.provenance_evidence,
        source_path=entry.path or "docs/src/authoring/skills",
        selector_mode=entry.selector_mode or "named",
        unresolved_reason=entry.unresolved_reason,
        unsupported_target_agents=entry.unsupported_target_agents,
    )


def authoring_entry_to_catalog_node(entry: CatalogAuthoringEntry) -> CatalogNode:
    """Convert an authoring entry into a CatalogNode.

    source is "custom" for source_kind=="custom", otherwise "curated-external".
    Metadata includes frontmatter plus authoring-derived fields for parity with skill_docs/site_model.
    """
    source = "custom" if entry.source_kind == "custom" else "curated-external"
    metadata: dict[str, Any] = dict(entry.frontmatter)
    # Ensure core keys
    metadata.setdefault("name", entry.name)
    metadata.setdefault("description", entry.description)
    if entry.source_kind == "curated-external":
        if entry.install_command:
            metadata["_skills_install_command"] = entry.install_command
        if entry.provenance_status:
            metadata["_skills_provenance_status"] = entry.provenance_status
        if entry.trust_tier:
            metadata["_skills_trust_tier"] = entry.trust_tier
        if entry.target_agents:
            metadata["_skills_target_agents"] = list(entry.target_agents)
        if entry.source:
            metadata["_skills_source"] = entry.source
        if entry.install_source:
            metadata["_skills_install_source"] = entry.install_source
        metadata["_curated_status"] = entry.status or ""
        metadata["_is_stub"] = not bool((entry.body or "").strip())
        if entry.promotion_policy:
            metadata["_promotion_policy"] = entry.promotion_policy
        if entry.provenance_evidence:
            metadata["_provenance_evidence"] = entry.provenance_evidence
        if entry.source_url:
            metadata["_source_url"] = entry.source_url
        if entry.selector_mode:
            metadata["_selector_mode"] = entry.selector_mode
        if entry.risk_notes:
            metadata["_risk_notes"] = entry.risk_notes
        if entry.notes:
            metadata["_notes_full"] = entry.notes
        if entry.status:
            metadata["_install_endorsed"] = entry.status == "install-now-after-trust-gate"
    else:
        # custom
        metadata.setdefault("license", metadata.get("license", ""))
        metadata.setdefault("model", metadata.get("model", ""))

    body = entry.body or ""
    return CatalogNode(
        kind="skill",
        id=entry.name,
        title=entry.title or to_title(entry.name),
        description=entry.description,
        metadata=metadata,
        body=body,
        source_path=entry.path or f"skills/{entry.name}/SKILL.md",
        source=source,
    )
