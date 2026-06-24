"""Curated external skill source parsing."""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import asdict, dataclass, replace
from typing import TYPE_CHECKING

import wagents

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class ExternalSkillEntry:
    """A curated third-party skill or source-level external skill entry."""

    name: str
    source: str
    install_source: str
    status: str
    trust_tier: str
    provenance_status: str
    install_command: str
    target_agents: tuple[str, ...]
    source_url: str
    notes: str
    risk_notes: str = ""
    promotion_policy: str = ""
    provenance_evidence: str = ""
    source_path: str = "config/external-skills.md"
    selector_mode: str = "named"
    unresolved_reason: str = ""
    unsupported_target_agents: tuple[str, ...] = ()
    license: str = ""
    license_status: str = ""
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

    def public_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["target_agents"] = list(self.target_agents)
        data["unsupported_target_agents"] = list(self.unsupported_target_agents)
        return data


SECTION_TO_STATUS = {
    "install now after trust gate": ("install-now-after-trust-gate", "curated-trust-gated"),
    "inspect then install": ("inspect-then-install", "needs-inspection"),
    "keep global only or avoid": ("global-only-or-avoid", "global-only-or-avoid"),
}

SUPPORTED_TARGET_AGENTS = (
    "adal",
    "aider-desk",
    "amp",
    "antigravity",
    "augment",
    "bob",
    "claude-code",
    "cline",
    "codearts-agent",
    "codebuddy",
    "codemaker",
    "codestudio",
    "codex",
    "command-code",
    "continue",
    "cortex",
    "crush",
    "cursor",
    "deepagents",
    "devin",
    "dexto",
    "droid",
    "firebender",
    "forgecode",
    "gemini-cli",
    "github-copilot",
    "grok",
    "goose",
    "hermes-agent",
    "iflow-cli",
    "junie",
    "kilo",
    "kimi-cli",
    "kiro-cli",
    "kode",
    "mcpjam",
    "mistral-vibe",
    "mux",
    "neovate",
    "opencode",
    "openclaw",
    "openhands",
    "pi",
    "pochi",
    "qoder",
    "qwen-code",
    "replit",
    "roo",
    "rovodev",
    "tabnine-cli",
    "trae",
    "trae-cn",
    "universal",
    "warp",
    "windsurf",
    "zencoder",
)


def read_external_skill_entries(path: Path | None = None) -> list[ExternalSkillEntry]:
    """Read curated external skill entries.

    Prefer catalog index JSON + authoring external MDX (via skill_index).
    Fall back to legacy ``config/external-skills.md`` when the index path is empty,
    or when ``WAGENTS_CATALOG_LEGACY_EXTERNAL_MD=1`` forces legacy reconciliation.
    """
    default_path = wagents.ROOT / "config" / "external-skills.md"
    if path is not None and path.resolve() != default_path.resolve():
        if path.exists():
            return parse_external_skill_entries_legacy(path.read_text(encoding="utf-8"))
        return []

    # Try catalog index + authoring first (bundle-first / dual-read)
    combined: list[ExternalSkillEntry] = []
    try:
        seen: set[tuple[str, str]] = set()
        for entry in (*read_catalog_external_entries(), *_load_authoring_external_entries()):
            key = (entry.name.lower(), entry.source.lower())
            if key in seen:
                continue
            seen.add(key)
            combined.append(entry)
    except Exception:
        combined = []

    if combined:
        return combined

    # Legacy fallback while config/external-skills.md remains as projection (W6: remove when index-only)
    if os.environ.get("WAGENTS_CATALOG_LEGACY_EXTERNAL_MD") == "1" or not combined:
        source_path = path or default_path
        if source_path.exists():
            legacy = parse_external_skill_entries_legacy(source_path.read_text(encoding="utf-8"))
            if legacy:
                return legacy
    return combined


def _load_authoring_external_entries() -> list[ExternalSkillEntry]:
    """Load external entries from docs/src/authoring/skills mdx (via skill_index)."""
    try:
        from . import skill_index as si

        auths = si.load_authoring_entries()
        return [si.entry_to_external_skill_entry(e) for e in auths if getattr(e, "source_kind", "custom") != "custom"]
    except Exception:
        return []


