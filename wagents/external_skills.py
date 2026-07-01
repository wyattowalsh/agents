"""Curated external skill source parsing."""

from __future__ import annotations

import re
import shlex
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from typing import TYPE_CHECKING

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
    source_path: str = "docs/src/authoring/skills"
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
    sync_kind: str = ""

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

SYNC_KIND_SKILLS_CLI = "skills-cli"
SYNC_KIND_EXTERNAL_TOOL = "external-tool"
SYNC_KIND_NONE = "none"
SUPPORTED_SYNC_KINDS = {SYNC_KIND_SKILLS_CLI, SYNC_KIND_EXTERNAL_TOOL, SYNC_KIND_NONE}
CURATED_EXTERNAL_REQUIRED_FIELDS = (
    "name",
    "description",
    "source",
    "install_source",
    "status",
    "trust_tier",
    "provenance_status",
    "source_url",
    "sync_kind",
)
INSTALLABLE_STATUSES = {"install-now-after-trust-gate", "inspect-then-install"}
SYNC_RELEVANT_EXTERNAL_FIELDS = (
    "name",
    "source",
    "install_source",
    "status",
    "trust_tier",
    "provenance_status",
    "install_command",
    "target_agents",
    "selector_mode",
    "sync_kind",
)
CATALOG_REGEN_HINT = "Run uv run wagents docs generate --no-installed."


class ExternalSkillCatalogError(RuntimeError):
    """Raised when curated external skill catalog data cannot be loaded safely."""


def is_skills_cli_install_command(command: str) -> bool:
    """Return whether *command* is a Skills CLI install command."""
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    return len(parts) >= 4 and parts[:3] == ["npx", "skills", "add"]


def infer_sync_kind(sync_kind: str | None, install_command: str) -> str:
    """Normalize or infer how an external entry participates in harness sync."""
    normalized = str(sync_kind or "").strip()
    if normalized in SUPPORTED_SYNC_KINDS:
        return normalized
    if not str(install_command or "").strip():
        return SYNC_KIND_NONE
    if is_skills_cli_install_command(install_command):
        return SYNC_KIND_SKILLS_CLI
    return SYNC_KIND_EXTERNAL_TOOL


def is_external_authoring_source_kind(source_kind: object) -> bool:
    """Return whether an authoring row represents an external catalog entry."""
    return str(source_kind or "") in {"curated-external", "external"}


def _field_present(frontmatter: Mapping[str, object], field: str) -> bool:
    return field in frontmatter and frontmatter[field] not in (None, "")


def _is_installable_authoring(frontmatter: Mapping[str, object]) -> bool:
    return (
        str(frontmatter.get("status") or "") in INSTALLABLE_STATUSES
        and str(frontmatter.get("provenance_status") or "") == "verified-install-command"
    )


def curated_external_authoring_errors(
    source: str,
    frontmatter: Mapping[str, object],
) -> list[dict[str, str]]:
    """Return validation errors for curated external skill authoring frontmatter."""
    errors: list[dict[str, str]] = []
    for field in CURATED_EXTERNAL_REQUIRED_FIELDS:
        if not _field_present(frontmatter, field):
            errors.append({"source": source, "message": f"Curated external authoring is missing '{field}'"})

    if "target_agents" not in frontmatter:
        errors.append({"source": source, "message": "Curated external authoring is missing 'target_agents'"})

    install_command = str(frontmatter.get("install_command") or "")
    sync_kind = str(frontmatter.get("sync_kind") or "")
    if sync_kind and sync_kind not in SUPPORTED_SYNC_KINDS:
        errors.append({"source": source, "message": f"Invalid sync_kind '{sync_kind}'"})

    if _is_installable_authoring(frontmatter) and not install_command:
        errors.append({"source": source, "message": "Installable curated external authoring is missing 'install_command'"})

    if sync_kind == SYNC_KIND_SKILLS_CLI and not is_skills_cli_install_command(install_command):
        errors.append({"source": source, "message": "skills-cli authoring rows must use an npx skills add command"})

    if sync_kind == SYNC_KIND_EXTERNAL_TOOL and is_skills_cli_install_command(install_command):
        errors.append({"source": source, "message": "external-tool authoring rows must not use npx skills add"})

    return errors


