"""Normalized installed-skill inventory across supported harnesses."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from wagents import ROOT
from wagents.external_skills import (
    SYNC_KIND_NONE,
    SYNC_KIND_SKILLS_CLI,
    ExternalSkillEntry,
    desired_install_now_entries,
    infer_sync_kind,
    read_external_skill_entries,
)

# desired_install_now_entries (and callers) delegate to read_external_skill_entries (catalog index + authoring).
from wagents.parsing import parse_frontmatter

if TYPE_CHECKING:
    from collections.abc import Sequence

DEFAULT_HARNESS_QUERY_TIMEOUT_SEC = 120

EXPOSURE_OWNER_PLUGIN = "plugin"
EXPOSURE_OWNER_DIRECT_REPO_PATH = "direct-repo-path"
EXPOSURE_OWNER_PROJECT_LOCAL = "project-local"
EXPOSURE_OWNER_SKILLS_CLI = "skills-cli"
EXPOSURE_OWNER_USER_LOCAL = "user-local"

DUPLICATE_CLASS_NONE = "none"
DUPLICATE_CLASS_SAME_REALPATH = "same-realpath"
DUPLICATE_CLASS_SAME_BODY = "same-body"
DUPLICATE_CLASS_DIVERGENT_BODY = "divergent-body"

CLEANUP_ACTION_NONE = "none"
CLEANUP_ACTION_REMOVE_GENERATED_SYMLINK = "remove-generated-symlink"
CLEANUP_ACTION_REFRESH_PLUGIN_CACHE = "refresh-plugin-cache"
CLEANUP_ACTION_SYNC_HOME_CONFIG = "sync-home-config"
CLEANUP_ACTION_PRESERVE = "preserve"
CLEANUP_ACTION_MANUAL_REVIEW = "manual-review"

DOCS_STATUS_DOCUMENTED = "documented"
DOCS_STATUS_GENERATED_MISSING = "generated-missing"
DOCS_STATUS_NOT_APPLICABLE = "not-applicable"

DUPLICATE_CLASS_PRIORITY = {
    DUPLICATE_CLASS_NONE: 0,
    DUPLICATE_CLASS_SAME_BODY: 10,
    DUPLICATE_CLASS_SAME_REALPATH: 20,
    DUPLICATE_CLASS_DIVERGENT_BODY: 30,
}

CLEANUP_ACTION_PRIORITY = {
    CLEANUP_ACTION_NONE: 0,
    CLEANUP_ACTION_PRESERVE: 10,
    CLEANUP_ACTION_SYNC_HOME_CONFIG: 20,
    CLEANUP_ACTION_REFRESH_PLUGIN_CACHE: 20,
    CLEANUP_ACTION_REMOVE_GENERATED_SYMLINK: 30,
    CLEANUP_ACTION_MANUAL_REVIEW: 40,
}

DOCS_STATUS_PRIORITY = {
    DOCS_STATUS_NOT_APPLICABLE: 0,
    DOCS_STATUS_DOCUMENTED: 10,
    DOCS_STATUS_GENERATED_MISSING: 20,
}

AGENT_LABEL_TO_ID = {
    "Antigravity": "antigravity",
    "Claude Code": "claude-code",
    "Codex": "codex",
    "Crush": "crush",
    "Cursor": "cursor",
    "Gemini CLI": "gemini-cli",
    "GitHub Copilot": "github-copilot",
    "Grok Build": "grok",
    "OpenCode": "opencode",
}

INSTALLED_SKILL_SUPERSESSION_PATH = ROOT / "config" / "skill-installed-supersession.json"


def load_installed_skill_supersession_aliases(*, repo_root: Path | None = None) -> dict[str, str]:
    """Return stale installed skill ids mapped to verified catalog replacement ids."""
    path = (repo_root or ROOT) / "config" / "skill-installed-supersession.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    aliases = data.get("aliases")
    if not isinstance(aliases, dict):
        return {}
    return {
        str(stale_id): str(replacement_id)
        for stale_id, replacement_id in aliases.items()
        if stale_id and replacement_id
    }


# Skills CLI has no native Grok adapter; sync installs via Claude Code paths Grok reads.
SKILLS_CLI_AGENT_ALIASES = {"grok": "claude-code"}

GROK_SKILL_SCAN_SOURCES: tuple[tuple[Path, str], ...] = (
    (Path(".grok") / "skills", "Grok Build"),
    (Path(".claude") / "skills", "Claude Code"),
)

LOCAL_SKILL_ROOT_FALLBACKS: dict[str, tuple[tuple[Path, str], ...]] = {
    "antigravity": ((Path(".agents") / "skills", "Antigravity"),),
    "claude-code": ((Path(".claude") / "skills", "Claude Code"),),
    "codex": ((Path(".codex") / "skills", "Codex"),),
    "crush": (
        (Path(".config") / "crush" / "skills", "Crush"),
        (Path(".agents") / "skills", "Crush"),
    ),
    "cursor": (
        (Path(".cursor") / "skills", "Cursor"),
        (Path(".agents") / "skills", "Cursor"),
    ),
    "gemini-cli": ((Path(".gemini") / "skills", "Gemini CLI"),),
    "github-copilot": ((Path(".copilot") / "skills", "GitHub Copilot"),),
    "opencode": ((Path(".config") / "opencode" / "skills", "OpenCode"),),
}

SKILL_EXPOSURE_ROOTS: tuple[tuple[str, Path, str, str], ...] = (
    ("multi-harness", Path(".agents") / "skills", EXPOSURE_OWNER_SKILLS_CLI, "global"),
    ("claude-code", Path(".claude") / "skills", EXPOSURE_OWNER_SKILLS_CLI, "global"),
    ("codex", Path(".codex") / "skills", EXPOSURE_OWNER_SKILLS_CLI, "global"),
    ("opencode", Path(".config") / "opencode" / "skills", EXPOSURE_OWNER_SKILLS_CLI, "global"),
    ("crush", Path(".config") / "crush" / "skills", EXPOSURE_OWNER_SKILLS_CLI, "global"),
    ("gemini-cli", Path(".gemini") / "skills", EXPOSURE_OWNER_SKILLS_CLI, "global"),
    ("github-copilot", Path(".copilot") / "skills", EXPOSURE_OWNER_SKILLS_CLI, "global"),
    ("grok", Path(".grok") / "skills", EXPOSURE_OWNER_SKILLS_CLI, "global"),
    ("cursor", Path(".cursor") / "skills", EXPOSURE_OWNER_SKILLS_CLI, "global"),
)

PROJECT_SKILL_EXPOSURE_ROOTS: tuple[tuple[str, Path, str, str], ...] = (
    ("cursor", Path(".cursor") / "skills", EXPOSURE_OWNER_PROJECT_LOCAL, "project"),
    ("cursor", Path(".cursor") / "skills" / "repo", EXPOSURE_OWNER_PROJECT_LOCAL, "project"),
    ("grok", Path(".grok") / "skills", EXPOSURE_OWNER_PROJECT_LOCAL, "project"),
    ("claude-code", Path(".claude") / "skills", EXPOSURE_OWNER_PROJECT_LOCAL, "project"),
)

TREE_HASH_ALWAYS_FILES = ("SKILL.md", "metadata.json")
TREE_HASH_INCLUDED_DIRS = frozenset(("evals", "examples", "references", "scripts", "templates"))
TREE_HASH_IGNORED_DIRS = frozenset(
    (
        ".cache",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
    )
)


@dataclass(frozen=True)
class HarnessSkillEntry:
    """One row returned by `npx skills ls --json` for a queried harness."""

    queried_agent: str
    name: str
    path: str
    scope: str
    raw_agents: tuple[str, ...]


@dataclass(frozen=True)
class HarnessQueryResult:
    """Outcome of one `npx skills ls -a <agent> --json` query."""

    agent_id: str
    ok: bool
    entries: tuple[HarnessSkillEntry, ...]
    error: str = ""


@dataclass(frozen=True)
class InstalledSkillInventoryRow:
    """Normalized installed-skill row shared by docs and sync logic."""

    name: str
    path: str
    source_path: str
    scope: str
    description: str
    license: str
    version: str
    author: str
    source: str
    install_source: str
    source_url: str
    install_command: str
    provenance_status: str
    trust_tier: str
    selector_mode: str
    installed_agents: tuple[str, ...]
    discovered_in: tuple[str, ...]
    target_agents: tuple[str, ...]
    unresolved_reason: str = ""
    sync_kind: str = ""
    exposure_owner: str = ""
    duplicate_class: str = DUPLICATE_CLASS_NONE
    cleanup_action: str = CLEANUP_ACTION_NONE
    docs_status: str = DOCS_STATUS_NOT_APPLICABLE

    def is_repo_owned(self) -> bool:
        return self.provenance_status == "repo-owned"

    def is_verified_curated(self) -> bool:
        return self.provenance_status == "verified-curated-external"

    def is_installable(self) -> bool:
        return self.is_syncable() and bool(self.install_command) and self.provenance_status not in {
            "curated-unresolved",
            "read-only-discovered",
        }

    def is_syncable(self) -> bool:
        return infer_sync_kind(self.sync_kind, self.install_command) == SYNC_KIND_SKILLS_CLI

    def public_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "path": self.path,
            "source_path": self.source_path,
            "scope": self.scope,
            "description": self.description,
            "license": self.license,
            "version": self.version,
            "author": self.author,
            "source": self.source,
            "install_source": self.install_source,
            "source_url": self.source_url,
            "install_command": self.install_command,
            "provenance_status": self.provenance_status,
            "trust_tier": self.trust_tier,
            "selector_mode": self.selector_mode,
            "installed_agents": list(self.installed_agents),
            "discovered_in": list(self.discovered_in),
            "target_agents": list(self.target_agents),
            "unresolved_reason": self.unresolved_reason,
            "sync_kind": infer_sync_kind(self.sync_kind, self.install_command),
            "exposure_owner": self.exposure_owner,
            "duplicate_class": self.duplicate_class,
            "cleanup_action": self.cleanup_action,
            "docs_status": self.docs_status,
        }


@dataclass(frozen=True)
class SkillExposure:
    """One filesystem skill exposure discovered during cleanup planning."""

    name: str
    harness: str
    root: str
    path: str
    source_path: str
    resolved_path: str
    scope: str
    exposure_owner: str
    canonical_owner: str
    repo_owned: bool
    is_symlink: bool
    skill_hash: str
    tree_hash: str
    duplicate_class: str = DUPLICATE_CLASS_NONE
    cleanup_action: str = CLEANUP_ACTION_NONE
    docs_status: str = DOCS_STATUS_NOT_APPLICABLE

    def public_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "harness": self.harness,
            "root": self.root,
            "path": self.path,
            "source_path": self.source_path,
            "resolved_path": self.resolved_path,
            "scope": self.scope,
            "exposure_owner": self.exposure_owner,
            "canonical_owner": self.canonical_owner,
            "repo_owned": self.repo_owned,
            "is_symlink": self.is_symlink,
            "skill_hash": self.skill_hash,
            "tree_hash": self.tree_hash,
            "duplicate_class": self.duplicate_class,
            "cleanup_action": self.cleanup_action,
            "docs_status": self.docs_status,
        }


@dataclass(frozen=True)
class InstalledInventorySnapshot:
    """Snapshot of normalized rows plus per-harness query outcomes."""

    rows: tuple[InstalledSkillInventoryRow, ...]
    queries: tuple[HarnessQueryResult, ...]


def supported_agent_ids() -> tuple[str, ...]:
    """Return the repo's canonical supported agent IDs."""
    from wagents.site_model import SUPPORTED_AGENT_IDS

    return SUPPORTED_AGENT_IDS


