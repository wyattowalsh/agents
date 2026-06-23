#!/usr/bin/env python3
"""Plan read-only ecosystem source access for harness-master research."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "data" / "research-sources.json"


def _load_registry() -> dict[str, Any]:
    with SOURCES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _format_template(template: str, *, query: str, candidate: str, harness: str, category: str) -> str:
    http_template = template.lstrip().startswith(("http://", "https://", "POST http://", "POST https://"))
    query_value = urllib.parse.quote(query, safe="") if http_template else query
    candidate_encoded = urllib.parse.quote(candidate, safe="")
    safe_values = {
        "query": query_value,
        "candidate": candidate,
        "candidate_encoded": candidate_encoded,
        "harness": harness,
        "category": category,
        "source": candidate,
        "year": "2026",
        "docs_url": candidate or "https://example.com/docs",
        "domain": candidate.replace("https://", "").replace("http://", "").split("/")[0] or "example.com",
        "owner": "OWNER",
        "repo": "REPO",
        "namespace": "NAMESPACE",
        "repository": "REPOSITORY",
        "extension": "EXTENSION",
    }
    try:
        return template.format(**safe_values)
    except KeyError:
        return template


def _render_templates(source: dict[str, Any], *, query: str, candidate: str, harness: str) -> list[str]:
    rendered: list[str] = []
    category = str(source.get("category", "all"))
    templates = source.get("query_templates", {})
    values = templates.values() if isinstance(templates, dict) else _as_list(templates)
    for value in values:
        for template in _as_list(value):
            if isinstance(template, str):
                if not candidate and (f"{candidate}" in template or f"{source}" in template):
                    continue
                rendered.append(
                    _format_template(
                        template,
                        query=query,
                        candidate=candidate,
                        harness=harness,
                        category=category,
                    )
                )
    if not rendered and isinstance(source.get("base_url_or_command"), str):
        rendered.append(
            _format_template(
                source["base_url_or_command"],
                query=query,
                candidate=candidate,
                harness=harness,
                category=category,
            )
        )
    return rendered


def _source_status(source: dict[str, Any]) -> tuple[str, list[str]]:
    missing = [name for name in source.get("auth_env", []) if not os.environ.get(name)]
    if missing:
        return "missing-env", missing
    return "ready", []


def _filter_sources(sources: list[dict[str, Any]], category: str | None) -> list[dict[str, Any]]:
    if not category or category == "all":
        return sources
    return [source for source in sources if source.get("category") == category]


def _build_plan(source: dict[str, Any], *, query: str, candidate: str, harness: str) -> dict[str, Any]:
    status, missing_env = _source_status(source)
    rendered = _render_templates(source, query=query, candidate=candidate, harness=harness)
    return {
        "id": source["id"],
        "category": source.get("category"),
        "authority_tier": source.get("authority_tier"),
        "access_method": source.get("access_method"),
        "base_url_or_command": source.get("base_url_or_command"),
        "auth_env": source.get("auth_env", []),
        "missing_env": missing_env,
        "status": status,
        "dry_run": {
            "planned_access": rendered,
            "required_env": source.get("auth_env", []),
            "expected_evidence_fields": source.get("evidence_fields", []),
        },
        "rate_limit_notes": source.get("rate_limit_notes"),
        "confidence_role": source.get("confidence_role"),
        "failure_mode": source.get("failure_mode"),
    }


def _execute_http_get(plan: dict[str, Any]) -> dict[str, Any]:
    access = plan["dry_run"]["planned_access"]
    url = next((item for item in access if isinstance(item, str) and item.startswith("http")), None)
    if not url:
        return {"executed": False, "reason": "No HTTP URL was available for low-risk execution."}
    request = urllib.request.Request(url, headers={"User-Agent": "harness-master-source-probe/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read(1024)
            return {
                "executed": True,
                "url": url,
                "status": response.status,
                "content_type": response.headers.get("content-type"),
                "sample_bytes": len(body),
            }
    except urllib.error.URLError as exc:
        return {"executed": False, "url": url, "error": str(exc)}


def _print_text(payload: dict[str, Any]) -> None:
    if "sources" in payload:
        for source in payload["sources"]:
            print(f"{source['id']} [{source.get('category')}] {source.get('access_method')}")
        return
    for plan in payload["plans"]:
        print(f"Source: {plan['id']}")
        print(f"Status: {plan['status']}")
        if plan["missing_env"]:
            print(f"Missing env: {', '.join(plan['missing_env'])}")
        print("Planned access:")
        for item in plan["dry_run"]["planned_access"]:
            print(f"- {item}")
        print("Evidence fields:")
        for item in plan["dry_run"]["expected_evidence_fields"]:
            print(f"- {item}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-sources", action="store_true", help="List configured source IDs.")
    parser.add_argument("--source", action="append", help="Source ID to probe. May be repeated.")
    parser.add_argument("--query", default="", help="Search text for source templates.")
    parser.add_argument("--candidate", default="", help="Candidate URL, package, repo, or source string.")
    parser.add_argument("--harness", default="all", help="Target harness ID or all.")
    parser.add_argument("--category", help="Optional source category filter, such as mcp, skill, package, or security.")
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="Print planned access. This is the default."
    )
    parser.add_argument("--execute", action="store_true", help="Execute low-risk read-only HTTP probes.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)

    registry = _load_registry()
    sources = registry.get("sources", [])
    by_id = {source["id"]: source for source in sources}

    if args.list_sources:
        payload = {
            "schema_version": registry.get("schema_version"),
            "category": args.category or "all",
            "sources": _filter_sources(sources, args.category),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_text(payload)
        return 0

    selected_ids = args.source or list(by_id)
    if args.category and not args.source:
        selected_ids = [source["id"] for source in _filter_sources(sources, args.category)]
    unknown = [source_id for source_id in selected_ids if source_id not in by_id]
    if unknown:
        print(f"Unknown source id(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    plans = [
        _build_plan(
            by_id[source_id],
            query=args.query,
            candidate=args.candidate,
            harness=args.harness,
        )
        for source_id in selected_ids
    ]
    if args.execute:
        for plan in plans:
            if plan["status"] == "missing-env":
                plan["execution"] = {"executed": False, "reason": "Missing required environment variables."}
            elif plan["access_method"] in {"http-api", "http-fetch", "openapi"}:
                plan["execution"] = _execute_http_get(plan)
            else:
                plan["execution"] = {
                    "executed": False,
                    "reason": "Execution is not enabled for command, local-file, GraphQL, or web-search sources.",
                }

    payload = {
        "harness": args.harness,
        "query": args.query,
        "candidate": args.candidate,
        "dry_run": not args.execute,
        "plans": plans,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
