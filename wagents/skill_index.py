"""Authoring catalog index for skills: load mdx entries, build public index, and convert to catalog models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import wagents
from wagents.catalog import CatalogNode
from wagents.external_skills import ExternalSkillEntry
from wagents.parsing import parse_frontmatter, to_title
from wagents.site_model import use_command_for_catalog_row

if TYPE_CHECKING:
    from pathlib import Path

AUTHORING_SKILLS_DIR = wagents.ROOT / "docs" / "src" / "authoring" / "skills"
CATALOG_INDEX_PATH = wagents.ROOT / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
EXTERNAL_AUTHORING_SOURCE_KINDS = {"curated-external", "external"}


def _is_external_authoring_source_kind(source_kind: str) -> bool:
    return source_kind in EXTERNAL_AUTHORING_SOURCE_KINDS


def _catalog_source_type(source_kind: str) -> str:
    if source_kind == "custom":
        return "custom"
    if _is_external_authoring_source_kind(source_kind):
        return "curated-external"
    return source_kind


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
    source_kind: str = "custom"  # "custom" | "curated-external" | "external"
    # External projected fields (populated for supported external source_kind values)
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
    audit_date: str = ""
    audited_head: str = ""
    pin_policy: str = ""
    no_pin_rationale: str = ""
    source_list_evidence: str = ""
    executable_surface: str = ""
    allowed_tools: str = ""
    hook_surface: str = ""
    script_surface: str = ""
    credential_behavior: str = ""
    network_access: str = ""
    file_access: str = ""
    live_action_risk: str = ""
    risk_category: str = ""
    dedupe_notes: str = ""
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
            audit_date=str(_frontmatter_get(fm, "audit_date", "auditDate", default="")),
            audited_head=str(_frontmatter_get(fm, "audited_head", "auditedHead", default="")),
            pin_policy=str(_frontmatter_get(fm, "pin_policy", "pinPolicy", default="")),
            no_pin_rationale=str(_frontmatter_get(fm, "no_pin_rationale", "noPinRationale", default="")),
            source_list_evidence=str(_frontmatter_get(fm, "source_list_evidence", "sourceListEvidence", default="")),
            executable_surface=str(_frontmatter_get(fm, "executable_surface", "executableSurface", default="")),
            allowed_tools=str(_frontmatter_get(fm, "allowed_tools", "allowed-tools", "allowedTools", default="")),
            hook_surface=str(_frontmatter_get(fm, "hook_surface", "hookSurface", default="")),
            script_surface=str(_frontmatter_get(fm, "script_surface", "scriptSurface", default="")),
            credential_behavior=str(_frontmatter_get(fm, "credential_behavior", "credentialBehavior", default="")),
            network_access=str(_frontmatter_get(fm, "network_access", "networkAccess", default="")),
            file_access=str(_frontmatter_get(fm, "file_access", "fileAccess", default="")),
            live_action_risk=str(_frontmatter_get(fm, "live_action_risk", "liveActionRisk", default="")),
            risk_category=str(_frontmatter_get(fm, "risk_category", "riskCategory", default="")),
            dedupe_notes=str(_frontmatter_get(fm, "dedupe_notes", "dedupeNotes", default="")),
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
            "sourceType": _catalog_source_type(e.source_kind),
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
            "useCommand": use_command_for_catalog_row(e.install_command, e.name),
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
            "auditDate": e.audit_date,
            "auditedHead": e.audited_head,
            "pinPolicy": e.pin_policy,
            "noPinRationale": e.no_pin_rationale,
            "sourceListEvidence": e.source_list_evidence,
            "executableSurface": e.executable_surface,
            "allowedTools": e.allowed_tools,
            "hookSurface": e.hook_surface,
            "scriptSurface": e.script_surface,
            "credentialBehavior": e.credential_behavior,
            "networkAccess": e.network_access,
            "fileAccess": e.file_access,
            "liveActionRisk": e.live_action_risk,
            "riskCategory": e.risk_category,
            "dedupeNotes": e.dedupe_notes,
            "selectorMode": e.selector_mode,
            "unresolvedReason": e.unresolved_reason,
            "unsupportedTargetAgents": list(e.unsupported_target_agents),
            "license": e.frontmatter.get("license", ""),
            "licenseStatus": e.frontmatter.get("license_status", e.frontmatter.get("licenseStatus", "")),
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
    external_rows.sort(key=lambda r: (str(r.get("status", "")), str(r.get("sourceRoot", "")), str(r.get("name", ""))))
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


def build_catalog_index_from_authoring(dir_path: Path | None = None) -> dict[str, Any] | None:
    """Build the expected index bundle from authoring MDX entries."""
    entries = load_authoring_entries(dir_path)
    if not entries:
        return None
    return build_catalog_index(entries)


def catalog_index_stale_reason(path: Path | None = None) -> str | None:
    """Return a remediation message when the committed index drifts from authoring SSOT."""
    expected = build_catalog_index_from_authoring()
    if expected is None:
        return None
    existing = read_catalog_index(path)
    out = path or CATALOG_INDEX_PATH
    if existing is None:
        return f"{out.relative_to(wagents.ROOT)} missing; run `uv run wagents docs generate --no-installed`"
    if json.dumps(expected, indent=2, sort_keys=True) != json.dumps(existing, indent=2, sort_keys=True):
        return f"{out.relative_to(wagents.ROOT)} is stale; run `uv run wagents docs generate --no-installed`"
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
        license=str(entry.frontmatter.get("license", "")),
        license_status=str(entry.frontmatter.get("license_status", entry.frontmatter.get("licenseStatus", ""))),
        audit_date=entry.audit_date,
        audited_head=entry.audited_head,
        pin_policy=entry.pin_policy,
        no_pin_rationale=entry.no_pin_rationale,
        source_list_evidence=entry.source_list_evidence,
        executable_surface=entry.executable_surface,
        allowed_tools=entry.allowed_tools,
        hook_surface=entry.hook_surface,
        script_surface=entry.script_surface,
        credential_behavior=entry.credential_behavior,
        network_access=entry.network_access,
        file_access=entry.file_access,
        live_action_risk=entry.live_action_risk,
        risk_category=entry.risk_category,
        dedupe_notes=entry.dedupe_notes,
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
    if _is_external_authoring_source_kind(entry.source_kind):
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
        license_status = entry.frontmatter.get("license_status") or entry.frontmatter.get("licenseStatus")
        if license_status:
            metadata["license_status"] = str(license_status)
        for attr, key in (
            ("audit_date", "_audit_date"),
            ("audited_head", "_audited_head"),
            ("pin_policy", "_pin_policy"),
            ("no_pin_rationale", "_no_pin_rationale"),
            ("source_list_evidence", "_source_list_evidence"),
            ("executable_surface", "_executable_surface"),
            ("allowed_tools", "_allowed_tools"),
            ("hook_surface", "_hook_surface"),
            ("script_surface", "_script_surface"),
            ("credential_behavior", "_credential_behavior"),
            ("network_access", "_network_access"),
            ("file_access", "_file_access"),
            ("live_action_risk", "_live_action_risk"),
            ("risk_category", "_risk_category"),
            ("dedupe_notes", "_dedupe_notes"),
        ):
            value = getattr(entry, attr)
            if value:
                metadata[key] = value
        if entry.unsupported_target_agents:
            metadata["_unsupported_target_agents"] = list(entry.unsupported_target_agents)
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