def read_external_skill_entries(path: Path | None = None, *, strict: bool = False) -> list[ExternalSkillEntry]:
    """Read curated external skill entries from catalog index + authoring MDX.

    When *path* is set, parse curated markdown from that file (tests and one-off tools only).
    """
    if path is not None:
        if path.exists():
            return parse_external_skill_entries(path.read_text(encoding="utf-8"))
        return []

    try:
        authoring_entries = _dedupe_external_entries_first_wins(_load_authoring_external_entries(strict=strict))
        catalog_entries = _dedupe_external_entries_first_wins(read_catalog_external_entries(strict=strict))
        if authoring_entries:
            if strict:
                _validate_external_index_parity(authoring_entries, catalog_entries)
            return authoring_entries
        return catalog_entries
    except ExternalSkillCatalogError:
        if strict:
            raise
        return []
    except Exception as exc:
        if strict:
            raise ExternalSkillCatalogError(f"Failed to load curated external skill catalog: {exc}") from exc
        return []


def _load_authoring_external_entries(*, strict: bool = False) -> list[ExternalSkillEntry]:
    """Load external entries from docs/src/authoring/skills mdx (via skill_index)."""
    try:
        from . import skill_index as si

        auths = si.load_authoring_entries(strict=strict)
        external_auths = [e for e in auths if is_external_authoring_source_kind(getattr(e, "source_kind", "custom"))]
        if strict:
            errors: list[dict[str, str]] = []
            for entry in external_auths:
                errors.extend(curated_external_authoring_errors(entry.path, entry.frontmatter))
            if errors:
                raise ExternalSkillCatalogError(_format_authoring_errors(errors))
        return [si.entry_to_external_skill_entry(e) for e in external_auths]
    except Exception as exc:
        if strict and isinstance(exc, ExternalSkillCatalogError):
            raise
        if strict:
            raise ExternalSkillCatalogError(f"Failed to load authoring skill entries: {exc}") from exc
        return []


def read_catalog_external_entries(*, strict: bool = False) -> list[ExternalSkillEntry]:
    """Read external (curated) entries from the catalog index JSON using skill_index."""
    try:
        from . import skill_index as si

        idx = si.read_catalog_index(strict=strict)
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
                    sync_kind=infer_sync_kind(
                        str(r.get("syncKind") or r.get("sync_kind") or ""),
                        str(r.get("installCommand") or r.get("install_command") or ""),
                    ),
                )
            )
        return entries
    except Exception as exc:
        if strict:
            raise ExternalSkillCatalogError(f"Failed to load generated skill catalog index: {exc}") from exc
        return []


def _format_authoring_errors(errors: list[dict[str, str]]) -> str:
    visible = errors[:10]
    details = "; ".join(f"{error['source']}: {error['message']}" for error in visible)
    if len(errors) > len(visible):
        details = f"{details}; ... {len(errors) - len(visible)} more"
    return f"Invalid curated external authoring: {details}"


def _validate_external_index_parity(
    authoring_entries: list[ExternalSkillEntry],
    catalog_entries: list[ExternalSkillEntry],
) -> None:
    authoring_by_key = {_external_entry_key(entry): entry for entry in authoring_entries}
    catalog_by_key = {_external_entry_key(entry): entry for entry in catalog_entries}

    missing = sorted(set(authoring_by_key) - set(catalog_by_key))
    extra = sorted(set(catalog_by_key) - set(authoring_by_key))
    mismatches: list[str] = []
    for key in sorted(set(authoring_by_key) & set(catalog_by_key)):
        authoring_projection = _external_sync_projection(authoring_by_key[key])
        catalog_projection = _external_sync_projection(catalog_by_key[key])
        for field in SYNC_RELEVANT_EXTERNAL_FIELDS:
            if authoring_projection[field] != catalog_projection[field]:
                mismatches.append(
                    f"{_format_external_entry_key(key)} {field} "
                    f"authoring={authoring_projection[field]!r} index={catalog_projection[field]!r}"
                )

    if not missing and not extra and not mismatches:
        return

    problems: list[str] = []
    if missing:
        problems.append("missing index rows: " + ", ".join(_format_external_entry_key(key) for key in missing[:10]))
    if extra:
        problems.append("extra index rows: " + ", ".join(_format_external_entry_key(key) for key in extra[:10]))
    if mismatches:
        problems.append("mismatched index rows: " + "; ".join(mismatches[:10]))
    if len(missing) > 10 or len(extra) > 10 or len(mismatches) > 10:
        problems.append("additional drift omitted")
    raise ExternalSkillCatalogError(
        "Curated external catalog index is stale relative to authoring; "
        + "; ".join(problems)
        + f". {CATALOG_REGEN_HINT}"
    )


