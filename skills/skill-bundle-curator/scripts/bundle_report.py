#!/usr/bin/env python3
"""Summarize agent-bundle.json component inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


def _count_skills() -> int:
    skills_dir = REPO_ROOT / "skills"
    if not skills_dir.is_dir():
        return 0
    return sum(1 for path in skills_dir.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())


def _count_agents() -> int:
    agents_dir = REPO_ROOT / "agents"
    if not agents_dir.is_dir():
        return 0
    return sum(
        1
        for path in agents_dir.glob("*.md")
        if path.name != "README.md" and path.is_file()
    )


def _count_mcp() -> int:
    mcp_dir = REPO_ROOT / "mcp"
    if not mcp_dir.is_dir():
        return 0
    return sum(
        1
        for path in mcp_dir.iterdir()
        if path.is_dir() and (path / "server.py").is_file() and path.name != "servers"
    )


def build_report(mode: str = "summary") -> dict[str, Any]:
    bundle_path = REPO_ROOT / "agent-bundle.json"
    if not bundle_path.is_file():
        return {"ok": False, "error": "missing agent-bundle.json"}

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    components = bundle.get("components", {})
    adapters = bundle.get("adapters", {})

    if mode == "adapters":
        return {"ok": True, "adapters": adapters}

    return {
        "ok": True,
        "bundle_name": bundle.get("name"),
        "schema_version": bundle.get("schemaVersion"),
        "components": components,
        "counts": {
            "skills": _count_skills(),
            "agents": _count_agents(),
            "mcp_servers": _count_mcp(),
        },
        "adapter_ids": sorted(adapters.keys()) if isinstance(adapters, dict) else [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bundle composition report")
    parser.add_argument("mode", nargs="?", default="summary", choices=("summary", "adapters"))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    payload = build_report(args.mode)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    elif not payload.get("ok"):
        print(payload.get("error", "error"))
    elif args.mode == "adapters":
        for adapter_id, meta in payload.get("adapters", {}).items():
            install = meta.get("install") if isinstance(meta, dict) else None
            print(f"{adapter_id}: {install or '(no install string)'}")
    else:
        counts = payload.get("counts", {})
        print(f"bundle={payload.get('bundle_name')} skills={counts.get('skills')} agents={counts.get('agents')} mcp={counts.get('mcp_servers')}")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