def read_catalog_external_entries() -> list[ExternalSkillEntry]:
    """Read external (curated) entries from the catalog index JSON using skill_index."""
    try:
        from . import skill_index as si

        idx = si.read_catalog_index()
        if not idx:
            return []
        rows = idx.get("externalSkillIndex") or idx.get("allSkillIndex") or []
        entries: list[ExternalSkillEntry] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            if r.get("sourceType") not in ("curated-external", "external"):
                continue
            entries.append(
                ExternalSkillEntry(
                    name=str(r.get("name") or ""),
                    source=str(r.get("sourceRoot") or r.get("source") or ""),
                    install_source=str(r.get("installSource") or r.get("install_source") or ""),
                    status=str(r.get("status") or ""),
                    trust_tier=str(r.get("trustTier") or r.get("trust_tier") or ""),
                    provenance_status=str(r.get("provenanceStatus") or r.get("provenance_status") or ""),
                    install_command=str(r.get("installCommand") or r.get("install_command") or ""),
                    target_agents=tuple(r.get("targetAgents") or r.get("target_agents") or ()),
                    source_url=str(r.get("sourceUrl") or r.get("source_url") or ""),
                    notes=str(r.get("description") or r.get("notes") or ""),
                    risk_notes=str(r.get("riskNotes") or r.get("risk_notes") or ""),
                    promotion_policy=str(r.get("promotionPolicy") or r.get("promotion_policy") or ""),
                    provenance_evidence=str(r.get("provenanceEvidence") or r.get("provenance_evidence") or ""),
                    source_path=str(r.get("sourcePath") or r.get("source_path") or "catalog-index"),
                    selector_mode=str(r.get("selectorMode") or r.get("selector_mode") or "named"),
                    unresolved_reason=str(r.get("unresolvedReason") or r.get("unresolved_reason") or ""),
                    unsupported_target_agents=tuple(
                        r.get("unsupportedTargetAgents") or r.get("unsupported_target_agents") or ()
                    ),
                    license=str(r.get("license") or ""),
                    license_status=str(r.get("licenseStatus") or r.get("license_status") or ""),
                    audit_date=str(r.get("auditDate") or r.get("audit_date") or ""),
                    audited_head=str(r.get("auditedHead") or r.get("audited_head") or ""),
                    pin_policy=str(r.get("pinPolicy") or r.get("pin_policy") or ""),
                    no_pin_rationale=str(r.get("noPinRationale") or r.get("no_pin_rationale") or ""),
                    source_list_evidence=str(r.get("sourceListEvidence") or r.get("source_list_evidence") or ""),
                    executable_surface=str(r.get("executableSurface") or r.get("executable_surface") or ""),
                    allowed_tools=str(r.get("allowedTools") or r.get("allowed_tools") or ""),
                    hook_surface=str(r.get("hookSurface") or r.get("hook_surface") or ""),
                    script_surface=str(r.get("scriptSurface") or r.get("script_surface") or ""),
                    credential_behavior=str(r.get("credentialBehavior") or r.get("credential_behavior") or ""),
                    network_access=str(r.get("networkAccess") or r.get("network_access") or ""),
                    file_access=str(r.get("fileAccess") or r.get("file_access") or ""),
                    live_action_risk=str(r.get("liveActionRisk") or r.get("live_action_risk") or ""),
                    risk_category=str(r.get("riskCategory") or r.get("risk_category") or ""),
                    dedupe_notes=str(r.get("dedupeNotes") or r.get("dedupe_notes") or ""),
                )
            )
        return entries
    except Exception:
        return []


def parse_external_skill_entries_legacy(markdown: str) -> list[ExternalSkillEntry]:
    """Parse curated install commands and avoid notes from external-skills.md (legacy MD parser)."""
    entries: list[ExternalSkillEntry] = []
    current_status: tuple[str, str] | None = None
    in_fence = False
    command_lines: list[str] = []
    pending_entries: list[ExternalSkillEntry] = []
    pending_note_lines: list[str] = []

    def flush_pending() -> None:
        nonlocal pending_entries, pending_note_lines
        if not pending_entries:
            pending_note_lines = []
            return
        note = _normalize_note_lines(pending_note_lines)
        entries.extend(_entries_with_adjacent_note(pending_entries, note))
        pending_entries = []
        pending_note_lines = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            flush_pending()
            current_status = SECTION_TO_STATUS.get(heading.group(1).strip().lower())
            continue

        if line.startswith("```"):
            if in_fence:
                command = " ".join(part.strip() for part in command_lines if part.strip())
                if current_status and command:
                    flush_pending()
                    pending_entries = _entries_from_command(command, *current_status)
                command_lines = []
                in_fence = False
            else:
                flush_pending()
                in_fence = True
                command_lines = []
            continue

        if in_fence:
            command_lines.append(line)
            continue

        if current_status and current_status[0] == "global-only-or-avoid" and line.startswith("- "):
            flush_pending()
            entry = _entry_from_note(line[2:], *current_status)
            if entry:
                entries.append(entry)
            continue

        if pending_entries and line:
            pending_note_lines.append(line)

    flush_pending()

    return _dedupe_external_entries(entries)


