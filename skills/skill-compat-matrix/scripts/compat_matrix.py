#!/usr/bin/env python3
"""Report portable vs runtime-specific skill compatibility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
PORTABLE_CORE = frozenset({"name", "description", "license", "compatibility", "metadata", "allowed-tools"})
RUNTIME_SPECIFIC = frozenset({
    "user-invocable",
    "disable-model-invocation",
    "context",
    "agent",
    "hooks",
    "paths",
    "model",
    "argument-hint",
})
HARNESS_SUPPORT = {
    "claude-code": {"portable-core", "runtime-specific", "hooks"},
    "cursor": {"portable-core", "runtime-specific"},
    "codex": {"portable-core"},
    "opencode": {"portable-core"},
    "grok": {"portable-core", "runtime-specific"},
}


def _frontmatter_keys(text: str) -> list[str]:
    if not text.startswith("---\n"):
        return []
    end = text.find("\n---\n", 4)
    if end == -1:
        return []
    frontmatter = yaml.safe_load(text[4:end])
    if not isinstance(frontmatter, dict):
        return []
    return [str(key) for key in frontmatter]


def matrix_for_skill(skill_dir: Path) -> dict[str, object]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {"skill": skill_dir.name, "ok": False, "error": "missing SKILL.md"}

    keys = _frontmatter_keys(skill_md.read_text(encoding="utf-8"))
    portable_core = sorted(key for key in keys if key in PORTABLE_CORE)
    runtime_specific = sorted(key for key in keys if key in RUNTIME_SPECIFIC)
    unknown = sorted(key for key in keys if key not in PORTABLE_CORE and key not in RUNTIME_SPECIFIC)

    harness_rows = []
    for harness, supported in sorted(HARNESS_SUPPORT.items()):
        warnings: list[str] = []
        if runtime_specific and "runtime-specific" not in supported:
            warnings.append("runtime-specific frontmatter may be ignored")
        if "hooks" in keys and "hooks" not in supported:
            warnings.append("hooks frontmatter not portable")
        harness_rows.append({
            "harness": harness,
            "status": "supported" if not warnings else "degraded",
            "warnings": warnings,
        })

    return {
        "skill": skill_dir.name,
        "ok": True,
        "portable_core": portable_core,
        "runtime_specific": runtime_specific,
        "unknown_fields": unknown,
        "harnesses": harness_rows,
        "has_scripts": (skill_dir / "scripts").is_dir(),
        "has_evals": (skill_dir / "evals").is_dir(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Skill compatibility matrix")
    parser.add_argument("target", nargs="?", default="")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args(argv)

    skills_root = REPO_ROOT / "skills"
    if args.all or not args.target:
        skill_dirs = sorted(
            path for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
        )
    else:
        skill_dirs = [skills_root / args.target]

    rows = [matrix_for_skill(skill_dir) for skill_dir in skill_dirs]
    payload = {"ok": all(row.get("ok", False) for row in rows), "skills": rows}

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print("\n".join(f"[{row['skill']}]" for row in rows))

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
