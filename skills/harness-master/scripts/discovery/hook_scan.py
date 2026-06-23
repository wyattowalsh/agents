#!/usr/bin/env python3
"""Scan hook registry, settings, frontmatter, grok policy, and surface parity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure sibling _hook_collect and _paths are importable when script run directly
# (not as package module). Matches test importlib + real CLI invocation patterns.
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from _hook_collect import (
    HARNESS_ALIASES,
    collect_embedded_settings,
    collect_frontmatter_hooks,
    collect_grok_managed,
    collect_registry_summary,
    collect_validation_errors,
    load_hook_surface_registry,
)
from _paths import default_repo_root
from schemas import write_json


def _load_harness_surface_projections(repo_root: Path) -> dict[str, list[str]]:
    """Extract projection_surfaces from harness-surface-registry for hook parity checks."""
    hpath = repo_root / "config" / "harness-surface-registry.json"
    if not hpath.is_file():
        return {}
    try:
        data = json.loads(hpath.read_text(encoding="utf-8"))
        projs: dict[str, list[str]] = {}
        for entry in data.get("harnesses", []) if isinstance(data, dict) else []:
            if isinstance(entry, dict):
                hid = entry.get("id")
                surfs = entry.get("projection_surfaces") or []
                if hid and isinstance(hid, str):
                    projs[str(hid)] = [str(s) for s in surfs if isinstance(s, str)]
        return projs
    except (json.JSONDecodeError, OSError):
        return {}


def scan_hooks(*, repo_root: Path) -> dict[str, Any]:
    registry = collect_registry_summary(repo_root)
    frontmatter = collect_frontmatter_hooks(repo_root)
    embedded = collect_embedded_settings(repo_root)
    grok = collect_grok_managed(repo_root)
    hook_surf = load_hook_surface_registry(repo_root)
    harness_projs = _load_harness_surface_projections(repo_root)

    # Determine harnesses that declare "hooks" in their harness-surface-registry projection
    projected: set[str] = set()
    for hid, surfs in harness_projs.items():
        if any(s.lower() == "hooks" for s in surfs):
            projected.add(hid)

    # Also incorporate any harnesses mentioned in hook-surface-registry (if present)
    if isinstance(hook_surf, dict):
        for level in ("project", "global"):
            level_block = hook_surf.get(level)
            if isinstance(level_block, dict):
                for hid in level_block:
                    if isinstance(hid, str):
                        projected.add(hid)

    reg_harnesses: set[str] = set(registry.get("by_harness", {}).keys())
    # Alias targets count as covered (e.g. github-copilot-cli -> github-copilot).
    for target in HARNESS_ALIASES.values():
        reg_harnesses.add(target)

    missing_in_registry = sorted(h for h in projected if h not in reg_harnesses)

    surface_parity: dict[str, Any] = {
        "harnesses_projecting_hooks": sorted(projected),
        "harnesses_in_registry": sorted(reg_harnesses & projected) or sorted(reg_harnesses),
        "alias_map_used": {k: v for k, v in sorted(HARNESS_ALIASES.items()) if k != v},
    }

    gaps: list[str] = [
        f"harness:{h}:hooks-projected-in-harness-registry-but-missing-from-hook-registry" for h in missing_in_registry
    ]

    # Cross-ref hook-surface-registry for additional gap signals (e.g. declared hook surfaces without registry coverage)
    if isinstance(hook_surf, dict) and not hook_surf.get("error"):
        for level, block in hook_surf.items():
            if level in ("project", "global") and isinstance(block, dict):
                for hid, specs in block.items():
                    if isinstance(hid, str) and isinstance(specs, list) and specs and hid not in reg_harnesses:
                        gaps.append(
                            f"hook-surface:{level}:{hid}:hook-surfaces-declared-but-absent-from-central-hook-registry"
                        )

    validation_errors = collect_validation_errors(repo_root)

    blind_spots = [
        "team-managed-or-enterprise-hooks",
        "ui-only-hook-configuration",
        "global-per-user-hook-files-outside-repo",
        "harness-specific-hook-files-not-centralized-in-registry",
    ]

    return {
        "version": 1,
        "registry": registry,
        "frontmatter": frontmatter,
        "embedded_settings": embedded,
        "grok_managed": grok,
        "surface_parity": surface_parity,
        "gaps": gaps,
        "validation_errors": validation_errors,
        "blind_spots": blind_spots,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan hook registry + surfaces for discovery parity")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root or default_repo_root()
    result = scan_hooks(repo_root=repo_root)

    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
