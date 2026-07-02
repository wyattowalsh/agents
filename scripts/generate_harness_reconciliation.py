#!/usr/bin/env python3
"""Generate a redacted local harness skill/plugin reconciliation manifest."""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wagents import ROOT
from wagents.cli import collect_desired_sync_rows
from wagents.external_skills import read_external_skill_entries
from wagents.installed_inventory import (
    CLEANUP_ACTION_MANUAL_REVIEW,
    CLEANUP_ACTION_NONE,
    CLEANUP_ACTION_PRESERVE,
    CLEANUP_ACTION_REFRESH_PLUGIN_CACHE,
    CLEANUP_ACTION_SYNC_HOME_CONFIG,
    DOCS_STATUS_DOCUMENTED,
    DOCS_STATUS_NOT_APPLICABLE,
    DUPLICATE_CLASS_NONE,
    EXPOSURE_OWNER_PLUGIN,
    EXPOSURE_OWNER_SKILLS_CLI,
    collect_installed_inventory,
    collect_skill_cleanup_exposures,
    merge_desired_with_installed,
    repo_skill_owner_covered_agents,
    skill_cleanup_metadata_for_exposures,
    supported_agent_ids,
)

OUT = ROOT / "planning" / "manifests" / "harness-reconciliation.json"
HOME = Path.home()
TERMINAL_ACTIONS = {
    "synced",
    "repo-source-synced",
    "local-only-preserve",
    "curate-external",
    "catalog-non-sync",
    "cache-refresh-needed",
    "home-sync-needed",
    "blocked-needs-approval",
    "config-repair-needed",
}


def _redact(value: str) -> str:
    text = str(value)
    repo = str(ROOT)
    home = str(HOME)
    if text.startswith(repo):
        text = "${REPO_ROOT}" + text[len(repo) :]
    elif text.startswith(home):
        text = "~" + text[len(home) :]
    return text.replace(home, "~").replace(repo, "${REPO_ROOT}")


def _sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return _redact(value)
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    return value


