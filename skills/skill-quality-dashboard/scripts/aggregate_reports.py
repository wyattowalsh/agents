#!/usr/bin/env python3
"""Aggregate maintainer ops report JSON into a dashboard summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = REPO_ROOT / "docs" / "public" / "generated-reports"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _summarize(name: str, data: dict[str, Any]) -> dict[str, Any]:
    if name == "docs-link-check":
        return {"broken_count": data.get("broken_count"), "pages_scanned": data.get("total_pages_scanned")}
    if name == "docs-dependency-drift":
        return {"drift_detected": data.get("drift_detected"), "checked_sources": data.get("checked_sources")}
    if name == "llms-txt-coverage":
        return {"coverage_pct": data.get("coverage_pct"), "missing_description": data.get("missing_description")}
    if name == "maintainer-ops-dashboard":
        return {"report_count": data.get("report_count"), "all_populated": data.get("all_populated")}
    if name == "site-graph-insights":
        return {"node_count": data.get("node_count"), "edge_count": data.get("edge_count")}
    if name == "docs-graph-snapshot":
        latest = data.get("latest") if isinstance(data.get("latest"), dict) else {}
        return {"snapshot_pages": latest.get("page_count"), "history_len": len(data.get("history") or [])}
    return {"keys": sorted(data.keys())[:8]}


def aggregate() -> dict[str, Any]:
    sections: dict[str, Any] = {}
    missing: list[str] = []

    for path in sorted(REPORTS_DIR.glob("*.json")):
        data = _load_json(path)
        if data is None:
            missing.append(path.name)
            continue
        sections[path.stem] = {
            "path": str(path.relative_to(REPO_ROOT)),
            "summary": _summarize(path.stem, data),
        }

    ops = _load_json(REPORTS_DIR / "maintainer-ops-dashboard.json")
    return {
        "ok": len(missing) == 0,
        "reports_dir": str(REPORTS_DIR.relative_to(REPO_ROOT)),
        "section_count": len(sections),
        "missing_or_invalid": missing,
        "sections": sections,
        "ops_all_populated": ops.get("all_populated") if ops else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate maintainer quality reports")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    payload = aggregate()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"reports={payload['section_count']} ok={payload['ok']} ops_populated={payload.get('ops_all_populated')}")
        for name, meta in payload.get("sections", {}).items():
            print(f"  {name}: {meta.get('summary')}")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