def skills_cli_agent_id(agent_id: str) -> str:
    """Map harness IDs to Skills CLI adapter names when they differ."""
    return SKILLS_CLI_AGENT_ALIASES.get(agent_id, agent_id)


def query_harness_skills(
    *,
    agent_ids: tuple[str, ...] | None = None,
    runner: Any = subprocess.run,
    timeout_sec: int = DEFAULT_HARNESS_QUERY_TIMEOUT_SEC,
    home: Path | None = None,
    repo_root: Path | None = None,
    max_workers: int | None = None,
) -> tuple[HarnessQueryResult, ...]:
    """Enumerate installed skills for each supported harness."""
    home_dir = home or Path.home()
    root = repo_root or ROOT
    ids = agent_ids or supported_agent_ids()
    if not ids:
        return ()
    if len(ids) == 1:
        return (_query_one_harness(ids[0], runner=runner, timeout_sec=timeout_sec, home=home_dir, repo_root=root),)

    workers = max_workers or min(len(ids), 8)
    by_agent: dict[str, HarnessQueryResult] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _query_one_harness,
                agent_id,
                runner=runner,
                timeout_sec=timeout_sec,
                home=home_dir,
                repo_root=root,
            ): agent_id
            for agent_id in ids
        }
        for future in as_completed(futures):
            agent_id = futures[future]
            by_agent[agent_id] = future.result()
    return tuple(by_agent[agent_id] for agent_id in ids)