# Alias kept for backward compat and existing tests that import the parser name directly.
parse_external_skill_entries = parse_external_skill_entries_legacy


def _entries_from_command(command: str, status: str, trust_tier: str) -> list[ExternalSkillEntry]:
    try:
        parts = shlex.split(command)
    except ValueError:
        return [
            ExternalSkillEntry(
                name="unparsed-command",
                source="",
                install_source="",
                status=status,
                trust_tier=trust_tier,
                provenance_status="explicit-unresolved",
                install_command=command,
                target_agents=(),
                source_url="",
                notes="Curated command could not be parsed with shell quoting rules.",
                promotion_policy=_promotion_policy(status),
                provenance_evidence="Unparsed command in config/external-skills.md.",
                selector_mode="unresolved",
                unresolved_reason="Command could not be parsed with shlex.",
            )
        ]
    if len(parts) < 4 or parts[:3] != ["npx", "skills", "add"]:
        return [
            ExternalSkillEntry(
                name="unparsed-command",
                source="",
                install_source="",
                status=status,
                trust_tier=trust_tier,
                provenance_status="explicit-unresolved",
                install_command=command,
                target_agents=(),
                source_url="",
                notes="Curated command is not a supported `npx skills add ...` invocation.",
                promotion_policy=_promotion_policy(status),
                provenance_evidence="Unsupported command in config/external-skills.md.",
                selector_mode="unresolved",
                unresolved_reason="Only `npx skills add ...` commands are installable.",
            )
        ]
    raw_source = parts[3]
    source, embedded_skill = _split_source_spec(raw_source)
    skills: list[str] = []
    target_agents: list[str] = []
    idx = 4
    while idx < len(parts):
        part = parts[idx]
        if part == "--skill" and idx + 1 < len(parts):
            skills.append(parts[idx + 1])
            idx += 2
            continue
        if part in {"-a", "--agent"}:
            idx += 1
            while idx < len(parts) and not parts[idx].startswith("-"):
                target_agents.append(parts[idx])
                idx += 1
            continue
        idx += 1

    unsupported_target_agents = tuple(agent for agent in target_agents if agent not in SUPPORTED_TARGET_AGENTS)

    selector_mode = "named"
    if not skills and embedded_skill:
        skills = [embedded_skill]
        selector_mode = "source-spec"
    elif skills == ["*"]:
        skills = [_wildcard_name(source)]
        selector_mode = "wildcard"

    if not skills:
        return [
            ExternalSkillEntry(
                name=_wildcard_name(source),
                source=source,
                install_source=raw_source,
                status=status,
                trust_tier=trust_tier,
                provenance_status="explicit-unresolved",
                install_command=command,
                target_agents=tuple(target_agents),
                source_url=_source_url(source),
                notes="Curated source is present, but no installable skill selector was captured.",
                promotion_policy=_promotion_policy(status),
                provenance_evidence=_command_provenance_evidence(status, selector_mode="unresolved"),
                selector_mode="unresolved",
                unresolved_reason="Missing `--skill` selector or source-embedded skill name.",
                unsupported_target_agents=unsupported_target_agents,
            )
        ]

    return [
        ExternalSkillEntry(
            name=skill,
            source=source,
            install_source=raw_source,
            status=status,
            trust_tier=trust_tier,
            provenance_status="verified-install-command",
            install_command=command,
            target_agents=tuple(target_agents),
            source_url=_source_url(source),
            notes=_command_note(selector_mode),
            promotion_policy=_promotion_policy(status),
            provenance_evidence=_command_provenance_evidence(status, selector_mode=selector_mode),
            selector_mode=selector_mode,
            unsupported_target_agents=unsupported_target_agents,
        )
        for skill in skills
    ]


