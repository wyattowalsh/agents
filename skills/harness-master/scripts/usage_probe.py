#!/usr/bin/env python3
"""Collect safe aggregate usage-review signals for harness-master."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import discover_surfaces


SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "credentials.json",
    "auth.json",
    "secrets.toml",
}


OPENCODE_LOCAL_SOURCES = [
    "opencode.json",
    ".opencode/PLUGINS.md",
    "config/opencode-token-monitor.json",
    "config/opencode-quota-toast.json",
    "config/plugin-extension-registry.json",
    "config/harness-surface-registry.json",
    "instructions/opencode-global.md",
]


ENV_PRESENCE_KEYS = [
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_BASEURL",
    "WAKATIME_HOME",
    "OPENCODE_TERMINAL_PROGRESS",
]


@dataclass
class UsageSource:
    id: str
    harness: str
    level: str
    privacy_class: str
    access_method: str
    status: str
    blocked_reason: str | None = None


@dataclass
class UsageSignal:
    category: str
    source_id: str
    privacy_class: str
    harness: str
    level: str
    window_days: int
    summary: str
    confidence: str


def _top_level_json_keys(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    if isinstance(payload, dict):
        return sorted(str(key) for key in payload)
    return []


def _safe_file_metadata(repo_root: Path, relative_path: str) -> dict[str, Any]:
    path = repo_root / relative_path
    exists = path.exists()
    metadata: dict[str, Any] = {
        "path": relative_path,
        "exists": exists,
        "privacy_class": "metadata-safe",
    }
    if not exists:
        return metadata
    if path.name in SENSITIVE_NAMES or path.suffix in {".key", ".pem", ".p12", ".pfx"}:
        return {
            "path": relative_path,
            "exists": True,
            "privacy_class": "secret-file",
            "blocked_reason": "Sensitive file names and key material are not read by usage_probe.",
        }
    try:
        stat = path.stat()
    except OSError as exc:
        metadata["status"] = f"stat-error: {exc}"
        return metadata
    metadata.update(
        {
            "size_bytes": stat.st_size,
            "json_top_level_keys": _top_level_json_keys(path) if path.suffix == ".json" else [],
        }
    )
    return metadata


def _opencode_plugin_names(repo_root: Path) -> list[str]:
    path = repo_root / "opencode.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    plugins = payload.get("plugin", []) if isinstance(payload, dict) else []
    if not isinstance(plugins, list):
        return []
    names: list[str] = []
    for item in plugins:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict) and isinstance(item.get("npm"), str):
            names.append(item["npm"])
    return sorted(names)


def _planned_commands(harnesses: list[str], days: int) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    if "opencode" in harnesses:
        commands.extend(
            [
                {
                    "id": "opencode-stats",
                    "command_shape": "opencode stats",
                    "privacy_class": "aggregate-safe",
                    "execution": "planned-only",
                },
                {
                    "id": "opencode-session-list",
                    "command_shape": "opencode session list",
                    "privacy_class": "metadata-safe",
                    "execution": "planned-only",
                },
                {
                    "id": "opencode-export-sanitize",
                    "command_shape": "opencode export --sanitize",
                    "privacy_class": "sanitized-export",
                    "execution": "planned-only",
                },
                {
                    "id": "opencode-db-path",
                    "command_shape": "opencode db path",
                    "privacy_class": "metadata-safe",
                    "execution": "planned-only",
                },
            ]
        )
    commands.append(
        {
            "id": "token-history",
            "command_shape": f"token_history(from=<now-{days}d>, to=<now>, scope=session)",
            "privacy_class": "aggregate-safe",
            "execution": "runtime-tool-if-requested",
        }
    )
    return commands


def _usage_sources(harnesses: list[str], level: str) -> list[UsageSource]:
    sources = [
        UsageSource(
            id="surface-discovery",
            harness="all" if len(harnesses) > 1 else harnesses[0],
            level=level,
            privacy_class="metadata-safe",
            access_method="local-file-metadata",
            status="ready",
        ),
        UsageSource(
            id="runtime-token-tools",
            harness="all" if len(harnesses) > 1 else harnesses[0],
            level=level,
            privacy_class="aggregate-safe",
            access_method="runtime-tool-summary",
            status="planned",
        ),
    ]
    if "opencode" in harnesses:
        sources.append(
            UsageSource(
                id="opencode-local-metadata",
                harness="opencode",
                level=level,
                privacy_class="metadata-safe",
                access_method="top-level-config-metadata",
                status="ready",
            )
        )
    return sources


def _usage_signals(harnesses: list[str], level: str, days: int, metadata: list[dict[str, Any]]) -> list[UsageSignal]:
    signals = [
        UsageSignal(
            category="observability-gap",
            source_id="runtime-token-tools",
            privacy_class="aggregate-safe",
            harness="all" if len(harnesses) > 1 else harnesses[0],
            level=level,
            window_days=days,
            summary="Runtime aggregate tools are recommended for actual token and cost totals; this probe reports only safe local metadata.",
            confidence="medium",
        )
    ]
    if "opencode" in harnesses:
        existing = [item["path"] for item in metadata if item.get("exists")]
        signals.append(
            UsageSignal(
                category="plugin-usage",
                source_id="opencode-local-metadata",
                privacy_class="metadata-safe",
                harness="opencode",
                level=level,
                window_days=days,
                summary=f"Observed {len(existing)} OpenCode metadata source(s); use runtime summaries to distinguish configured plugins from actual usage.",
                confidence="medium",
            )
        )
    return signals


def probe(repo_root: Path, harnesses: list[str], level: str, days: int) -> dict[str, Any]:
    surfaces = discover_surfaces.discover(repo_root, harnesses, level)
    opencode_metadata = []
    if "opencode" in harnesses:
        opencode_metadata = [_safe_file_metadata(repo_root, path) for path in OPENCODE_LOCAL_SOURCES]

    payload = {
        "schema_version": "1.0",
        "repo_root": str(repo_root),
        "harnesses": harnesses,
        "level": level,
        "window_days": days,
        "privacy_boundary": {
            "collected": ["aggregate-safe", "metadata-safe", "credential-presence"],
            "blocked": ["raw-sensitive", "secret-file"],
            "notes": "This helper does not read raw session bodies, raw prompts, raw traces, database message rows, or secret files.",
        },
        "tools_available": {
            "opencode": bool(shutil.which("opencode")),
            "uv": bool(shutil.which("uv")),
        },
        "env_presence": {key: bool(os.environ.get(key)) for key in ENV_PRESENCE_KEYS},
        "surface_summary": surfaces.get("summary", {}),
        "opencode_metadata": opencode_metadata,
        "opencode_plugins": _opencode_plugin_names(repo_root) if "opencode" in harnesses else [],
        "planned_safe_commands": _planned_commands(harnesses, days),
    }
    payload["usage_sources"] = [asdict(item) for item in _usage_sources(harnesses, level)]
    payload["usage_signals"] = [asdict(item) for item in _usage_signals(harnesses, level, days, opencode_metadata)]
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect.")
    parser.add_argument(
        "--harness",
        action="append",
        dest="harnesses",
        required=True,
        choices=sorted({*discover_surfaces.PROJECT_SURFACES, *discover_surfaces.GLOBAL_SURFACES}),
        help="Canonical harness name. Repeat for multiple harnesses.",
    )
    parser.add_argument("--level", required=True, choices=["project", "global", "both"], help="Review level.")
    parser.add_argument("--days", type=int, default=14, help="Usage window in days for planned aggregate tools.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)

    if args.days < 1:
        parser.error("--days must be a positive integer")

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        parser.error(f"Repo root does not exist: {repo_root}")

    payload = probe(repo_root, args.harnesses, args.level, args.days)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"harnesses: {', '.join(args.harnesses)}")
        print(f"level: {args.level}")
        print(f"window_days: {args.days}")
        print(f"usage_sources: {len(payload['usage_sources'])}")
        print(f"usage_signals: {len(payload['usage_signals'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