def collect_installed_inventory(
    *,
    agent_ids: tuple[str, ...] | None = None,
    root: Path | None = None,
    home: Path | None = None,
    runner: Any = subprocess.run,
    query_timeout_sec: int = DEFAULT_HARNESS_QUERY_TIMEOUT_SEC,
    external_entries: list[ExternalSkillEntry] | None = None,
) -> InstalledInventorySnapshot:
    """Build one normalized installed-skill inventory snapshot."""
    repo_root = root or ROOT
    home_dir = home or Path.home()
    curated = external_entries if external_entries is not None else read_external_skill_entries()
    curated_by_name: dict[str, ExternalSkillEntry] = {}
    for entry in curated:
        existing = curated_by_name.get(entry.name)
        if existing is None or entry.provenance_status == "verified-install-command":
            curated_by_name[entry.name] = entry
    lock_sources = _load_installed_skill_sources(home=home_dir)
    queries = query_harness_skills(
        agent_ids=agent_ids,
        runner=runner,
        timeout_sec=query_timeout_sec,
        home=home_dir,
        repo_root=repo_root,
    )

    aggregated: dict[str, dict[str, object]] = {}
    for query in queries:
        if not query.ok:
            continue
        for entry in query.entries:
            current = aggregated.setdefault(
                entry.name,
                {
                    "name": entry.name,
                    "path": entry.path,
                    "scope": entry.scope,
                    "raw_agents": set(),
                    "discovered_in": set(),
                },
            )
            current["path"] = str(current.get("path") or entry.path)
            current["scope"] = str(current.get("scope") or entry.scope)
            cast_set(current["raw_agents"]).update(entry.raw_agents)
            cast_set(current["discovered_in"]).add(query.agent_id)

    rows: list[InstalledSkillInventoryRow] = []
    for name, raw in sorted(aggregated.items()):
        path = str(raw["path"])
        skill_dir = Path(path).expanduser()
        resolved_dir = skill_dir.resolve(strict=False)
        fm, file_meta = _read_skill_metadata(skill_dir)
        lock_meta = lock_sources.get(name) or lock_sources.get(skill_dir.name) or {}
        curated_entry = curated_by_name.get(name)
        discovered_in = tuple(sorted(cast_set(raw["discovered_in"])))
        installed_agent_ids = _normalize_agents(cast_set(raw["raw_agents"]))
        installed_agent_ids.update(discovered_in)
        installed_agents = tuple(sorted(installed_agent_ids))
        source_path = str((resolved_dir / "SKILL.md") if (resolved_dir / "SKILL.md").exists() else skill_dir)

        repo_owned = _is_repo_owned_skill(resolved_dir, repo_root, name)
        install_command_override = ""
        if repo_owned:
            install_source = resolve_repo_install_source(name, repo_root=repo_root)
            source = install_source
            provenance_status = "repo-owned"
            trust_tier = "repo"
            selector_mode = "named"
            target_agents = supported_agent_ids()
            unresolved_reason = ""
            sync_kind = SYNC_KIND_SKILLS_CLI
        elif curated_entry is not None and curated_entry.provenance_status == "verified-install-command":
            source = curated_entry.source
            install_source = curated_entry.install_source
            provenance_status = "verified-curated-external"
            trust_tier = curated_entry.trust_tier
            selector_mode = curated_entry.selector_mode
            target_agents = curated_entry.target_agents
            unresolved_reason = ""
            install_command_override = curated_entry.install_command
            sync_kind = infer_sync_kind(curated_entry.sync_kind, curated_entry.install_command)
        elif curated_entry is not None:
            source = curated_entry.source
            install_source = curated_entry.install_source
            provenance_status = "curated-unresolved"
            trust_tier = curated_entry.trust_tier
            selector_mode = curated_entry.selector_mode
            target_agents = curated_entry.target_agents
            unresolved_reason = curated_entry.unresolved_reason or curated_entry.notes
            install_command_override = curated_entry.install_command
            sync_kind = infer_sync_kind(curated_entry.sync_kind, curated_entry.install_command)
        elif isinstance(lock_meta, dict) and lock_meta.get("source"):
            source = str(lock_meta["source"])
            install_source = source
            provenance_status = "installed-external"
            trust_tier = str(lock_meta.get("sourceType") or "external-installed")
            selector_mode = "named"
            target_agents = ()
            unresolved_reason = ""
            sync_kind = ""
        else:
            source = str(fm.get("_skills_source") or "")
            install_source = source
            provenance_status = "read-only-discovered"
            trust_tier = "read-only-discovered"
            selector_mode = "named"
            target_agents = ()
            unresolved_reason = "No lockfile or curated source was found for this installed skill."
            sync_kind = SYNC_KIND_NONE

        install_command = install_command_override or _canonical_install_command(
            name, install_source, selector_mode, provenance_status
        )
        sync_kind = infer_sync_kind(sync_kind, install_command)
        rows.append(
            InstalledSkillInventoryRow(
                name=name,
                path=path,
                source_path=source_path,
                scope=str(raw["scope"]),
                description=str(fm.get("description") or file_meta.get("description") or ""),
                license=str(fm.get("license") or file_meta.get("license") or ""),
                version=str(_metadata_value(fm, file_meta, "version")),
                author=str(_metadata_value(fm, file_meta, "author")),
                source=source or path,
                install_source=install_source,
                source_url=_source_url(source or install_source),
                install_command=install_command,
                provenance_status=provenance_status,
                trust_tier=trust_tier,
                selector_mode=selector_mode,
                installed_agents=installed_agents,
                discovered_in=discovered_in,
                target_agents=tuple(target_agents),
                unresolved_reason=unresolved_reason,
                sync_kind=sync_kind,
                exposure_owner=EXPOSURE_OWNER_SKILLS_CLI if provenance_status == "repo-owned" else "",
                docs_status=_docs_status_for_skill(name, repo_owned=provenance_status == "repo-owned", root=repo_root),
            )
        )

    return InstalledInventorySnapshot(rows=tuple(rows), queries=queries)


