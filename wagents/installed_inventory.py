"""Normalized installed-skill inventory across supported harnesses."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from wagents import ROOT
from wagents.external_skills import ExternalSkillEntry, read_external_skill_entries
from wagents.parsing import parse_frontmatter

AGENT_LABEL_TO_ID = {
    "Antigravity": "antigravity",
    "Claude Code": "claude-code",
    "Codex": "codex",
    "Crush": "crush",
    "Cursor": "cursor",
    "Gemini CLI": "gemini-cli",
    "GitHub Copilot": "github-copilot",
    "OpenCode": "opencode",
}


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

    def is_repo_owned(self) -> bool:
        return self.provenance_status == "repo-owned"

    def is_verified_curated(self) -> bool:
        return self.provenance_status == "verified-curated-external"

    def is_installable(self) -> bool:
        return bool(self.install_command) and self.provenance_status not in {
            "curated-unresolved",
            "read-only-discovered",
        }

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


def query_harness_skills(
    *,
    agent_ids: tuple[str, ...] | None = None,
    runner: Any = subprocess.run,
) -> tuple[HarnessQueryResult, ...]:
    """Enumerate `npx skills ls -g -a <agent> --json` for each supported harness."""
    results: list[HarnessQueryResult] = []
    for agent_id in agent_ids or supported_agent_ids():
        results.append(_query_one_harness(agent_id, runner=runner))
    return tuple(results)


def collect_installed_inventory(
    *,
    agent_ids: tuple[str, ...] | None = None,
    root: Path | None = None,
    home: Path | None = None,
    runner: Any = subprocess.run,
    external_entries: list[ExternalSkillEntry] | None = None,
) -> InstalledInventorySnapshot:
    """Build one normalized installed-skill inventory snapshot."""
    repo_root = root or ROOT
    home_dir = home or Path.home()
    curated = external_entries or read_external_skill_entries()
    curated_by_name: dict[str, ExternalSkillEntry] = {}
    for entry in curated:
        existing = curated_by_name.get(entry.name)
        if existing is None or entry.provenance_status == "verified-install-command":
            curated_by_name[entry.name] = entry
    lock_sources = _load_installed_skill_sources(home=home_dir)
    queries = query_harness_skills(agent_ids=agent_ids, runner=runner)

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
        installed_agents = tuple(sorted(_normalize_agents(cast_set(raw["raw_agents"]))))
        discovered_in = tuple(sorted(cast_set(raw["discovered_in"])))
        source_path = str((resolved_dir / "SKILL.md") if (resolved_dir / "SKILL.md").exists() else skill_dir)

        repo_owned = _is_repo_owned_skill(resolved_dir, repo_root, name)
        if repo_owned:
            source = _repo_source()
            install_source = _repo_source()
            provenance_status = "repo-owned"
            trust_tier = "repo"
            selector_mode = "named"
            target_agents = supported_agent_ids()
            unresolved_reason = ""
        elif curated_entry is not None and curated_entry.provenance_status == "verified-install-command":
            source = curated_entry.source
            install_source = curated_entry.install_source
            provenance_status = "verified-curated-external"
            trust_tier = curated_entry.trust_tier
            selector_mode = curated_entry.selector_mode
            target_agents = curated_entry.target_agents
            unresolved_reason = ""
        elif curated_entry is not None:
            source = curated_entry.source
            install_source = curated_entry.install_source
            provenance_status = "curated-unresolved"
            trust_tier = curated_entry.trust_tier
            selector_mode = curated_entry.selector_mode
            target_agents = curated_entry.target_agents
            unresolved_reason = curated_entry.unresolved_reason or curated_entry.notes
        elif isinstance(lock_meta, dict) and lock_meta.get("source"):
            source = str(lock_meta["source"])
            install_source = source
            provenance_status = "installed-external"
            trust_tier = str(lock_meta.get("sourceType") or "external-installed")
            selector_mode = "named"
            target_agents = ()
            unresolved_reason = ""
        else:
            source = str(fm.get("_skills_source") or "")
            install_source = source
            provenance_status = "read-only-discovered"
            trust_tier = "read-only-discovered"
            selector_mode = "named"
            target_agents = ()
            unresolved_reason = "No lockfile or curated source was found for this installed skill."

        install_command = _canonical_install_command(name, install_source, selector_mode, provenance_status)
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
            )
        )

    return InstalledInventorySnapshot(rows=tuple(rows), queries=queries)


def _query_one_harness(agent_id: str, *, runner: Any) -> HarnessQueryResult:
    command = ["npx", "-y", "skills", "ls", "-g", "-a", agent_id, "--json"]
    try:
        result = runner(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        return HarnessQueryResult(agent_id=agent_id, ok=False, entries=(), error=str(exc))
    if result.returncode != 0:
        return HarnessQueryResult(
            agent_id=agent_id,
            ok=False,
            entries=(),
            error=(result.stderr or result.stdout or "").strip(),
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
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
    return HarnessQueryResult(agent_id=agent_id, ok=True, entries=tuple(entries))


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
        typed_meta = cast(dict[str, object], meta)
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


def _source_url(source: str) -> str:
    normalized = source.removeprefix("github:")
    if normalized.count("@") == 1 and not normalized.startswith("@"):
        normalized = normalized.rpartition("@")[0]
    if "/" in normalized and normalized.count("/") == 1:
        return f"https://github.com/{normalized}"
    if "." in normalized:
        return f"https://{normalized}"
    return ""


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