def _external_sync_projection(entry: ExternalSkillEntry) -> dict[str, object]:
    return {
        "name": entry.name,
        "source": entry.source.removeprefix("github:"),
        "install_source": entry.install_source,
        "status": entry.status,
        "trust_tier": entry.trust_tier,
        "provenance_status": entry.provenance_status,
        "install_command": entry.install_command,
        "target_agents": tuple(entry.target_agents),
        "selector_mode": entry.selector_mode,
        "sync_kind": infer_sync_kind(entry.sync_kind, entry.install_command),
    }


def _format_external_entry_key(key: tuple[str, str]) -> str:
    name, source = key
    return f"{source}@{name}" if source else name


def parse_external_skill_entries(markdown: str) -> list[ExternalSkillEntry]:
    """Parse curated install commands and avoid notes from markdown (tests/tools only)."""
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
                provenance_evidence="Unparsed curated markdown install command.",
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
                provenance_evidence="Unsupported curated markdown install command.",
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
        provenance_evidence="Explicit keep-global/avoid note in curated markdown.",
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
            or "Curated command plus adjacent audit note in curated markdown.",
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
    return f"Curated `npx skills add` command with {selector} under `{status}` in authoring catalog."


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


def _external_entry_key(entry: ExternalSkillEntry) -> tuple[str, str]:
    return (entry.name.lower(), entry.source.removeprefix("github:").lower())


def _dedupe_external_entries_first_wins(entries: list[ExternalSkillEntry]) -> list[ExternalSkillEntry]:
    deduped_by_key: dict[tuple[str, str], ExternalSkillEntry] = {}
    for entry in entries:
        deduped_by_key.setdefault(_external_entry_key(entry), entry)
    return list(deduped_by_key.values())


def _dedupe_external_entries(entries: list[ExternalSkillEntry]) -> list[ExternalSkillEntry]:
    deduped_by_key: dict[tuple[str, str], ExternalSkillEntry] = {}
    for entry in entries:
        key = _external_entry_key(entry)
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


def desired_install_now_entries(
    path: Path | None = None,
    *,
    sync_kind: str | None = SYNC_KIND_SKILLS_CLI,
    external_entries: list[ExternalSkillEntry] | None = None,
) -> list[ExternalSkillEntry]:
    """Return Install Now curated entries with verified install commands."""
    source_entries = external_entries if external_entries is not None else read_external_skill_entries(path)
    entries = [
        entry
        for entry in source_entries
        if entry.status == "install-now-after-trust-gate" and entry.provenance_status == "verified-install-command"
    ]
    if sync_kind is None:
        return entries
    return [entry for entry in entries if infer_sync_kind(entry.sync_kind, entry.install_command) == sync_kind]


def unsupported_target_agents(entries: list[ExternalSkillEntry]) -> dict[str, tuple[str, ...]]:
    """Return unsupported target-agent IDs keyed by source/name."""
    unsupported: dict[str, tuple[str, ...]] = {}
    for entry in entries:
        if not entry.unsupported_target_agents:
            continue
        unsupported[f"{entry.source}@{entry.name}"] = entry.unsupported_target_agents
    return unsupported
