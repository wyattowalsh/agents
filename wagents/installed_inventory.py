"""Normalized installed-skill inventory across supported harnesses."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from wagents import ROOT
from wagents.external_skills import ExternalSkillEntry, desired_install_now_entries, read_external_skill_entries

# desired_install_now_entries (and callers) continue to work by delegating to (dual-read) read_external_skill_entries
from wagents.parsing import parse_frontmatter

DEFAULT_HARNESS_QUERY_TIMEOUT_SEC = 120

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

# Skills CLI has no native Grok adapter; sync installs via Claude Code paths Grok reads.
SKILLS_CLI_AGENT_ALIASES = {"grok": "claude-code"}

GROK_SKILL_SCAN_SOURCES: tuple[tuple[Path, str], ...] = (
    (Path(".grok") / "skills", "Grok Build"),
    (Path(".claude") / "skills", "Claude Code"),
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
    curated = external_entries or read_external_skill_entries()
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
        return HarnessQueryResult(
            agent_id=agent_id,
            ok=False,
            entries=(),
            error=f"Timed out after {timeout_sec}s: {' '.join(command)}",
        )
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


def external_entry_to_inventory_row(entry: ExternalSkillEntry) -> InstalledSkillInventoryRow:
    """Build a desired sync row from a curated external-skills.md entry."""
    provenance_status = "verified-curated-external"
    install_command = entry.install_command or _canonical_install_command(
        entry.name,
        entry.install_source,
        entry.selector_mode,
        provenance_status,
    )
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
        install_source = _repo_source()
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
            )
        )
    return rows


def collect_desired_sync_rows(*, root: Path | None = None) -> tuple[InstalledSkillInventoryRow, ...]:
    """Return the full desired sync set: repo-owned plus Install Now curated skills."""
    rows = collect_repo_owned_desired_rows(root=root)
    rows.extend(external_entry_to_inventory_row(entry) for entry in desired_install_now_entries())
    return tuple(rows)


def merge_desired_with_installed(
    snapshot: InstalledInventorySnapshot,
    desired: tuple[InstalledSkillInventoryRow, ...] | list[InstalledSkillInventoryRow],
) -> InstalledInventorySnapshot:
    """Overlay desired rows onto an installed snapshot without replacing installed rows."""
    by_name = {row.name: row for row in snapshot.rows}
    for row in desired:
        by_name.setdefault(row.name, row)
    merged_rows = tuple(sorted(by_name.values(), key=lambda item: item.name))
    return InstalledInventorySnapshot(rows=merged_rows, queries=snapshot.queries)
