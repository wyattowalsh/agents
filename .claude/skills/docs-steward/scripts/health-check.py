#!/usr/bin/env python3
"""Deterministic health check for the docs site.

Used by docs-steward's Maintain mode to detect staleness, orphans,
link density, component usage, and design token coverage.

Outputs structured JSON to stdout and a human-readable summary to stderr.
Exit code: 0 if no critical issues, 1 if any critical issues.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ASSET_SOURCES = {
    "skills": ("skills/*/SKILL.md", "skills"),
    "agents": ("agents/*.md", "agents"),
    "mcp": ("mcp/*/server.py", "mcp"),
}
GENERATED_ROOT = Path("docs/src/content/docs")
STARLIGHT_COMPONENTS = [
    "Aside", "Badge", "Card", "CardGrid", "LinkCard",
    "Steps", "Tabs", "TabItem", "FileTree", "Code",
]
TOKEN_CATEGORIES = {
    "type-colors": re.compile(r"--type-"),
    "fonts": re.compile(r"--sl-font"),
    "content-width": re.compile(r"--sl-content-width"),
    "spacing": re.compile(r"--spacing|--gap|--pad"),
    "shadows": re.compile(r"--shadow"),
    "radius": re.compile(r"--radius"),
    "motion": re.compile(r"--duration|--ease|--transition|--motion"),
    "z-index": re.compile(r"--z-"),
}
CUSTOM_CSS = Path("docs/src/styles/custom.css")
SPECIAL_PAGES = {"index.mdx"}


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _mtime(p: Path) -> float:
    return p.stat().st_mtime


def _resolve_name(path: Path, asset_type: str) -> str:
    """Extract the asset name from a source path."""
    if asset_type in ("skills", "mcp"):
        return path.parent.name  # skills/foo/SKILL.md -> foo
    return path.stem  # agents/foo.md -> foo


def _collect_sources(root: Path) -> dict[str, list[tuple[str, Path]]]:
    result: dict[str, list[tuple[str, Path]]] = {}
    for atype, (pattern, _) in ASSET_SOURCES.items():
        result[atype] = [
            (_resolve_name(p, atype), p) for p in sorted(root.glob(pattern))
        ]
    return result


def _collect_generated(root: Path) -> dict[str, list[tuple[str, Path]]]:
    result: dict[str, list[tuple[str, Path]]] = {}
    gen_root = root / GENERATED_ROOT
    for atype in ASSET_SOURCES:
        gen_dir = gen_root / atype
        if gen_dir.is_dir():
            result[atype] = [
                (p.stem, p)
                for p in sorted(gen_dir.glob("*.mdx"))
                if p.name not in SPECIAL_PAGES
            ]
        else:
            result[atype] = []
    return result


# -- Checks ----------------------------------------------------------------

def check_staleness(root: Path) -> dict:
    """Compare source asset mtimes vs generated MDX mtimes."""
    sources, generated = _collect_sources(root), _collect_generated(root)
    stale_pages: list[dict] = []
    total = 0
    for atype in ASSET_SOURCES:
        src_map = dict(sources.get(atype, []))
        for name, gen_path in generated.get(atype, []):
            if name not in src_map:
                continue
            total += 1
            src_mt, gen_mt = _mtime(src_map[name]), _mtime(gen_path)
            if src_mt > gen_mt:
                stale_pages.append({
                    "source": str(src_map[name].relative_to(root)),
                    "generated": str(gen_path.relative_to(root)),
                    "source_mtime": _iso(src_mt),
                    "generated_mtime": _iso(gen_mt),
                })
    n = len(stale_pages)
    status = "ok" if n == 0 else ("warning" if n <= 3 else "critical")
    return {"status": status, "stale_pages": stale_pages,
            "total_pages": total, "stale_count": n}


def check_orphans(root: Path) -> dict:
    """Find generated MDX pages whose source assets no longer exist."""
    sources, generated = _collect_sources(root), _collect_generated(root)
    orphaned: list[str] = []
    total = 0
    for atype in ASSET_SOURCES:
        src_names = {name for name, _ in sources.get(atype, [])}
        for name, gen_path in generated.get(atype, []):
            total += 1
            if name not in src_names:
                orphaned.append(str(gen_path.relative_to(root)))
    status = "ok" if not orphaned else "warning"
    return {"status": status, "orphaned_pages": orphaned,
            "total_generated": total, "orphan_count": len(orphaned)}


def check_links(root: Path) -> dict:
    """Count internal and external links in generated MDX files."""
    generated = _collect_generated(root)
    no_links: list[str] = []
    total_int = total_ext = 0
    href_re = re.compile(r'href=["\']([^"\']+)["\']')
    md_re = re.compile(r"\]\(([^)]+)\)")
    for atype in ASSET_SOURCES:
        for _, gen_path in generated.get(atype, []):
            text = gen_path.read_text(encoding="utf-8")
            urls = href_re.findall(text) + md_re.findall(text)
            internal = sum(1 for u in urls if u.startswith("/"))
            external = sum(1 for u in urls if u.startswith("http"))
            total_int += internal
            total_ext += external
            if internal + external == 0:
                no_links.append(str(gen_path.relative_to(root)))
    status = "ok" if not no_links else "info"
    return {"status": status, "pages_without_links": no_links,
            "total_internal_links": total_int, "total_external_links": total_ext}


def check_components(root: Path) -> dict:
    """Detect Starlight component imports in generated MDX files."""
    generated = _collect_generated(root)
    usage: dict[str, int] = {c: 0 for c in STARLIGHT_COMPONENTS}
    no_comp: list[str] = []
    total_with = 0
    imp_re = re.compile(
        r"""import\s+\{([^}]+)\}\s+from\s+['"]@astrojs/starlight/components['"]"""
    )
    for atype in ASSET_SOURCES:
        for _, gen_path in generated.get(atype, []):
            text = gen_path.read_text(encoding="utf-8")
            found: set[str] = set()
            for block in imp_re.findall(text):
                for tok in block.split(","):
                    name = tok.strip()
                    if name in usage:
                        found.add(name)
            if found:
                total_with += 1
                for comp in found:
                    tag_count = len(re.findall(rf"<{comp}[\s/>]", text))
                    usage[comp] += max(tag_count, 1)
            else:
                no_comp.append(str(gen_path.relative_to(root)))
    status = "ok" if not no_comp else "info"
    return {"status": status, "pages_without_components": no_comp,
            "component_usage": usage, "total_pages_with_components": total_with}


