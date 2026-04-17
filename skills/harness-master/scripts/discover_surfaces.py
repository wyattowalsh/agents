#!/usr/bin/env python3
"""Discover harness config surfaces for project/global review.

Outputs structured JSON to stdout. Diagnostics go to stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


def _warn(message: str) -> None:
    print(f"[discover_surfaces] {message}", file=sys.stderr)


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(path))


@dataclass
class Surface:
    harness: str
    level: str
    label: str
    path: str | None
    kind: str
    role: str
    status: str
    management_mode: str | None
    notes: str | None
    matched_paths: list[str]


PROJECT_SURFACES: dict[str, list[dict[str, str]]] = {
    "claude-code": [
        {"label": "shared instructions", "path": "AGENTS.md", "kind": "instructions", "role": "secondary"},
        {"label": "claude entrypoint", "path": "CLAUDE.md", "kind": "instructions", "role": "authoritative"},
        {"label": "claude rules", "path": ".claude/rules/*.md", "kind": "rules", "role": "secondary"},
        {"label": "project settings", "path": ".claude/settings.json", "kind": "config", "role": "authoritative"},
        {
            "label": "project local settings",
            "path": ".claude/settings.local.json",
            "kind": "config",
            "role": "secondary",
        },
    ],
    "codex": [
        {"label": "shared instructions", "path": "AGENTS.md", "kind": "instructions", "role": "authoritative"},
        {"label": "project config", "path": ".codex/config.toml", "kind": "config", "role": "authoritative"},
    ],
    "cursor": [
        {"label": "root agents", "path": "AGENTS.md", "kind": "instructions", "role": "secondary"},
        {"label": "nested agents", "path": "**/AGENTS.md", "kind": "instructions", "role": "secondary"},
        {"label": "cursor rules", "path": ".cursor/rules/*", "kind": "rules", "role": "authoritative"},
        {"label": "project mcp", "path": ".cursor/mcp.json", "kind": "mcp", "role": "authoritative"},
    ],
    "gemini-cli": [
        {"label": "shared instructions", "path": "AGENTS.md", "kind": "instructions", "role": "secondary"},
        {"label": "gemini entrypoint", "path": "GEMINI.md", "kind": "instructions", "role": "authoritative"},
        {"label": "project settings", "path": ".gemini/settings.json", "kind": "config", "role": "authoritative"},
    ],
    "antigravity": [
        {"label": "repo wrapper instructions", "path": "AGENTS.md", "kind": "instructions", "role": "repo-observed"},
        {"label": "repo wrapper entrypoint", "path": "GEMINI.md", "kind": "instructions", "role": "repo-observed"},
    ],
    "github-copilot": [
        {"label": "shared instructions", "path": "AGENTS.md", "kind": "instructions", "role": "secondary"},
        {
            "label": "copilot instructions",
            "path": ".github/copilot-instructions.md",
            "kind": "instructions",
            "role": "authoritative",
        },
        {
            "label": "copilot generated instructions",
            "path": ".github/instructions/*",
            "kind": "instructions",
            "role": "secondary",
        },
        {"label": "copilot hooks", "path": ".github/hooks/*", "kind": "hooks", "role": "secondary"},
        {"label": "project mcp", "path": ".vscode/mcp.json", "kind": "mcp", "role": "authoritative"},
        {"label": "project agents", "path": "platforms/copilot/agents/*", "kind": "agents", "role": "secondary"},
    ],
    "opencode": [
        {"label": "shared instructions", "path": "AGENTS.md", "kind": "instructions", "role": "authoritative"},
        {"label": "opencode config", "path": "opencode.json", "kind": "config", "role": "authoritative"},
        {"label": "opencode agents", "path": ".opencode/agents/*", "kind": "agents", "role": "secondary"},
        {
            "label": "opencode companion config",
            "path": ".opencode/ocx.jsonc",
            "kind": "config",
            "role": "repo-observed",
        },
    ],
}


GLOBAL_SURFACES: dict[str, list[dict[str, str]]] = {
    "claude-code": [
        {"label": "global entrypoint", "path": "~/.claude/CLAUDE.md", "kind": "instructions", "role": "authoritative"},
        {"label": "global settings", "path": "~/.claude/settings.json", "kind": "config", "role": "authoritative"},
        {
            "label": "global local settings",
            "path": "~/.claude/settings.local.json",
            "kind": "config",
            "role": "secondary",
        },
        {
            "label": "desktop config",
            "path": "~/Library/Application Support/Claude/claude_desktop_config.json",
            "kind": "mcp",
            "role": "secondary",
        },
    ],
    "codex": [
        {"label": "global entrypoint", "path": "~/.codex/AGENTS.md", "kind": "instructions", "role": "authoritative"},
        {"label": "global config", "path": "~/.codex/config.toml", "kind": "config", "role": "authoritative"},
        {"label": "installed skills", "path": "~/.codex/skills", "kind": "skills", "role": "secondary"},
    ],
    "cursor": [
        {"label": "global mcp", "path": "~/.cursor/mcp.json", "kind": "mcp", "role": "authoritative"},
        {"label": "permissions", "path": "~/.cursor/permissions.json", "kind": "permissions", "role": "authoritative"},
    ],
    "gemini-cli": [
        {"label": "global entrypoint", "path": "~/.gemini/GEMINI.md", "kind": "instructions", "role": "authoritative"},
        {"label": "global settings", "path": "~/.gemini/settings.json", "kind": "config", "role": "authoritative"},
        {"label": "installed skills", "path": "~/.gemini/skills", "kind": "skills", "role": "secondary"},
    ],
    "antigravity": [
        {
            "label": "antigravity mcp config",
            "path": "~/.gemini/antigravity/mcp_config.json",
            "kind": "mcp",
            "role": "authoritative",
        },
        {
            "label": "extension antigravity mcp config",
            "path": "~/.gemini/extensions/outline-driven-development/antigravity/mcp_config.json",
            "kind": "mcp",
            "role": "secondary",
        },
    ],
    "github-copilot": [
        {
            "label": "global entrypoint",
            "path": "~/.copilot/copilot-instructions.md",
            "kind": "instructions",
            "role": "authoritative",
        },
        {"label": "global config", "path": "~/.copilot/config.json", "kind": "config", "role": "authoritative"},
        {"label": "global mcp", "path": "~/.copilot/mcp-config.json", "kind": "mcp", "role": "authoritative"},
        {"label": "alt global mcp", "path": "~/.config/.copilot/mcp-config.json", "kind": "mcp", "role": "secondary"},
        {"label": "global agents", "path": "~/.copilot/agents", "kind": "agents", "role": "secondary"},
    ],
    "opencode": [
        {
            "label": "global opencode config",
            "path": "~/.config/opencode/opencode.json",
            "kind": "config",
            "role": "authoritative",
        },
        {
            "label": "global opencode agents",
            "path": "~/.config/opencode/AGENTS.md",
            "kind": "instructions",
            "role": "secondary",
        },
        {
            "label": "global opencode skills",
            "path": "~/.config/opencode/skills",
            "kind": "skills",
            "role": "secondary",
        },
    ],
}


BLIND_SPOTS: dict[str, list[tuple[str, str, str]]] = {
    "cursor": [
        ("global", "Cursor user rules in settings UI", "User rules may exist only in the UI unless exported."),
        ("global", "Cursor team rules/dashboard", "Team-managed rules are not observable from local files by default."),
    ],
    "antigravity": [
        (
            "project",
            "Native Antigravity project config",
            "Project-level native Antigravity files are not strongly verified from first-party docs here.",
        ),
        (
            "global",
            "Antigravity settings UI",
            "Settings and approval policies may live in the UI and not map to local files.",
        ),
        (
            "global",
            "Antigravity agent mode settings",
            "Agent mode policies are documented but may not be file-backed locally.",
        ),
    ],
    "opencode": [
        (
            "global",
            "Global OpenCode rules",
            "Rules may affect OpenCode behavior, but a stable first-party global rules path is not verified in this plan.",
        ),
    ],
}


def _load_manifest(repo_root: Path) -> list[dict[str, Any]]:
    manifest_path = repo_root / "config" / "sync-manifest.json"
    if not manifest_path.is_file():
        return []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive parsing
        _warn(f"Failed to parse sync manifest: {exc}")
        return []
    managed = payload.get("managed", [])
    if not isinstance(managed, list):
        return []
    return [item for item in managed if isinstance(item, dict)]


def _management_mode(candidate: Path, manifest_entries: list[dict[str, Any]]) -> str | None:
    candidate_str = str(candidate)
    for item in manifest_entries:
        path_value = item.get("path")
        mode_value = item.get("mode")
        if not isinstance(path_value, str) or not isinstance(mode_value, str):
            continue
        if candidate_str == path_value:
            return mode_value
        if candidate_str.startswith(path_value.rstrip("/") + os.sep):
            return mode_value
    return None


def _project_matches(repo_root: Path, pattern: str) -> list[Path]:
    if any(ch in pattern for ch in "*?["):
        matches = sorted(repo_root.glob(pattern))
        if pattern == "**/AGENTS.md":
            root_agents = repo_root / "AGENTS.md"
            matches = [match for match in matches if match != root_agents]
        return matches
    candidate = repo_root / pattern
    return [candidate] if candidate.exists() else []


def _emit_surface(
    harness: str,
    level: str,
    spec: dict[str, str],
    repo_root: Path,
    manifest_entries: list[dict[str, Any]],
) -> Surface:
    pattern = spec["path"]
    if level == "project":
        matches = _project_matches(repo_root, pattern)
    else:
        candidate = _expand(pattern)
        matches = [candidate] if candidate.exists() else []

    if matches:
        management_modes = {
            _management_mode(match, manifest_entries) for match in matches if _management_mode(match, manifest_entries)
        }
        management_mode = sorted(management_modes)[0] if management_modes else None
        return Surface(
            harness=harness,
            level=level,
            label=spec["label"],
            path=pattern,
            kind=spec["kind"],
            role=spec["role"],
            status="present",
            management_mode=management_mode,
            notes=None,
            matched_paths=[str(match) for match in matches],
        )

    return Surface(
        harness=harness,
        level=level,
        label=spec["label"],
        path=pattern,
        kind=spec["kind"],
        role=spec["role"],
        status="missing",
        management_mode=None,
        notes=None,
        matched_paths=[],
    )


def _blind_spot_surfaces(harness: str, level: str) -> list[Surface]:
    surfaces: list[Surface] = []
    for spot_level, label, notes in BLIND_SPOTS.get(harness, []):
        if level not in {"both", spot_level}:
            continue
        surfaces.append(
            Surface(
                harness=harness,
                level=spot_level,
                label=label,
                path=None,
                kind="blind-spot",
                role="blind-spot",
                status="blind-spot",
                management_mode=None,
                notes=notes,
                matched_paths=[],
            )
        )
    return surfaces


def discover(repo_root: Path, harnesses: list[str], level: str) -> dict[str, Any]:
    manifest_entries = _load_manifest(repo_root)
    results: list[Surface] = []
    levels = ["project", "global"] if level == "both" else [level]

    for harness in harnesses:
        for active_level in levels:
            specs = PROJECT_SURFACES[harness] if active_level == "project" else GLOBAL_SURFACES[harness]
            for spec in specs:
                results.append(_emit_surface(harness, active_level, spec, repo_root, manifest_entries))
        results.extend(_blind_spot_surfaces(harness, level))

    summary = {
        "present": sum(1 for item in results if item.status == "present"),
        "missing": sum(1 for item in results if item.status == "missing"),
        "blind_spot": sum(1 for item in results if item.status == "blind-spot"),
        "generated": sum(1 for item in results if item.management_mode == "generated"),
        "merged": sum(1 for item in results if item.management_mode == "merged"),
        "symlink": sum(1 for item in results if item.management_mode == "symlink"),
        "symlinked_entries": sum(1 for item in results if item.management_mode == "symlinked-entries"),
    }
    return {
        "repo_root": str(repo_root),
        "harnesses": harnesses,
        "level": level,
        "surfaces": [asdict(item) for item in results],
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover harness config surfaces.")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect.")
    parser.add_argument(
        "--harness",
        action="append",
        dest="harnesses",
        required=True,
        choices=sorted(PROJECT_SURFACES),
        help="Canonical harness name. Repeat for multiple harnesses.",
    )
    parser.add_argument("--level", required=True, choices=["project", "global", "both"], help="Review level.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        _warn(f"Repo root does not exist: {repo_root}")
        return 2

    payload = discover(repo_root, args.harnesses, args.level)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
