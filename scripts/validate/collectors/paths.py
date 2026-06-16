"""Collect portable-path violations in tracked repo surfaces."""

from __future__ import annotations

import importlib.util
from pathlib import Path

TRACKED_GLOBS = [
    "config/mcp-registry.json",
    "config/sync-manifest.json",
    "config/tooling-policy.json",
    "instructions/*.md",
    "CLAUDE.md",
    "AGENTS.md",
    "GEMINI.md",
]
ALLOW_SUFFIXES = (".example", ".mcphub.example")
SKIP_PARTS = {"audit", "probes", "openspec/changes/oss-friendly-codebase-standardization/audit"}


def _load_contains():
    spec = importlib.util.spec_from_file_location(
        "repo_paths", Path(__file__).resolve().parents[3] / "wagents/repo_paths.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.contains_maintainer_absolute_path


def collect_path_portability_errors(repo_root: Path) -> list[dict[str, str]]:
    contains = _load_contains()
    errors: list[dict[str, str]] = []
    for pattern in TRACKED_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_root).as_posix()
            if any(part in rel for part in SKIP_PARTS):
                continue
            if rel.endswith(ALLOW_SUFFIXES):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if contains(text):
                errors.append({
                    "source": rel,
                    "message": "Maintainer-specific absolute path leak (/Users/<user>/)",
                })
    return errors