def _query_one_harness(
    agent_id: str,
    *,
    runner: Any,
    timeout_sec: int,
    home: Path,
    repo_root: Path | None = None,
) -> HarnessQueryResult:
    if agent_id == "grok":
        return _query_grok_harness(home, repo_root=repo_root)
    cli_agent_id = skills_cli_agent_id(agent_id)
    command = ["npx", "-y", "skills", "ls", "-g", "-a", cli_agent_id, "--json"]
    try:
        result = _run_harness_command(command, runner=runner, timeout_sec=timeout_sec)
    except subprocess.TimeoutExpired:
        fallback = _query_local_harness_roots(
            agent_id,
            home=home,
            reason=f"Fallback local skill-root inventory after timeout: {' '.join(command)}",
        )
        if fallback is not None:
            return fallback
        return HarnessQueryResult(
            agent_id=agent_id,
            ok=False,
            entries=(),
            error=f"Timed out after {timeout_sec}s: {' '.join(command)}",
        )
    except OSError as exc:
        fallback = _query_local_harness_roots(
            agent_id,
            home=home,
            reason=f"Fallback local skill-root inventory after query error: {exc}",
        )
        if fallback is not None:
            return fallback
        return HarnessQueryResult(agent_id=agent_id, ok=False, entries=(), error=str(exc))
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "").strip()
        fallback = _query_local_harness_roots(
            agent_id,
            home=home,
            reason=f"Fallback local skill-root inventory after query failure: {error}",
        )
        if fallback is not None:
            return fallback
        return HarnessQueryResult(
            agent_id=agent_id,
            ok=False,
            entries=(),
            error=error,
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fallback = _query_local_harness_roots(
            agent_id,
            home=home,
            reason=f"Fallback local skill-root inventory after invalid JSON: {exc}",
        )
        if fallback is not None:
            return fallback
        return HarnessQueryResult(agent_id=agent_id, ok=False, entries=(), error=f"Invalid JSON: {exc}")
    entries: list[HarnessSkillEntry] = []
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            entries.append(
                HarnessSkillEntry(
                    queried_agent=agent_id,
                    name=str(item.get("name") or ""),
                    path=str(item.get("path") or ""),
                    scope=str(item.get("scope") or ""),
                    raw_agents=tuple(str(agent) for agent in item.get("agents", []) if str(agent).strip()),
                )
            )
    query = HarnessQueryResult(agent_id=agent_id, ok=True, entries=tuple(entries))
    return _merge_local_skill_roots_into_query(query, home=home)


def _append_local_skill_root_entries(
    entries: list[HarnessSkillEntry],
    entries_by_name: dict[str, HarnessSkillEntry],
    *,
    agent_id: str,
    skill_root: Path,
    label: str,
    scope: str,
) -> None:
    if not skill_root.is_dir():
        return
    for skill_dir in sorted(skill_root.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue
        frontmatter, _ = _read_skill_metadata(skill_dir)
        name = str(frontmatter.get("name") or skill_dir.name).strip()
        if not name:
            continue
        entry = HarnessSkillEntry(
            queried_agent=agent_id,
            name=name,
            path=str(skill_dir),
            scope=scope,
            raw_agents=(label,),
        )
        existing = entries_by_name.get(name)
        if existing is not None:
            continue
        entries_by_name[name] = entry
        entries.append(entry)


def _merge_local_skill_roots_into_query(
    query: HarnessQueryResult,
    *,
    home: Path,
) -> HarnessQueryResult:
    """Augment a successful Skills CLI query with on-disk skill roots.

    ``npx skills ls`` omits ``metadata.internal`` skills and other copies that
    exist only under harness-specific directories (for example ``~/.cursor/skills``
    or the universal ``~/.agents/skills`` tree). Merging local roots keeps sync
    parity aligned with runtime discovery.

    ``installed_agents`` may include a harness when a skill is visible on disk for
    that harness's configured roots, even if the Skills CLI adapter did not list it.
    Treat that as disk-visible coverage, not proof that the harness runtime loaded
    the skill through its primary discovery path.
    """
    root_specs = LOCAL_SKILL_ROOT_FALLBACKS.get(query.agent_id)
    if not root_specs:
        return query
    entries = list(query.entries)
    entries_by_name = {entry.name: entry for entry in entries if entry.name}
    for relative_root, label in root_specs:
        _append_local_skill_root_entries(
            entries,
            entries_by_name,
            agent_id=query.agent_id,
            skill_root=(home / relative_root).expanduser(),
            label=label,
            scope="global",
        )
    return HarnessQueryResult(
        agent_id=query.agent_id,
        ok=query.ok,
        entries=tuple(entries),
        error=query.error,
    )


def _query_local_harness_roots(agent_id: str, *, home: Path, reason: str) -> HarnessQueryResult | None:
    root_specs = LOCAL_SKILL_ROOT_FALLBACKS.get(agent_id)
    if not root_specs:
        return None
    entries: list[HarnessSkillEntry] = []
    entries_by_name: dict[str, HarnessSkillEntry] = {}
    for relative_root, label in root_specs:
        _append_local_skill_root_entries(
            entries,
            entries_by_name,
            agent_id=agent_id,
            skill_root=(home / relative_root).expanduser(),
            label=label,
            scope="global",
        )
    if not entries:
        return None
    return HarnessQueryResult(agent_id=agent_id, ok=True, entries=tuple(entries), error=reason)


def _append_grok_skill_entries(
    entries: list[HarnessSkillEntry],
    entries_by_name: dict[str, HarnessSkillEntry],
    *,
    skill_root: Path,
    label: str,
    scope: str,
) -> None:
    if not skill_root.is_dir():
        return
    for skill_dir in sorted(skill_root.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue
        frontmatter, _ = _read_skill_metadata(skill_dir)
        name = str(frontmatter.get("name") or skill_dir.name).strip()
        if not name:
            continue
        entry = HarnessSkillEntry(
            queried_agent="grok",
            name=name,
            path=str(skill_dir),
            scope=scope,
            raw_agents=(label,),
        )
        existing = entries_by_name.get(name)
        if existing is not None and scope != "project":
            continue
        if existing is not None and existing.scope == "project" and scope != "project":
            continue
        if existing is not None and existing in entries:
            entries.remove(existing)
        entries_by_name[name] = entry
        entries.append(entry)


def _query_grok_harness(home: Path, *, repo_root: Path | None = None) -> HarnessQueryResult:
    """Scan Grok-native, Claude-compat global, and optional repo project skill directories."""
    entries: list[HarnessSkillEntry] = []
    entries_by_name: dict[str, HarnessSkillEntry] = {}
    for relative_root, label in GROK_SKILL_SCAN_SOURCES:
        _append_grok_skill_entries(
            entries,
            entries_by_name,
            skill_root=(home / relative_root).expanduser(),
            label=label,
            scope="global",
        )
    if repo_root is not None:
        _append_grok_skill_entries(
            entries,
            entries_by_name,
            skill_root=repo_root / ".grok" / "skills",
            label="Grok Build (project)",
            scope="project",
        )
    return HarnessQueryResult(agent_id="grok", ok=True, entries=tuple(entries))


def mirror_grok_skills_from_claude(*, home: Path | None = None) -> int:
    """Symlink Claude Code and Skills CLI global skills into ``~/.grok/skills`` when absent."""
    home_dir = home or Path.home()
    source_roots = (
        home_dir / ".claude" / "skills",
        home_dir / ".agents" / "skills",
    )
    grok_root = home_dir / ".grok" / "skills"
    grok_root.mkdir(parents=True, exist_ok=True)
    mirrored = 0
    for source_root in source_roots:
        if not source_root.is_dir():
            continue
        for skill_dir in sorted(source_root.iterdir()):
            if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
                continue
            dest = grok_root / skill_dir.name
            if dest.exists():
                continue
            dest.symlink_to(skill_dir, target_is_directory=True)
            mirrored += 1
    return mirrored


def _run_harness_command(command: list[str], *, runner: Any, timeout_sec: int) -> subprocess.CompletedProcess[str]:
    if runner is not subprocess.run:
        return runner(command, capture_output=True, text=True, check=False, timeout=timeout_sec)

    with tempfile.TemporaryDirectory(prefix="wagents-skills-ls-") as tmpdir:
        stdout_path = Path(tmpdir) / "stdout.json"
        stderr_path = Path(tmpdir) / "stderr.txt"
        timed_out = False
        with (
            stdout_path.open("w", encoding="utf-8") as stdout_file,
            stderr_path.open("w", encoding="utf-8") as stderr_file,
        ):
            process = subprocess.Popen(
                command,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                start_new_session=True,
            )
            try:
                process.wait(timeout=timeout_sec)
            except subprocess.TimeoutExpired:
                timed_out = True
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    with suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait()

        stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
        if timed_out:
            raise subprocess.TimeoutExpired(command, timeout_sec, output=stdout, stderr=stderr)
        return subprocess.CompletedProcess(command, process.returncode, stdout=stdout, stderr=stderr)


def _read_skill_metadata(skill_dir: Path) -> tuple[dict[str, object], dict[str, object]]:
    frontmatter: dict[str, object] = {}
    metadata_json: dict[str, object] = {}
    skill_file = skill_dir / "SKILL.md"
    if skill_file.exists():
        try:
            frontmatter, _ = parse_frontmatter(skill_file.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            frontmatter = {}
    metadata_file = skill_dir / "metadata.json"
    if metadata_file.exists():
        try:
            payload = json.loads(metadata_file.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                metadata_json = payload
        except (OSError, json.JSONDecodeError):
            metadata_json = {}
    return frontmatter, metadata_json


def _metadata_value(frontmatter: dict[str, object], metadata_json: dict[str, object], key: str) -> str:
    meta = frontmatter.get("metadata")
    if isinstance(meta, dict):
        typed_meta = cast("dict[str, object]", meta)
        value = typed_meta.get(key)
        if value:
            return str(value)
    if metadata_json.get(key):
        return str(metadata_json[key])
    return ""


def _normalize_agents(raw_agents: set[object]) -> set[str]:
    normalized: set[str] = set()
    for raw_agent in raw_agents:
        label = str(raw_agent).strip()
        if not label:
            continue
        agent_id = AGENT_LABEL_TO_ID.get(label)
        if agent_id:
            normalized.add(agent_id)
    return normalized


def _is_repo_owned_skill(skill_dir: Path, repo_root: Path, name: str) -> bool:
    repo_skill_dir = (repo_root / "skills" / name).resolve(strict=False)
    try:
        return skill_dir.resolve(strict=False) == repo_skill_dir
    except OSError:
        return False


def _canonical_install_command(name: str, install_source: str, selector_mode: str, provenance_status: str) -> str:
    if provenance_status in {"curated-unresolved", "read-only-discovered"} or not install_source:
        return ""
    if selector_mode == "source-spec":
        return f"npx skills add {install_source} -y -g"
    if selector_mode == "wildcard":
        return f'npx skills add {install_source} --skill "*" -y -g'
    return f"npx skills add {install_source} --skill {name} -y -g"


def _repo_source() -> str:
    from wagents.site_model import REPO_SOURCE

    return REPO_SOURCE


def resolve_repo_install_source(name: str, *, repo_root: Path | None = None) -> str:
    """Prefer the local clone path when a repo-owned skill exists on disk.

    Unpublished repo skills (for example ``trafilatura`` before bundle publish) fail
    when sync only targets ``github:wyattowalsh/agents``.
    """
    root = (repo_root or ROOT).resolve()
    skill_file = root / "skills" / name / "SKILL.md"
    if skill_file.is_file():
        return str(root)
    return _repo_source()


def _source_url(source: str) -> str:
    normalized = source.removeprefix("github:")
    if normalized.count("@") == 1 and not normalized.startswith("@"):
        normalized = normalized.rpartition("@")[0]
    if "/" in normalized and normalized.count("/") == 1:
        return f"https://github.com/{normalized}"
    if "." in normalized:
        return f"https://{normalized}"
    return ""


def repo_skill_exposure_owner_for_agent(
    agent_id: str,
    *,
    home: Path | None = None,
    root: Path | None = None,
) -> str:
    """Return the preferred owner for repo-owned skills in one harness."""
    home_dir = home or Path.home()
    repo_root = root or ROOT
    if agent_id == "codex" and _codex_agents_plugin_enabled(home_dir):
        return EXPOSURE_OWNER_PLUGIN
    if agent_id == "opencode" and _opencode_repo_skills_path_configured(home_dir, repo_root):
        return EXPOSURE_OWNER_DIRECT_REPO_PATH
    return EXPOSURE_OWNER_SKILLS_CLI


def repo_skill_owner_covered_agents(
    row: InstalledSkillInventoryRow,
    agent_ids: Sequence[str],
    *,
    home: Path | None = None,
    root: Path | None = None,
) -> tuple[str, ...]:
    """Return target agents whose repo skill exposure is owned outside Skills CLI."""
    if not row.is_repo_owned():
        return ()
    return tuple(
        agent_id
        for agent_id in agent_ids
        if repo_skill_exposure_owner_for_agent(agent_id, home=home, root=root) != EXPOSURE_OWNER_SKILLS_CLI
    )


def _codex_agents_plugin_enabled(home: Path) -> bool:
    config_path = home / ".codex" / "config.toml"
    try:
        payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return False
    plugins = payload.get("plugins")
    if not isinstance(plugins, dict):
        return False
    agents_plugin = plugins.get("agents@agents")
    return isinstance(agents_plugin, dict) and bool(agents_plugin.get("enabled"))


def _opencode_repo_skills_path_configured(home: Path, repo_root: Path) -> bool:
    candidate_paths = (repo_root / "opencode.json", home / ".config" / "opencode" / "opencode.json")
    repo_skills = (repo_root / "skills").resolve(strict=False)
    for config_path in candidate_paths:
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        skills = payload.get("skills")
        if not isinstance(skills, dict):
            continue
        paths = skills.get("paths")
        if not isinstance(paths, list):
            continue
        for raw_path in paths:
            resolved = _resolve_config_path(str(raw_path), base=config_path.parent, home=home)
            if resolved.resolve(strict=False) == repo_skills:
                return True
    return False


def _resolve_config_path(raw_path: str, *, base: Path, home: Path) -> Path:
    path = raw_path.replace("~", str(home), 1) if raw_path == "~" or raw_path.startswith("~/") else raw_path
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = base / candidate
    return candidate


def _docs_status_for_skill(name: str, *, repo_owned: bool, root: Path) -> str:
    if not repo_owned:
        return DOCS_STATUS_NOT_APPLICABLE
    docs_candidates = (
        root / "docs" / "src" / "authoring" / "skills" / f"{name}.mdx",
        root / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "custom" / f"{name}.mdx",
    )
    if any(path.exists() for path in docs_candidates):
        return DOCS_STATUS_DOCUMENTED
    return DOCS_STATUS_GENERATED_MISSING


def _file_hash(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 128), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _tree_hash(skill_dir: Path) -> str:
    if not skill_dir.exists():
        return ""
    digest = sha256()
    try:
        for path in _tree_hash_paths(skill_dir):
            if not path.is_file():
                continue
            relative = path.relative_to(skill_dir).as_posix()
            digest.update(relative.encode("utf-8", errors="replace"))
            digest.update(b"\0")
            digest.update(_file_hash(path).encode("ascii"))
            digest.update(b"\0")
    except OSError:
        return ""
    return digest.hexdigest()


def _tree_hash_paths(skill_dir: Path) -> list[Path]:
    paths = [skill_dir / name for name in TREE_HASH_ALWAYS_FILES]
    extra_paths: list[Path] = []
    for item in sorted(skill_dir.iterdir(), key=lambda item: item.name):
        if item.name in TREE_HASH_ALWAYS_FILES:
            continue
        if item.is_file():
            extra_paths.append(item)
        elif item.name in TREE_HASH_INCLUDED_DIRS and item.is_dir() and not item.is_symlink():
            for current, dirnames, filenames in os.walk(item, followlinks=False):
                dirnames[:] = sorted(name for name in dirnames if name not in TREE_HASH_IGNORED_DIRS)
                for filename in sorted(filenames):
                    extra_paths.append(Path(current) / filename)
    paths.extend(sorted(extra_paths, key=lambda path: path.relative_to(skill_dir).as_posix()))
    return paths


def _iter_skill_exposures(*, root: Path, home: Path) -> list[SkillExposure]:
    exposures: list[SkillExposure] = []
    root_specs = [
        *(
            (harness, home / relative_root, owner, scope)
            for harness, relative_root, owner, scope in SKILL_EXPOSURE_ROOTS
        ),
        *(
            (harness, root / relative_root, owner, scope)
            for harness, relative_root, owner, scope in PROJECT_SKILL_EXPOSURE_ROOTS
        ),
    ]
    seen_paths: set[tuple[str, str, str]] = set()
    for harness, skill_root, owner, scope in root_specs:
        skill_root = skill_root.expanduser()
        if not skill_root.is_dir():
            continue
        for skill_dir in sorted(skill_root.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_dir.is_dir() or not skill_file.exists():
                continue
            key = (harness, scope, str(skill_dir))
            if key in seen_paths:
                continue
            seen_paths.add(key)
            frontmatter, _ = _read_skill_metadata(skill_dir)
            name = str(frontmatter.get("name") or skill_dir.name).strip()
            if not name:
                continue
            resolved_dir = skill_dir.resolve(strict=False)
            resolved_skill_file = resolved_dir / "SKILL.md"
            repo_owned = _is_repo_owned_skill(resolved_dir, root, name)
            canonical_owner = (
                repo_skill_exposure_owner_for_agent(harness, home=home, root=root) if repo_owned else owner
            )
            exposures.append(
                SkillExposure(
                    name=name,
                    harness=harness,
                    root=str(skill_root),
                    path=str(skill_dir),
                    source_path=str(resolved_skill_file if resolved_skill_file.exists() else skill_file),
                    resolved_path=str(resolved_dir),
                    scope=scope,
                    exposure_owner=owner,
                    canonical_owner=canonical_owner,
                    repo_owned=repo_owned,
                    is_symlink=skill_dir.is_symlink(),
                    skill_hash=_file_hash(resolved_skill_file if resolved_skill_file.exists() else skill_file),
                    tree_hash=_tree_hash(resolved_dir),
                    docs_status=_docs_status_for_skill(name, repo_owned=repo_owned, root=root),
                )
            )
    return exposures


def _duplicate_class_for_group(exposures: list[SkillExposure]) -> str:
    if len(exposures) <= 1:
        return DUPLICATE_CLASS_NONE
    realpaths = {item.resolved_path for item in exposures if item.resolved_path}
    if len(realpaths) <= 1:
        return DUPLICATE_CLASS_SAME_REALPATH
    tree_hashes = {item.tree_hash for item in exposures if item.tree_hash}
    if len(tree_hashes) <= 1:
        return DUPLICATE_CLASS_SAME_BODY
    return DUPLICATE_CLASS_DIVERGENT_BODY


def _cleanup_action_for_exposure(exposure: SkillExposure, duplicate_class: str) -> str:
    if duplicate_class == DUPLICATE_CLASS_DIVERGENT_BODY:
        return CLEANUP_ACTION_MANUAL_REVIEW
    if (
        exposure.repo_owned
        and exposure.is_symlink
        and exposure.exposure_owner != exposure.canonical_owner
        and exposure.canonical_owner in {EXPOSURE_OWNER_PLUGIN, EXPOSURE_OWNER_DIRECT_REPO_PATH}
    ):
        return CLEANUP_ACTION_REMOVE_GENERATED_SYMLINK
    if exposure.repo_owned:
        return CLEANUP_ACTION_NONE
    return CLEANUP_ACTION_PRESERVE


def collect_skill_cleanup_exposures(*, root: Path | None = None, home: Path | None = None) -> tuple[SkillExposure, ...]:
    """Return read-only skill exposures annotated with duplicate and cleanup classes."""
    repo_root = root or ROOT
    home_dir = home or Path.home()
    exposures = _iter_skill_exposures(root=repo_root, home=home_dir)
    by_name: dict[str, list[SkillExposure]] = {}
    for exposure in exposures:
        by_name.setdefault(exposure.name, []).append(exposure)
    annotated: list[SkillExposure] = []
    for group in by_name.values():
        duplicate_class = _duplicate_class_for_group(group)
        for exposure in group:
            annotated.append(
                replace(
                    exposure,
                    duplicate_class=duplicate_class,
                    cleanup_action=_cleanup_action_for_exposure(exposure, duplicate_class),
                )
            )
    return tuple(sorted(annotated, key=lambda item: (item.name, item.harness, item.scope, item.path)))


def _highest_priority(values: set[str], priorities: dict[str, int], default: str) -> str:
    if not values:
        return default
    return max(values, key=lambda value: (priorities.get(value, -1), value))


def skill_cleanup_metadata_for_exposures(
    exposures: Sequence[SkillExposure],
    *,
    fallback_docs_status: str = DOCS_STATUS_NOT_APPLICABLE,
    fallback_exposure_owner: str = EXPOSURE_OWNER_SKILLS_CLI,
) -> dict[str, str]:
    """Summarize per-exposure cleanup data for one skill-level reconciliation row."""
    if not exposures:
        return {
            "exposure_owner": fallback_exposure_owner,
            "duplicate_class": DUPLICATE_CLASS_NONE,
            "cleanup_action": CLEANUP_ACTION_NONE,
            "docs_status": fallback_docs_status or DOCS_STATUS_NOT_APPLICABLE,
        }

    duplicate_classes = {exposure.duplicate_class for exposure in exposures}
    cleanup_actions = {exposure.cleanup_action for exposure in exposures}
    docs_statuses = {exposure.docs_status for exposure in exposures}
    owners = {
        str(exposure.canonical_owner or exposure.exposure_owner)
        for exposure in exposures
        if exposure.canonical_owner or exposure.exposure_owner
    }
    return {
        "exposure_owner": sorted(owners)[0] if len(owners) == 1 else "multi-owner",
        "duplicate_class": _highest_priority(
            duplicate_classes,
            DUPLICATE_CLASS_PRIORITY,
            DUPLICATE_CLASS_NONE,
        ),
        "cleanup_action": _highest_priority(
            cleanup_actions,
            CLEANUP_ACTION_PRIORITY,
            CLEANUP_ACTION_NONE,
        ),
        "docs_status": _highest_priority(
            docs_statuses,
            DOCS_STATUS_PRIORITY,
            fallback_docs_status or DOCS_STATUS_NOT_APPLICABLE,
        ),
    }


def _git_head(path: Path) -> str:
    if not (path / ".git").exists():
        return ""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _plugin_cleanup_rows(*, root: Path, home: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    codex_cache = home / ".codex" / "plugins" / "cache" / "agents" / "agents" / "local"
    cache_head = _git_head(codex_cache)
    repo_head = _git_head(root)
    if _codex_agents_plugin_enabled(home):
        stale = bool(cache_head and repo_head and cache_head != repo_head)
        cache_missing = bool(repo_head and not cache_head)
        repo_unreadable = not repo_head
        cleanup_action = CLEANUP_ACTION_NONE
        evidence = "Codex agents plugin owns repo skills when enabled; cache refresh is approval-gated."
        if repo_unreadable:
            cleanup_action = CLEANUP_ACTION_MANUAL_REVIEW
            evidence = "Codex agents plugin is enabled, but the repo HEAD could not be read."
        elif stale or cache_missing:
            cleanup_action = CLEANUP_ACTION_REFRESH_PLUGIN_CACHE
            if cache_missing:
                evidence = "Codex agents plugin is enabled, but its local cache has no readable HEAD."
            else:
                evidence = "Codex agents plugin cache HEAD differs from the repo HEAD."
        rows.append({
            "asset_type": "plugin-cache",
            "harness": "codex",
            "name": "agents@agents-cache",
            "exposure_owner": EXPOSURE_OWNER_PLUGIN,
            "cleanup_action": cleanup_action,
            "risk": "approval-required" if cleanup_action != CLEANUP_ACTION_NONE else "none",
            "source_path": str(codex_cache),
            "installed_state": {"cache_head": cache_head[:12], "repo_head": repo_head[:12]},
            "docs_status": DOCS_STATUS_DOCUMENTED,
            "evidence": evidence,
        })

    repo_config = _safe_json(root / "opencode.json")
    live_config = _safe_json(home / ".config" / "opencode" / "opencode.json")
    repo_plugins = {_plugin_name(item) for item in repo_config.get("plugin", []) if _plugin_name(item)}
    live_plugins = {_plugin_name(item) for item in live_config.get("plugin", []) if _plugin_name(item)}
    for name in sorted(repo_plugins - live_plugins):
        rows.append({
            "asset_type": "plugin",
            "harness": "opencode",
            "name": name,
            "exposure_owner": EXPOSURE_OWNER_DIRECT_REPO_PATH,
            "cleanup_action": CLEANUP_ACTION_SYNC_HOME_CONFIG,
            "risk": "approval-required",
            "source_path": "opencode.json",
            "installed_state": {"repo": True, "live": False},
            "docs_status": DOCS_STATUS_DOCUMENTED,
            "evidence": "Repo-managed OpenCode plugin is absent from live config; sync is approval-gated.",
        })
    return rows


def _safe_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _plugin_name(spec: Any) -> str:
    if isinstance(spec, str):
        return spec
    if isinstance(spec, list) and spec:
        return str(spec[0])
    return ""


def build_skill_cleanup_report(*, root: Path | None = None, home: Path | None = None) -> dict[str, object]:
    """Build a read-only cleanup plan for local harness skill/plugin exposure."""
    repo_root = root or ROOT
    home_dir = home or Path.home()
    exposures = collect_skill_cleanup_exposures(root=repo_root, home=home_dir)
    skill_rows = [exposure.public_dict() for exposure in exposures]
    plugin_rows = _plugin_cleanup_rows(root=repo_root, home=home_dir)
    action_counts: dict[str, int] = {}
    duplicate_counts: dict[str, int] = {}
    docs_counts: dict[str, int] = {}
    for row in [*skill_rows, *plugin_rows]:
        action = str(row.get("cleanup_action") or CLEANUP_ACTION_NONE)
        action_counts[action] = action_counts.get(action, 0) + 1
        docs_status = str(row.get("docs_status") or DOCS_STATUS_NOT_APPLICABLE)
        docs_counts[docs_status] = docs_counts.get(docs_status, 0) + 1
        if row.get("asset_type") != "plugin" and row.get("asset_type") != "plugin-cache":
            duplicate_class = str(row.get("duplicate_class") or DUPLICATE_CLASS_NONE)
            duplicate_counts[duplicate_class] = duplicate_counts.get(duplicate_class, 0) + 1
    return {
        "ok": True,
        "mode": "dry-run",
        "summary": {
            "skill_exposure_count": len(skill_rows),
            "plugin_row_count": len(plugin_rows),
            "cleanup_action_counts": dict(sorted(action_counts.items())),
            "duplicate_class_counts": dict(sorted(duplicate_counts.items())),
            "docs_status_counts": dict(sorted(docs_counts.items())),
        },
        "skills": skill_rows,
        "plugins": plugin_rows,
    }


def _load_installed_skill_sources(*, home: Path) -> dict[str, dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    candidates = [
        home / ".agents" / ".skill-lock.json",
        home / ".local" / "state" / "skills" / ".skill-lock.json",
    ]
    for lock_path in candidates:
        if not lock_path.exists():
            continue
        try:
            payload = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        skills = payload.get("skills", {})
        if isinstance(skills, dict):
            for name, metadata in skills.items():
                if isinstance(metadata, dict):
                    merged[str(name)] = {str(key): value for key, value in metadata.items()}
    return merged


def cast_set(value: object) -> set[Any]:
    if isinstance(value, set):
        return value
    raise TypeError("Expected set during inventory aggregation.")


def external_entry_to_inventory_row(entry: ExternalSkillEntry) -> InstalledSkillInventoryRow:
    """Build a desired sync row from a curated external authoring entry."""
    provenance_status = "verified-curated-external"
    install_command = entry.install_command
    return InstalledSkillInventoryRow(
        name=entry.name,
        path="",
        source_path=entry.source_path,
        scope="desired",
        description=entry.notes.strip(),
        license="",
        version="",
        author="",
        source=entry.source,
        install_source=entry.install_source,
        source_url=entry.source_url,
        install_command=install_command,
        provenance_status=provenance_status,
        trust_tier=entry.trust_tier,
        selector_mode=entry.selector_mode,
        installed_agents=(),
        discovered_in=(),
        target_agents=entry.target_agents,
        unresolved_reason="",
        sync_kind=infer_sync_kind(entry.sync_kind, install_command),
        docs_status=DOCS_STATUS_DOCUMENTED,
    )


def collect_repo_owned_desired_rows(*, root: Path | None = None) -> list[InstalledSkillInventoryRow]:
    """Return repo-owned skills as desired sync rows even when not installed."""
    repo_root = root or ROOT
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        return []

    rows: list[InstalledSkillInventoryRow] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        frontmatter, file_meta = _read_skill_metadata(skill_dir)
        name = str(frontmatter.get("name") or skill_dir.name).strip()
        if not name:
            continue
        install_source = resolve_repo_install_source(name, repo_root=repo_root)
        rows.append(
            InstalledSkillInventoryRow(
                name=name,
                path=str(skill_dir),
                source_path=str(skill_file),
                scope="repo",
                description=str(frontmatter.get("description") or file_meta.get("description") or ""),
                license=str(frontmatter.get("license") or file_meta.get("license") or ""),
                version=str(_metadata_value(frontmatter, file_meta, "version")),
                author=str(_metadata_value(frontmatter, file_meta, "author")),
                source=install_source,
                install_source=install_source,
                source_url=_source_url(install_source),
                install_command=_canonical_install_command(name, install_source, "named", "repo-owned"),
                provenance_status="repo-owned",
                trust_tier="repo",
                selector_mode="named",
                installed_agents=(),
                discovered_in=(),
                target_agents=supported_agent_ids(),
                unresolved_reason="",
                sync_kind=SYNC_KIND_SKILLS_CLI,
                exposure_owner=EXPOSURE_OWNER_SKILLS_CLI,
                docs_status=_docs_status_for_skill(name, repo_owned=True, root=repo_root),
            )
        )
    return rows


def collect_desired_sync_rows(
    *,
    root: Path | None = None,
    external_entries: list[ExternalSkillEntry] | None = None,
) -> tuple[InstalledSkillInventoryRow, ...]:
    """Return the full desired sync set: repo-owned plus Install Now curated skills."""
    rows = collect_repo_owned_desired_rows(root=root)
    rows.extend(
        external_entry_to_inventory_row(entry)
        for entry in desired_install_now_entries(external_entries=external_entries)
    )
    return tuple(rows)


def merge_desired_with_installed(
    snapshot: InstalledInventorySnapshot,
    desired: tuple[InstalledSkillInventoryRow, ...] | list[InstalledSkillInventoryRow],
) -> InstalledInventorySnapshot:
    """Overlay desired rows onto installed evidence while preserving install state."""
    by_name = {row.name: row for row in snapshot.rows}
    for row in desired:
        existing = by_name.get(row.name)
        if existing is None:
            by_name[row.name] = row
            continue
        by_name[row.name] = replace(
            existing,
            source=row.source or existing.source,
            install_source=row.install_source or existing.install_source,
            source_url=row.source_url or existing.source_url,
            install_command=(
                row.install_command
                if row.install_command
                and (
                    row.provenance_status == "verified-curated-external"
                    or row.provenance_status == "repo-owned"
                )
                else (row.install_command or existing.install_command)
            ),
            provenance_status=row.provenance_status or existing.provenance_status,
            trust_tier=row.trust_tier or existing.trust_tier,
            selector_mode=row.selector_mode or existing.selector_mode,
            target_agents=row.target_agents or existing.target_agents,
            unresolved_reason=row.unresolved_reason or existing.unresolved_reason,
            sync_kind=row.sync_kind or existing.sync_kind,
        )
    merged_rows = tuple(sorted(by_name.values(), key=lambda item: item.name))
    return InstalledInventorySnapshot(rows=merged_rows, queries=snapshot.queries)