def check_tokens(root: Path) -> dict:
    """Audit CSS custom property coverage in custom.css."""
    css_path = root / CUSTOM_CSS
    if not css_path.is_file():
        return {"status": "critical", "defined_categories": [],
                "missing_categories": sorted(TOKEN_CATEGORIES), "total_custom_properties": 0}
    text = css_path.read_text(encoding="utf-8")
    props = re.findall(r"^\s*(--[\w-]+)\s*:", text, re.MULTILINE)
    defined = sorted(c for c, p in TOKEN_CATEGORIES.items() if p.search(text))
    missing = sorted(c for c, p in TOKEN_CATEGORIES.items() if not p.search(text))
    status = "ok" if not missing else ("info" if len(missing) <= 2 else "warning")
    return {"status": status, "defined_categories": defined,
            "missing_categories": missing, "total_custom_properties": len(props)}


# -- Runner ----------------------------------------------------------------

ALL_CHECKS = {
    "staleness": check_staleness,
    "orphans": check_orphans,
    "links": check_links,
    "components": check_components,
    "tokens": check_tokens,
}


def run_checks(root: Path, selected: list[str]) -> dict:
    checks_out: dict[str, dict] = {}
    for name in selected:
        checks_out[name] = ALL_CHECKS[name](root)
    summary = {"critical": 0, "warning": 0, "info": 0, "ok": 0}
    for r in checks_out.values():
        s = r.get("status", "ok")
        if s in summary:
            summary[s] += 1
    return {"timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "checks": checks_out, "summary": summary}


def _stderr(report: dict) -> None:
    """Print human-readable summary to stderr."""
    icons = {"ok": "[OK]", "info": "[INFO]", "warning": "[WARN]", "critical": "[CRIT]"}
    checks = report["checks"]
    err = lambda *a, **kw: print(*a, file=sys.stderr, **kw)  # noqa: E731
    err("\n=== Docs Health Check ===\n")
    for name, res in checks.items():
        err(f"  {icons.get(res.get('status', 'ok'), '[??]')} {name}")
        if name == "staleness" and res.get("stale_count", 0):
            err(f"       {res['stale_count']}/{res['total_pages']} pages stale")
            for p in res["stale_pages"][:5]:
                err(f"         - {p['source']}")
        elif name == "orphans" and res.get("orphan_count", 0):
            err(f"       {res['orphan_count']} orphaned pages")
            for p in res["orphaned_pages"][:5]:
                err(f"         - {p}")
        elif name == "links":
            err(f"       internal={res['total_internal_links']} "
                f"external={res['total_external_links']}")
            nl = res.get("pages_without_links", [])
            if nl:
                err(f"       {len(nl)} pages with zero links")
        elif name == "components":
            active = sum(1 for n in res.get("component_usage", {}).values() if n > 0)
            err(f"       {res['total_pages_with_components']} pages use "
                f"components ({active} distinct)")
            nc = res.get("pages_without_components", [])
            if nc:
                err(f"       {len(nc)} pages without components")
        elif name == "tokens":
            err(f"       {res['total_custom_properties']} custom properties, "
                f"{len(res.get('defined_categories', []))} categories defined")
            m = res.get("missing_categories", [])
            if m:
                err(f"       missing: {', '.join(m)}")
    err()
    totals = " | ".join(
        f"{k.upper()}: {v}" for k, v in report["summary"].items() if v > 0)
    err(f"  Summary: {totals or 'no checks run'}\n")


# -- CLI -------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Deterministic health check for the docs site.",
        epilog="Outputs JSON to stdout, human-readable summary to stderr.",
    )
    p.add_argument("--project-root", type=Path, default=Path.cwd(),
                   help="Project root directory (default: cwd)")
    p.add_argument("--check", action="append", dest="checks",
                   choices=list(ALL_CHECKS),
                   help="Run a specific check (repeatable). Omit for --all.")
    p.add_argument("--all", action="store_true",
                   help="Run all checks (default when no --check given)")
    p.add_argument("--quiet", action="store_true",
                   help="Suppress human-readable summary on stderr")
    return p


def main() -> int:
    args = build_parser().parse_args()
    root = args.project_root.resolve()
    if not root.is_dir():
        print(f"Error: project root does not exist: {root}", file=sys.stderr)
        return 1
    if args.all or not args.checks:
        selected = list(ALL_CHECKS)
    else:
        seen: set[str] = set()
        selected = [c for c in args.checks if c not in seen and not seen.add(c)]  # type: ignore[func-returns-value]
    report = run_checks(root, selected)
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    if not args.quiet:
        _stderr(report)
    return 1 if report["summary"].get("critical", 0) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