def _entry_from_note(note: str, status: str, trust_tier: str) -> ExternalSkillEntry | None:
    match = re.match(r"`([^`]+)`:\s*(.+)$", note)
    if not match:
        return None
    raw_source, details = match.groups()
    source, skill_name = _split_source_spec(raw_source)
    name = skill_name or _wildcard_name(source)
    return ExternalSkillEntry(
        name=name,
        source=source,
        install_source=raw_source,
        status=status,
        trust_tier=trust_tier,
        provenance_status="explicit-unresolved",
        install_command="",
        target_agents=(),
        source_url=_source_url(source),
        notes=details.strip(),
        risk_notes=details.strip(),
        promotion_policy=_promotion_policy(status),
        provenance_evidence="Explicit keep-global/avoid note in config/external-skills.md.",
        selector_mode="unresolved",
        unresolved_reason=details.strip(),
    )


def _normalize_note_lines(lines: list[str]) -> str:
    return " ".join(line.strip() for line in lines if line.strip())


def _entries_with_adjacent_note(entries: list[ExternalSkillEntry], note: str) -> list[ExternalSkillEntry]:
    if not note:
        return entries
    return [
        replace(
            entry,
            notes=note,
            risk_notes=note,
            provenance_evidence=entry.provenance_evidence
            or "Curated command plus adjacent audit note in config/external-skills.md.",
        )
        for entry in entries
    ]


def _promotion_policy(status: str) -> str:
    return {
        "install-now-after-trust-gate": "Install only after trust gate; audit again before repo promotion.",
        "inspect-then-install": "Inspect source, hooks, scripts, credentials, and dedupe before install.",
        "global-only-or-avoid": "Keep global-only or avoid unless explicitly approved.",
    }.get(status, "")


def _command_provenance_evidence(status: str, *, selector_mode: str) -> str:
    selector = {
        "named": "named `--skill` selectors",
        "source-spec": "source-embedded skill selector",
        "wildcard": 'wildcard `--skill "*"` selector',
        "unresolved": "unresolved selector",
    }.get(selector_mode, "parsed selector")
    return f"Curated `npx skills add` command with {selector} under `{status}` in config/external-skills.md."


def _source_url(source: str) -> str:
    normalized = source.removeprefix("github:")
    if re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", normalized):
        return f"https://github.com/{normalized}"
    if re.match(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", normalized):
        return f"https://{normalized}"
    return ""


def _split_source_spec(raw_source: str) -> tuple[str, str | None]:
    normalized = raw_source.strip()
    source_only = normalized.removeprefix("github:")
    if normalized.startswith("@"):
        return source_only, None
    if normalized.count("@") == 1:
        source, _, skill_name = normalized.rpartition("@")
        if source and skill_name:
            return source.removeprefix("github:"), skill_name
    return source_only, None


def _command_note(selector_mode: str) -> str:
    if selector_mode == "wildcard":
        return "Curated third-party source. This command installs every exposed skill from the source."
    if selector_mode == "source-spec":
        return "Curated third-party source. The source spec encodes the installable skill directly."
    return "Curated third-party skill source. Run /review source before repo promotion."


def _wildcard_name(source: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")
    return f"{slug}-all" if slug else "all-skills"


def _dedupe_external_entries(entries: list[ExternalSkillEntry]) -> list[ExternalSkillEntry]:
    deduped_by_key: dict[tuple[str, str], ExternalSkillEntry] = {}
    for entry in entries:
        key = (entry.name.lower(), entry.source.removeprefix("github:").lower())
        existing = deduped_by_key.get(key)
        if existing is None or _entry_priority(entry) > _entry_priority(existing):
            deduped_by_key[key] = entry
    return list(deduped_by_key.values())


def _entry_priority(entry: ExternalSkillEntry) -> int:
    if entry.provenance_status == "verified-install-command":
        return 3
    if entry.install_command:
        return 2
    if entry.status != "global-only-or-avoid":
        return 1
    return 0


def desired_install_now_entries(path: Path | None = None) -> list[ExternalSkillEntry]:
    """Return Install Now curated entries with verified install commands."""
    return [
        entry
        for entry in read_external_skill_entries(path)
        if entry.status == "install-now-after-trust-gate" and entry.provenance_status == "verified-install-command"
    ]


def unsupported_target_agents(entries: list[ExternalSkillEntry]) -> dict[str, tuple[str, ...]]:
    """Return unsupported target-agent IDs keyed by source/name."""
    unsupported: dict[str, tuple[str, ...]] = {}
    for entry in entries:
        if not entry.unsupported_target_agents:
            continue
        unsupported[f"{entry.source}@{entry.name}"] = entry.unsupported_target_agents
    return unsupported