def _run(command: list[str], *, cwd: Path = ROOT, timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "command": command, "returncode": None, "stdout": "", "stderr": str(exc)}
    return {
        "ok": result.returncode == 0,
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


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


def _toml_plugin_headings(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    return re.findall(r'^\[plugins\."([^"]+)"\]', text, flags=re.MULTILINE)


def _skill_disposition(
    row: Any,
    all_agents: tuple[str, ...],
    missing: set[str],
    unknown: set[str],
) -> tuple[str, str, str]:
    if row.provenance_status in {"repo-owned", "verified-curated-external"}:
        if not missing:
            if unknown:
                return "blocked-needs-approval", "blocked-needs-approval", (
                    "Target harness inventory was unavailable, so install coverage cannot be asserted for that harness."
                )
            return "synced", "synced", "Desired skill is visible in every target harness."
        return "home-sync-needed", "home-sync-needed", "Desired skill is missing from one or more target harnesses."
    if row.provenance_status == "installed-external":
        return "local-only-preserve", "local-only-preserve", (
            "Installed external is outside the curated desired set; preserve locally until explicitly promoted."
        )
    if row.provenance_status == "curated-unresolved":
        return "catalog-non-sync", "catalog-non-sync", "Catalog row is explicitly non-syncing or unresolved."
    if row.provenance_status == "read-only-discovered":
        return "local-only-preserve", "local-only-preserve", (
            "No trusted install provenance was found; keep local-only and do not sync or promote automatically."
        )
    return "blocked-needs-approval", "blocked-needs-approval", "Unknown provenance requires maintainer review."


def _skill_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    external_entries = read_external_skill_entries(strict=True)
    snapshot = collect_installed_inventory(external_entries=external_entries, query_timeout_sec=300)
    desired = collect_desired_sync_rows(external_entries=external_entries)
    merged = merge_desired_with_installed(snapshot, desired)
    cleanup_by_name: dict[str, list[Any]] = defaultdict(list)
    for exposure in collect_skill_cleanup_exposures():
        cleanup_by_name[exposure.name].append(exposure)
    all_agents = supported_agent_ids()
    failed_agents = {query.agent_id for query in snapshot.queries if not query.ok}
    rows: list[dict[str, Any]] = []
    default_missing_by_agent: dict[str, int] = dict.fromkeys(all_agents, 0)
    include_installed_missing_by_agent: dict[str, int] = dict.fromkeys(all_agents, 0)
    query_blocked_by_agent: dict[str, int] = dict.fromkeys(all_agents, 0)

    desired_names = {row.name for row in desired}
    for row in merged.rows:
        if row.provenance_status == "read-only-discovered" and not row.target_agents:
            target_agents = tuple(row.installed_agents)
        else:
            target_agents = tuple(row.target_agents or all_agents)
        unknown = set(target_agents) & failed_agents
        owner_covered = set(repo_skill_owner_covered_agents(row, target_agents, home=HOME, root=ROOT))
        missing = set(target_agents) - set(row.installed_agents) - unknown - owner_covered
        classification, action, rationale = _skill_disposition(row, all_agents, missing, unknown)
        if owner_covered and row.provenance_status == "repo-owned" and classification == "synced":
            rationale = (
                "Repo-owned skill is covered by a native plugin or direct repo skill path for "
                f"{', '.join(sorted(owner_covered))}; no duplicate Skills CLI install is recommended."
            )
        cleanup_meta = skill_cleanup_metadata_for_exposures(
            cleanup_by_name.get(row.name, ()),
            fallback_docs_status=row.docs_status,
        )
        if row.name in desired_names or row.provenance_status in {"repo-owned", "verified-curated-external"}:
            for agent in missing:
                default_missing_by_agent[agent] = default_missing_by_agent.get(agent, 0) + 1
            for agent in unknown:
                query_blocked_by_agent[agent] = query_blocked_by_agent.get(agent, 0) + 1
        if row.provenance_status in {"repo-owned", "verified-curated-external", "installed-external"}:
            for agent in missing:
                include_installed_missing_by_agent[agent] = include_installed_missing_by_agent.get(agent, 0) + 1
        rows.append(
            {
                "asset_type": "skill",
                "harness": "multi-harness",
                "name": row.name,
                "source": row.source,
                "source_path": _redact(row.source_path),
                "scope": row.scope,
                "provenance_status": row.provenance_status,
                "trust_tier": row.trust_tier,
                "sync_kind": row.sync_kind,
                "installed_agents": list(row.installed_agents),
                "target_agents": list(target_agents),
                "missing_agents": sorted(missing),
                "owner_covered_agents": sorted(owner_covered),
                "query_blocked_agents": sorted(unknown),
                "exposure_owner": cleanup_meta["exposure_owner"],
                "duplicate_class": cleanup_meta["duplicate_class"],
                "cleanup_action": cleanup_meta["cleanup_action"],
                "docs_status": cleanup_meta["docs_status"],
                "classification": classification,
                "action": action,
                "owner": "catalog" if row.provenance_status != "read-only-discovered" else "user-local",
                "evidence": rationale,
            }
        )

    summary = {
        "inventory_count": len(merged.rows),
        "desired_count": len(desired),
        "query_errors": [
            {"agent": query.agent_id, "error": query.error}
            for query in snapshot.queries
            if not query.ok or query.error
        ],
        "provenance_counts": dict(Counter(row.provenance_status for row in merged.rows)),
        "classification_counts": dict(Counter(row["classification"] for row in rows)),
        "default_sync_missing_by_agent": default_missing_by_agent,
        "include_installed_missing_by_agent": include_installed_missing_by_agent,
        "query_blocked_by_agent": query_blocked_by_agent,
    }
    return rows, summary


def _git_head(path: Path) -> str:
    if not (path / ".git").exists():
        return ""
    result = _run(["git", "rev-parse", "HEAD"], cwd=path, timeout=5)
    return str(result["stdout"]).strip() if result["ok"] else ""


def _opencode_source_paths(*, in_repo: bool, in_live: bool, in_tui: bool) -> list[str]:
    paths = []
    if in_repo:
        paths.append("opencode.json")
    if in_live:
        paths.append("~/.config/opencode/opencode.json")
    if in_tui:
        paths.append("~/.config/opencode/tui.json")
    return paths


def _primary_source_path(source_paths: list[str]) -> str:
    return source_paths[0] if source_paths else "opencode plugin array"


def _opencode_plugin_rows() -> list[dict[str, Any]]:
    repo_config = _safe_json(ROOT / "opencode.json")
    live_config = _safe_json(HOME / ".config" / "opencode" / "opencode.json")
    tui_config = _safe_json(HOME / ".config" / "opencode" / "tui.json")
    repo_plugins = {_plugin_name(item) for item in repo_config.get("plugin", []) if _plugin_name(item)}
    live_plugins = {_plugin_name(item) for item in live_config.get("plugin", []) if _plugin_name(item)}
    tui_plugins = {_plugin_name(item) for item in tui_config.get("plugin", []) if _plugin_name(item)}
    rows: list[dict[str, Any]] = []
    for name in sorted(repo_plugins | live_plugins | tui_plugins):
        in_repo = name in repo_plugins
        in_live = name in live_plugins
        in_tui = name in tui_plugins
        if in_repo and in_live:
            classification = action = "synced"
            evidence = "Repo-managed OpenCode plugin is present in live root plugin config."
            owner = "repo"
        elif in_repo:
            classification = action = "home-sync-needed"
            evidence = "Repo-managed OpenCode plugin is absent from live root config; do not apply without approval."
            owner = "repo"
        else:
            classification = action = "local-only-preserve"
            evidence = "OpenCode plugin is live-only or TUI-only user configuration."
            owner = "user-local"
        source_paths = _opencode_source_paths(in_repo=in_repo, in_live=in_live, in_tui=in_tui)
        rows.append(
            {
                "asset_type": "plugin",
                "harness": "opencode",
                "name": name,
                "source": "opencode plugin array",
                "source_path": _primary_source_path(source_paths),
                "source_paths": source_paths,
                "installed_state": {"repo": in_repo, "live": in_live, "tui": in_tui},
                "classification": classification,
                "action": action,
                "owner": owner,
                "evidence": evidence,
            }
        )
    return rows


def _codex_plugin_rows() -> list[dict[str, Any]]:
    config_plugins = set(_toml_plugin_headings(HOME / ".codex" / "config.toml"))
    list_result = _run(["codex", "plugin", "list"], timeout=30)
    installed = set(re.findall(r"^(\S+@\S+)\s+installed, enabled", list_result["stdout"], flags=re.MULTILINE))
    cache = HOME / ".codex" / "plugins" / "cache" / "agents" / "agents" / "local"
    cache_head = _git_head(cache)
    repo_head = _git_head(ROOT)
    rows: list[dict[str, Any]] = []
    for name in sorted(config_plugins | installed):
        if name == "agents@agents" and cache_head and repo_head and cache_head != repo_head:
            classification = action = "cache-refresh-needed"
            evidence = "Configured agents plugin cache revision differs from current repo HEAD."
            owner = "repo"
        elif name in installed or name in config_plugins:
            classification = action = "local-only-preserve"
            evidence = "Codex marketplace plugin is user-selected local runtime configuration."
            owner = "user-local"
        else:
            classification = action = "blocked-needs-approval"
            evidence = "Codex plugin state could not be classified from local config/list output."
            owner = "unknown"
        rows.append(
            {
                "asset_type": "plugin",
                "harness": "codex",
                "name": name,
                "source": "codex plugin marketplace/config",
                "source_path": "~/.codex/config.toml",
                "installed_state": {"configured": name in config_plugins, "installed_enabled": name in installed},
                "classification": classification,
                "action": action,
                "owner": owner,
                "evidence": evidence,
            }
        )
    cache_stale = bool(cache_head and repo_head and cache_head != repo_head)
    rows.append(
        {
            "asset_type": "plugin-cache",
            "harness": "codex",
            "name": "agents@agents-cache",
            "source": "github:wyattowalsh/agents",
            "source_path": "~/.codex/plugins/cache/agents/agents/local",
            "installed_state": {"cache_head": cache_head[:12], "repo_head": repo_head[:12]},
            "classification": "cache-refresh-needed" if cache_stale else "synced",
            "action": "cache-refresh-needed" if cache_stale else "synced",
            "owner": "repo",
            "evidence": "Cache is a local clone of the repo plugin; refresh only after source worktree stabilizes.",
        }
    )
    return rows


def _gemini_extension_evidence(invalid_disabled: list[str]) -> str:
    if invalid_disabled:
        return "Gemini settings contain MCP disabled keys rejected by the CLI; repair before extension validation."
    return "Extension is locally installed and preserved unless promoted through catalog/registry review."


def _gemini_rows() -> list[dict[str, Any]]:
    settings = _safe_json(HOME / ".gemini" / "settings.json")
    enabled = set(settings.get("enabledPlugins", []) if isinstance(settings.get("enabledPlugins"), list) else [])
    mcp_servers = settings.get("mcpServers", {}) if isinstance(settings.get("mcpServers"), dict) else {}
    invalid_disabled = [name for name, value in mcp_servers.items() if isinstance(value, dict) and "disabled" in value]
    extension_root = HOME / ".gemini" / "extensions"
    rows: list[dict[str, Any]] = []
    if extension_root.is_dir():
        for path in sorted(extension_root.iterdir()):
            if not path.is_dir() or path.name.startswith("."):
                continue
            skill_count = len(list(path.glob("skills/*/SKILL.md")))
            command_count = len([item for item in path.glob("commands/*") if item.is_file()])
            rows.append(
                {
                    "asset_type": "extension",
                    "harness": "gemini-cli",
                    "name": path.name,
                    "source": "gemini extension directory",
                    "source_path": _redact(str(path)),
                    "installed_state": {
                        "enabled_in_settings": path.name in enabled,
                        "skill_count": skill_count,
                        "command_count": command_count,
                    },
                    "classification": "config-repair-needed" if invalid_disabled else "local-only-preserve",
                    "action": "config-repair-needed" if invalid_disabled else "local-only-preserve",
                    "owner": "user-local",
                    "evidence": _gemini_extension_evidence(invalid_disabled),
                }
            )
    if enabled:
        for name in sorted(enabled):
            rows.append(
                {
                    "asset_type": "plugin",
                    "harness": "gemini-cli",
                    "name": name,
                    "source": "enabledPlugins",
                    "source_path": "~/.gemini/settings.json",
                    "installed_state": {"enabled_in_settings": True},
                    "classification": "config-repair-needed" if invalid_disabled else "local-only-preserve",
                    "action": "config-repair-needed" if invalid_disabled else "local-only-preserve",
                    "owner": "user-local",
                    "evidence": "Gemini enabled plugin entry is local user configuration.",
                }
    )
    return rows


def _native_plugins_reported(result: dict[str, Any]) -> bool:
    if not result.get("ok"):
        return False
    stdout = str(result.get("stdout") or "").strip()
    if not stdout:
        return False
    normalized = stdout.lower()
    no_plugin_markers = (
        "no plugins installed",
        "no installed plugins",
        "no plugins found",
        "0 plugins",
    )
    return not any(marker in normalized for marker in no_plugin_markers)


def _native_plugin_evidence(
    harness: str,
    result: dict[str, Any],
    *,
    no_plugins_message: str,
    plugins_message: str,
) -> str:
    if not result.get("ok"):
        return f"{harness} native plugin list was unavailable; preserving configured reconciliation state."
    if _native_plugins_reported(result):
        return plugins_message
    return no_plugins_message


def _simple_plugin_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    claude = _run(["claude", "plugin", "list"], timeout=20)
    rows.append(
        {
            "asset_type": "plugin",
            "harness": "claude-code",
            "name": "agents-native-plugin",
            "source": ".claude-plugin/plugin.json",
            "source_path": ".claude-plugin/plugin.json",
            "installed_state": {
                "native_list_ok": claude["ok"],
                "native_plugins_reported": _native_plugins_reported(claude),
            },
            "classification": "repo-source-synced",
            "action": "repo-source-synced",
            "owner": "repo",
            "evidence": _native_plugin_evidence(
                "Claude Code",
                claude,
                no_plugins_message=(
                    "Repo plugin manifest exists; native install is not required for Skills CLI coverage."
                ),
                plugins_message=(
                    "Claude Code native plugin list returned plugin entries; repo manifest remains source-owned."
                ),
            ),
        }
    )
    grok = _run(["grok", "plugin", "list"], timeout=20)
    rows.append(
        {
            "asset_type": "plugin",
            "harness": "grok",
            "name": "native-plugin-surface",
            "source": "grok plugin list",
            "source_path": "~/.grok/config.toml",
            "installed_state": {
                "native_list_ok": grok["ok"],
                "native_plugins_reported": _native_plugins_reported(grok),
            },
            "classification": "local-only-preserve",
            "action": "local-only-preserve",
            "owner": "user-local",
            "evidence": _native_plugin_evidence(
                "Grok",
                grok,
                no_plugins_message=(
                    "Grok native plugin list reports no installed plugins; Grok skills/hooks are handled separately."
                ),
                plugins_message=(
                    "Grok native plugin list returned plugin entries; Grok skills/hooks are handled separately."
                ),
            ),
        }
    )
    for harness in ("cursor", "github-copilot", "crush", "antigravity"):
        rows.append(
            {
                "asset_type": "plugin",
                "harness": harness,
                "name": "native-plugin-surface",
                "source": "local harness config",
                "source_path": "config/plugin-extension-registry.json",
                "installed_state": {"native_plugin_surface": False},
                "classification": "repo-source-synced",
                "action": "repo-source-synced",
                "owner": "repo",
                "evidence": (
                    "No repo-managed native plugin surface beyond Skills CLI/config "
                    "projection was found for this harness."
                ),
            }
        )
    return rows


def _plugin_rows() -> list[dict[str, Any]]:
    rows = []
    rows.extend(_codex_plugin_rows())
    rows.extend(_opencode_plugin_rows())
    rows.extend(_gemini_rows())
    rows.extend(_simple_plugin_rows())
    return rows


def _cleanup_action_for_terminal_action(row: dict[str, Any]) -> str:
    action = str(row.get("action") or "")
    if action == "cache-refresh-needed":
        return CLEANUP_ACTION_REFRESH_PLUGIN_CACHE
    if action == "home-sync-needed":
        return CLEANUP_ACTION_SYNC_HOME_CONFIG
    if action == "local-only-preserve":
        return CLEANUP_ACTION_PRESERVE
    if action in {"blocked-needs-approval", "config-repair-needed", "curate-external"}:
        return CLEANUP_ACTION_MANUAL_REVIEW
    return CLEANUP_ACTION_NONE


def _default_exposure_owner(row: dict[str, Any]) -> str:
    if row.get("asset_type") == "skill":
        return EXPOSURE_OWNER_SKILLS_CLI
    if row.get("owner") == "user-local":
        return "user-local"
    return EXPOSURE_OWNER_PLUGIN


def _default_docs_status(row: dict[str, Any]) -> str:
    if row.get("owner") == "repo":
        return DOCS_STATUS_DOCUMENTED
    return DOCS_STATUS_NOT_APPLICABLE


def _with_reconciliation_defaults(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized.setdefault("exposure_owner", _default_exposure_owner(normalized))
    normalized.setdefault("duplicate_class", DUPLICATE_CLASS_NONE)
    normalized.setdefault("cleanup_action", _cleanup_action_for_terminal_action(normalized))
    normalized.setdefault("docs_status", _default_docs_status(normalized))
    return normalized


def _task_files(harness: str, asset_type: str) -> list[str]:
    files = {"planning/manifests/harness-reconciliation.json"}
    if asset_type == "skill":
        files.update({"docs/src/authoring/skills/*.mdx", "skills/*/SKILL.md"})
    if harness == "codex":
        files.update({".codex-plugin/plugin.json", ".agents/plugins/marketplace.json", "~/.codex/config.toml"})
    if harness == "claude-code":
        files.update({".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"})
    if harness == "opencode":
        files.update(
            {
                "opencode.json",
                "config/opencode-ensemble.json",
                "~/.config/opencode/opencode.json",
                "~/.config/opencode/tui.json",
            }
        )
    if harness == "gemini-cli":
        files.update({"GEMINI.md", "~/.gemini/settings.json", "~/.gemini/extensions/*"})
    if harness == "grok":
        files.update({"config/grok-config.toml", "~/.grok/config.toml", "~/.grok/skills/*"})
    if harness in {"cursor", "github-copilot", "crush", "antigravity"}:
        files.add("config/plugin-extension-registry.json")
    return sorted(files)


def _task_graph(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    graph: list[dict[str, Any]] = [
        {
            "id": "T-000",
            "lane": "coordinator",
            "parallel": False,
            "files": ["planning/manifests/harness-reconciliation.json"],
            "done_when": "Every local skill/plugin row has a terminal action, evidence, and redacted source path.",
        },
    ]

    shards: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        shards[
            row["harness"],
            row["asset_type"],
            row["action"],
            row["owner"],
            row["source"],
        ].append(row)

    shard_ids = []
    for index, ((harness, asset_type, action, owner, source), shard_rows) in enumerate(
        sorted(shards.items()),
        start=10,
    ):
        shard_id = f"T-{index:03d}"
        shard_ids.append(shard_id)
        graph.append(
            {
                "id": shard_id,
                "lane": f"{harness}:{asset_type}:{action}:{owner}:{source}",
                "parallel": True,
                "depends_on": ["T-000"],
                "filter": {
                    "action": action,
                    "asset_type": asset_type,
                    "harness": harness,
                    "owner": owner,
                    "source": source,
                },
                "files": _task_files(harness, asset_type),
                "manual_inspection": (
                    "Inspect every matrix row matching this filter and verify the action follows from evidence; "
                    "counts alone are not sufficient."
                ),
                "row_count": len(shard_rows),
                "sample_names": [row["name"] for row in sorted(shard_rows, key=lambda item: item["name"])[:12]],
                "terminal_action": action,
                "done_when": (
                    f"All {len(shard_rows)} {harness} {asset_type} row(s) with action {action} are reconciled "
                    "or explicitly deferred behind the documented stop rules."
                ),
            }
        )

    graph.append(
        {
            "id": "T-999",
            "lane": "validation",
            "parallel": False,
            "depends_on": shard_ids,
            "files": [
                "scripts/generate_harness_reconciliation.py",
                "tests/test_harness_reconciliation.py",
                "planning/manifests/harness-reconciliation.json",
            ],
            "done_when": "Focused tests, repo validation commands, redaction checks, and dry-run sync pass.",
        }
    )
    return graph


def _summary(rows: list[dict[str, Any]], skill_summary: dict[str, Any]) -> dict[str, Any]:
    by_type = Counter(row["asset_type"] for row in rows)
    by_action = Counter(row["action"] for row in rows)
    by_harness: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_harness[row["harness"]][row["action"]] += 1
    return {
        "row_count": len(rows),
        "by_asset_type": dict(sorted(by_type.items())),
        "by_action": dict(sorted(by_action.items())),
        "by_harness_action": {harness: dict(counter) for harness, counter in sorted(by_harness.items())},
        "skills": skill_summary,
    }


def build_manifest() -> dict[str, Any]:
    skill_rows, skill_summary = _skill_rows()
    plugin_rows = _plugin_rows()
    rows = sorted(
        (_with_reconciliation_defaults(row) for row in [*skill_rows, *plugin_rows]),
        key=lambda item: (item["asset_type"], item["harness"], item["name"]),
    )
    return _sanitize({
        "version": 1,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generated_by": "scripts/generate_harness_reconciliation.py",
        "scope": {
            "repo_root": "${REPO_ROOT}",
            "home": "~",
            "live_mutation_policy": "No live installs, cache deletion, or home sync were performed by this generator.",
        },
        "terminal_actions": sorted(TERMINAL_ACTIONS),
        "task_graph": _task_graph(rows),
        "summary": _summary(rows, skill_summary),
        "matrix": rows,
    })


def main() -> None:
    manifest = build_manifest()
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if str(HOME) in text or str(ROOT) in text:
        raise SystemExit("Refusing to write manifest with unredacted local absolute paths.")
    OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {_redact(str(OUT))}")


if __name__ == "__main__":
    main()
