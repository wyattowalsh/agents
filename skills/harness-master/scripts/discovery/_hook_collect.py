#!/usr/bin/env python3
"""Private stdlib-only collectors for hook discovery (no repo CLI imports)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HARNESS_ALIASES: dict[str, str] = {
    "copilot": "github-copilot",
    "github-copilot-web": "github-copilot",
    "github-copilot-cli": "github-copilot",
    "claude": "claude-code",
    "claude-desktop": "claude-code",
    "gemini": "gemini-cli",
    "cursor": "cursor-editor",
    "cursor-editor": "cursor-editor",
    "cursor-agent-web": "cursor-editor",
    "cursor-agent-cli": "cursor-editor",
    "antigravity": "antigravity",
    "opencode": "opencode",
    "chatgpt": "chatgpt",
}


def _normalize_harness(h: str) -> str:
    return HARNESS_ALIASES.get(h, h)


def _extract_frontmatter_block(text: str) -> str:
    """Return the YAML frontmatter content between first --- markers, or ''."""
    if not text.lstrip().startswith("---"):
        return ""
    # split on top-level --- lines
    parts = re.split(r"^\s*---\s*$", text, maxsplit=2, flags=re.MULTILINE)
    if len(parts) >= 2:
        return parts[1].strip()
    # fallback for no closing
    m = re.search(r"^---\s*$", text[3:], flags=re.MULTILINE)
    if m:
        return text[3 : 3 + m.start()].strip()
    return text[3:].strip()


def _has_hooks_key(fm_block: str) -> bool:
    if not fm_block:
        return False
    return bool(re.search(r"^\s*hooks\s*:", fm_block, flags=re.MULTILINE))


def collect_registry_summary(repo_root: Path) -> dict[str, Any]:
    """Parse config/hook-registry.json into grouped views + managed hook-runner count."""
    path = repo_root / "config" / "hook-registry.json"
    if not path.is_file():
        return {
            "by_harness": {},
            "by_logical_event": {},
            "managed_wagents_hook_count": 0,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "by_harness": {},
            "by_logical_event": {},
            "managed_wagents_hook_count": 0,
        }

    hooks = data.get("hooks", []) if isinstance(data, dict) else []
    by_harness: dict[str, list[str]] = {}
    by_logical_event: dict[str, list[str]] = {}
    wagents_count = 0

    for entry in hooks:
        if not isinstance(entry, dict):
            continue
        hid = str(entry.get("id") or "")
        event = str(entry.get("logical_event") or "unknown")
        cmd = str(entry.get("command") or "")
        harness_list = entry.get("harnesses") or []

        if "wagents-hook.py" in cmd or "{repo_root}/hooks/wagents-hook.py" in cmd:
            wagents_count += 1

        for raw_h in harness_list if isinstance(harness_list, (list, tuple)) else []:
            canon = _normalize_harness(str(raw_h))
            by_harness.setdefault(canon, []).append(hid)
            by_logical_event.setdefault(event, []).append(hid)

    # dedup + sort lists for stability
    for d in (by_harness, by_logical_event):
        for k in list(d.keys()):
            d[k] = sorted(set(x for x in d[k] if x))

    return {
        "by_harness": {k: by_harness[k] for k in sorted(by_harness)},
        "by_logical_event": {k: by_logical_event[k] for k in sorted(by_logical_event)},
        "managed_wagents_hook_count": wagents_count,
    }


def collect_embedded_settings(repo_root: Path) -> dict[str, Any]:
    """Detect presence of hooks in .claude/*settings*.json and .gemini/settings.json."""
    claude = False
    paths: list[str] = []
    for name in ("settings.json", "settings.local.json"):
        p = repo_root / ".claude" / name
        if p.is_file():
            rel = str(p.relative_to(repo_root))
            paths.append(rel)
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                hooks = data.get("hooks") if isinstance(data, dict) else None
                if isinstance(hooks, dict) and hooks:
                    claude = True
            except (json.JSONDecodeError, OSError):
                pass

    gemini = False
    gp = repo_root / ".gemini" / "settings.json"
    if gp.is_file():
        rel = str(gp.relative_to(repo_root))
        paths.append(rel)
        try:
            gdata = json.loads(gp.read_text(encoding="utf-8"))
            ghooks = gdata.get("hooks") if isinstance(gdata, dict) else None
            if isinstance(ghooks, dict) and ghooks:
                gemini = True
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "claude": claude,
        "gemini": gemini,
        "paths": sorted(set(paths)),
    }


def collect_frontmatter_hooks(repo_root: Path) -> dict[str, Any]:
    """Lightweight scan of skills/*/SKILL.md and agents/*.md for hooks: frontmatter (--- delimited)."""
    skills_with = 0
    agents_with = 0
    sources: list[str] = []

    skills_dir = repo_root / "skills"
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            if child.is_dir():
                f = child / "SKILL.md"
                if f.is_file():
                    try:
                        txt = f.read_text(encoding="utf-8")
                        fm = _extract_frontmatter_block(txt)
                        if _has_hooks_key(fm):
                            skills_with += 1
                            sources.append(f"skill:{child.name}")
                    except (OSError, UnicodeDecodeError):
                        pass

    agents_dir = repo_root / "agents"
    if agents_dir.is_dir():
        for f in sorted(agents_dir.glob("*.md")):
            try:
                txt = f.read_text(encoding="utf-8")
                fm = _extract_frontmatter_block(txt)
                if _has_hooks_key(fm):
                    agents_with += 1
                    sources.append(f"agent:{f.stem}")
            except (OSError, UnicodeDecodeError):
                pass

    return {
        "skills_with_hooks": skills_with,
        "agents_with_hooks": agents_with,
        "sources": sources,
    }


def collect_grok_managed(repo_root: Path) -> dict[str, Any]:
    """Report presence of Grok/Plannotator managed hook policy file."""
    p = repo_root / "config" / "grok-plannotator-hooks.json"
    if not p.is_file():
        return {"policy_present": False}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        hooks_section = data.get("hooks") if isinstance(data, dict) else None
        present = isinstance(hooks_section, dict) and bool(hooks_section)
        return {"policy_present": present}
    except (json.JSONDecodeError, OSError):
        return {"policy_present": False}


def collect_validation_errors(repo_root: Path) -> list[dict[str, str]]:
    """Run the asset_toolkit hook validator via subprocess (cwd=repo_root) and return its errors list."""
    script = (
        repo_root
        / "skills"
        / "skill-creator"
        / "scripts"
        / "asset_toolkit"
        / "validate_hooks.py"
    )
    if not script.is_file():
        return [{"source": "validate_hooks.py", "message": "validator script missing"}]

    cmd = [sys.executable, str(script), "--format", "json"]
    proc = subprocess.run(
        cmd, cwd=str(repo_root), capture_output=True, text=True, check=False
    )
    stdout = (proc.stdout or "").strip()
    if not stdout:
        return [{"source": "validate_hooks", "message": proc.stderr.strip() or "no output"}]
    try:
        payload = json.loads(stdout)
        if isinstance(payload, dict):
            errs = payload.get("errors", [])
            if isinstance(errs, list):
                return [e for e in errs if isinstance(e, dict)]
        return []
    except json.JSONDecodeError:
        return [{"source": "validate_hooks", "message": "invalid json from validator"}]


def load_hook_surface_registry(repo_root: Path) -> dict[str, Any]:
    """Load optional config/hook-surface-registry.json (project/global blocks of hook surfaces)."""
    p = repo_root / "config" / "hook-surface-registry.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"error": "invalid-json"}
