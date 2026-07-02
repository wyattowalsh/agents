#!/usr/bin/env python3
"""Enrich portable skill package manifests with repo metadata."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_eval_count(skill_dir: Path) -> int:
    evals_file = skill_dir / "evals" / "evals.json"
    if not evals_file.is_file():
        return 0
    try:
        data = json.loads(evals_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    evals = data.get("evals")
    return len(evals) if isinstance(evals, list) else 0


def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta


def enrich_manifest(skill_dir: Path, *, apply: bool) -> dict[str, object]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {"ok": False, "error": "missing SKILL.md"}
    frontmatter = _parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    base = {
        "name": frontmatter.get("name", skill_dir.name),
        "description": frontmatter.get("description", "").strip("> \n"),
        "compatibility_notes": frontmatter.get("compatibility", ""),
        "eval_case_count": _load_eval_count(skill_dir),
        "harness_targets": ["claude-code", "cursor", "codex", "github-copilot", "opencode", "gemini-cli", "grok"],
    }
    if apply:
        base["packaged_at"] = datetime.now(UTC).isoformat()
    out = skill_dir / "manifest.enriched.json"
    if apply:
        out.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "path": str(out), "manifest": base, "applied": apply}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Enrich skill package manifest")
    parser.add_argument("name")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    skill_dir = REPO_ROOT / "skills" / args.name
    payload = enrich_manifest(skill_dir, apply=args.apply and not args.dry_run)
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
