"""Maintainer-facing generated reports pipeline (dual MDX + JSON output).

Modeled on `write_harness_support_page()` in `wagents/docs.py`: each report is
a pure collector (returns a JSON-serializable dict from current repo state)
plus a renderer (dict -> MDX text). `write_reports_pages()` drives every
registered report from `_docs_generate_impl()`; `reports_stale_reasons()` is
exercised by `docs generate --check`.

Reports write two artifacts each:

- `docs/src/content/docs/reports/<slug>.mdx` — human-browsable page
- `docs/public/generated-reports/<slug>.json` — machine-consumable payload
  (future `mcp-docs-index` / `mcp-eval-results` servers read these directly)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

from wagents import CONTENT_DIR, DOCS_DIR, ROOT
from wagents.parsing import parse_frontmatter

REPORTS_CONTENT_DIR = CONTENT_DIR / "reports"
REPORTS_JSON_DIR = DOCS_DIR / "public" / "generated-reports"

_ABS_MARKDOWN_LINK_RE = re.compile(r"\]\((/[^)\s#]+)\)")
_ABS_HREF_LINK_RE = re.compile(r"""\bhref=["'](/[^"'\s#]+)["']""")
_IGNORED_LINK_PREFIXES = ("/generated-", "/favicon", "/pagefind", "/_astro")


def _slug_for_content_path(page: Path) -> str:
    """Return the Starlight route slug (e.g. '/skills/catalog') for a content mdx path."""
    rel = page.relative_to(CONTENT_DIR).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "index":
        parts = parts[:-1]
    if not parts:
        return "/"
    return "/" + "/".join(parts)


def _iter_content_pages() -> list[Path]:
    if not CONTENT_DIR.exists():
        return []
    reports_dir = REPORTS_CONTENT_DIR.resolve()
    pages: list[Path] = []
    for path in CONTENT_DIR.rglob("*.mdx"):
        if not path.is_file():
            continue
        try:
            if path.resolve().is_relative_to(reports_dir):
                continue
        except OSError:
            continue
        pages.append(path)
    return sorted(pages)


def _read_frontmatter(page: Path) -> dict[str, Any]:
    try:
        text = page.read_text(encoding="utf-8", errors="replace")
        fm, _ = parse_frontmatter(text)
        return fm if isinstance(fm, dict) else {}
    except (OSError, ValueError):
        return {}


def iter_content_pages() -> list[Path]:
    """Return every generated docs content page path (public wrapper for MCP consumers)."""
    return _iter_content_pages()


def read_page_frontmatter(page: Path) -> dict[str, Any]:
    """Return a content page's parsed frontmatter dict (public wrapper for MCP consumers)."""
    return _read_frontmatter(page)


# ---------------------------------------------------------------------------
# Report registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReportSpec:
    slug: str
    title: str
    description: str
    collect: Callable[[], dict[str, Any]]
    render_mdx: Callable[[dict[str, Any]], str]
    # Historical/trend reports accumulate state across generate runs and are
    # not a pure function of current repo state; `--check` only verifies they
    # exist rather than diffing byte-for-byte against a fresh collect().
    historical: bool = False


# ---------------------------------------------------------------------------
# docs-dependency-drift (T-210a/b)
# ---------------------------------------------------------------------------

_STARLIGHT_PLUGIN_PREFIXES = ("starlight-",)


def collect_docs_dependency_drift() -> dict[str, Any]:
    """Detect drift between docs npm dependencies, astro.config.mjs, and the artifact registry."""
    package_json_path = DOCS_DIR / "package.json"
    astro_config_path = DOCS_DIR / "astro.config.mjs"
    registry_path = ROOT / "config" / "docs-artifact-registry.json"

    package_json = json.loads(package_json_path.read_text(encoding="utf-8")) if package_json_path.exists() else {}
    astro_config_text = astro_config_path.read_text(encoding="utf-8") if astro_config_path.exists() else ""
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {}

    deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
    plugin_deps = sorted(name for name in deps if name.startswith(_STARLIGHT_PLUGIN_PREFIXES))
    accounted_plugins = registry.get("docs_dependency_drift", {}).get("accounted_plugin_dependencies", {})
    if not isinstance(accounted_plugins, dict):
        accounted_plugins = {}
    registered_plugins = [name for name in plugin_deps if name in astro_config_text]
    accounted_plugin_deps = sorted(
        name for name in plugin_deps if name in accounted_plugins and name not in registered_plugins
    )
    unregistered_plugins = [
        name for name in plugin_deps if name not in registered_plugins and name not in accounted_plugin_deps
    ]

    missing_artifacts = [
        artifact["path"] for artifact in registry.get("artifacts", []) if not (ROOT / artifact["path"]).exists()
    ]
    missing_source_registries = [
        src for src in registry.get("source_registries", []) if not (ROOT / src.rstrip("/")).exists()
    ]

    return {
        "checked_sources": [
            "docs/package.json",
            "docs/astro.config.mjs",
            "config/docs-artifact-registry.json",
        ],
        "plugin_dependencies": plugin_deps,
        "registered_plugin_dependencies": registered_plugins,
        "accounted_plugin_dependencies": {
            name: str(accounted_plugins.get(name) or "accounted outside astro.config.mjs")
            for name in accounted_plugin_deps
        },
        "unregistered_plugin_dependencies": unregistered_plugins,
        "missing_registered_artifacts": missing_artifacts,
        "missing_source_registries": missing_source_registries,
        "drift_detected": bool(unregistered_plugins or missing_artifacts or missing_source_registries),
    }


def render_docs_dependency_drift_mdx(data: dict[str, Any]) -> str:
    status = "🔴 Drift detected" if data["drift_detected"] else "🟢 No drift detected"
    parts = [
        "---",
        "title: Docs Dependency Drift",
        (
            "description: Drift between docs npm dependencies, astro.config.mjs plugin wiring, "
            "and the docs artifact registry"
        ),
        "---",
        "",
        "{/* Auto-generated by wagents docs generate - do not edit */}",
        "",
        f"**Status:** {status}",
        "",
        "Checks that every `starlight-*` npm dependency in `docs/package.json` is either registered as "
        "a plugin in `docs/astro.config.mjs` or explicitly accounted in "
        "`config/docs-artifact-registry.json`, and that every declared artifact/source path still exists on disk.",
        "",
        "## Starlight plugin dependencies",
        "",
    ]
    if data["plugin_dependencies"]:
        for name in data["plugin_dependencies"]:
            if name in data["unregistered_plugin_dependencies"]:
                flag = " ⚠️ not referenced in astro.config.mjs or accounted registry"
            elif name in data.get("accounted_plugin_dependencies", {}):
                reason = data["accounted_plugin_dependencies"][name]
                flag = f" ✅ accounted — {reason}"
            else:
                flag = " ✅"
            parts.append(f"- `{name}`{flag}")
    else:
        parts.append("_No `starlight-*` dependencies found in `docs/package.json`._")
    parts.extend(["", "## Missing registered artifacts", ""])
    if data["missing_registered_artifacts"]:
        for path in data["missing_registered_artifacts"]:
            parts.append(f"- `{path}` — declared in `docs-artifact-registry.json` but missing on disk")
    else:
        parts.append("_All artifacts declared in `config/docs-artifact-registry.json` exist on disk._")
    parts.extend(["", "## Missing source registries", ""])
    if data["missing_source_registries"]:
        for path in data["missing_source_registries"]:
            parts.append(f"- `{path}` — declared as a source registry but missing on disk")
    else:
        parts.append("_All declared source registries exist on disk._")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# llms-txt-coverage (T-310a-e)
# ---------------------------------------------------------------------------


def collect_llms_txt_coverage() -> dict[str, Any]:
    """Report content pages missing the title/description fields `starlight-llms-txt` needs."""
    pages = _iter_content_pages()
    missing_title: list[str] = []
    missing_description: list[str] = []
    for page in pages:
        fm = _read_frontmatter(page)
        rel = str(page.relative_to(CONTENT_DIR))
        if not fm.get("title"):
            missing_title.append(rel)
        if not fm.get("description"):
            missing_description.append(rel)
    total = len(pages)
    uncovered = len(set(missing_title) | set(missing_description))
    covered = total - uncovered
    coverage_pct = round((covered / total) * 100, 1) if total else 100.0
    return {
        "total_pages": total,
        "covered_pages": covered,
        "coverage_pct": coverage_pct,
        "missing_title": sorted(missing_title),
        "missing_description": sorted(missing_description),
    }


def render_llms_txt_coverage_mdx(data: dict[str, Any]) -> str:
    parts = [
        "---",
        "title: llms.txt Coverage",
        "description: Content pages missing the title/description fields starlight-llms-txt needs",
        "---",
        "",
        "{/* Auto-generated by wagents docs generate - do not edit */}",
        "",
        "[`starlight-llms-txt`](https://www.npmjs.com/package/starlight-llms-txt) builds `/llms.txt` and "
        "`/llms-full.txt` from every content page's `title` and `description` frontmatter. Pages missing "
        "either field degrade the generated summary.",
        "",
        f"**Coverage:** {data['coverage_pct']}% ({data['covered_pages']}/{data['total_pages']} pages)",
        "",
        "## Pages missing `title`",
        "",
    ]
    if data["missing_title"]:
        parts.extend(f"- `{p}`" for p in data["missing_title"])
    else:
        parts.append("_None._")
    parts.extend(["", "## Pages missing `description`", ""])
    if data["missing_description"]:
        parts.extend(f"- `{p}`" for p in data["missing_description"])
    else:
        parts.append("_None._")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# site-graph-insights (T-311a-f)
# ---------------------------------------------------------------------------


def _build_link_graph() -> tuple[set[str], dict[str, set[str]], dict[str, set[str]]]:
    pages = _iter_content_pages()
    slug_by_path = {page: _slug_for_content_path(page) for page in pages}
    known_slugs = set(slug_by_path.values())
    outgoing: dict[str, set[str]] = {slug: set() for slug in known_slugs}
    incoming: dict[str, set[str]] = {slug: set() for slug in known_slugs}
    for page, slug in slug_by_path.items():
        try:
            text = page.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            continue
        matches = [*_ABS_MARKDOWN_LINK_RE.finditer(text), *_ABS_HREF_LINK_RE.finditer(text)]
        for match in matches:
            target = match.group(1).rstrip("/") or "/"
            if target.startswith(_IGNORED_LINK_PREFIXES) or target == slug:
                continue
            if target in known_slugs:
                outgoing[slug].add(target)
                incoming[target].add(slug)
    return known_slugs, outgoing, incoming


def collect_site_graph_insights() -> dict[str, Any]:
    """Compute a lightweight internal-link graph summary (orphans, most-linked pages)."""
    known_slugs, outgoing, incoming = _build_link_graph()
    orphans = sorted(slug for slug in known_slugs if not incoming[slug] and not outgoing[slug])
    most_linked = sorted(
        ((slug, len(incoming[slug])) for slug in known_slugs),
        key=lambda kv: (-kv[1], kv[0]),
    )
    return {
        "total_pages": len(known_slugs),
        "total_internal_links": sum(len(v) for v in outgoing.values()),
        "orphan_count": len(orphans),
        "orphan_pages": orphans,
        "most_linked_pages": [{"slug": s, "backlinks": c} for s, c in most_linked[:15] if c > 0],
        "note": (
            "Counts static absolute-path markdown and MDX/HTML href links only "
            "(paths like /foo/); relative links, generated sidebars, and client-created links are not resolved."
        ),
    }


def render_site_graph_insights_mdx(data: dict[str, Any]) -> str:
    parts = [
        "---",
        "title: Site Graph Insights",
        "description: Internal link graph summary derived from generated docs content",
        "---",
        "",
        "{/* Auto-generated by wagents docs generate - do not edit */}",
        "",
        f"Complements the interactive graph rendered by `starlight-site-graph`. {data['note']}",
        "",
        f"- **Total pages:** {data['total_pages']}",
        f"- **Total internal links:** {data['total_internal_links']}",
        f"- **Orphan pages (no inbound or outbound links):** {data['orphan_count']}",
        "",
        "## Most-linked pages",
        "",
        "| Page | Backlinks |",
        "| ---- | --------- |",
    ]
    for entry in data["most_linked_pages"]:
        parts.append(f"| `{entry['slug']}` | {entry['backlinks']} |")
    if not data["most_linked_pages"]:
        parts.append("| _None_ | — |")
    parts.extend(["", "## Orphan pages", ""])
    if data["orphan_pages"]:
        parts.extend(f"- `{slug}`" for slug in data["orphan_pages"])
    else:
        parts.append("_None._")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# docs-link-check (T-312a-d)
# ---------------------------------------------------------------------------


def collect_docs_link_check() -> dict[str, Any]:
    """Scan content pages for absolute markdown links that don't resolve to a known route."""
    pages = _iter_content_pages()
    known_slugs = {_slug_for_content_path(page) for page in pages}
    broken: list[dict[str, str]] = []
    for page in pages:
        rel = str(page.relative_to(CONTENT_DIR))
        try:
            text = page.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            # docs generate rewrites generated content in phases; tolerate a
            # stale rglob result from the same process and let the next pass
            # observe the stable tree.
            continue
        for match in _ABS_MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).rstrip("/") or "/"
            if target.startswith(_IGNORED_LINK_PREFIXES):
                continue
            if target not in known_slugs:
                broken.append({"page": rel, "target": target})
    return {
        "total_pages_scanned": len(pages),
        "broken_count": len(broken),
        "broken_internal_links": broken,
        "note": "Complements the build-time starlight-links-validator check; scans absolute markdown links only.",
    }


def render_docs_link_check_mdx(data: dict[str, Any]) -> str:
    status = "🔴 Broken links found" if data["broken_count"] else "🟢 No broken internal links"
    parts = [
        "---",
        "title: Docs Link Check",
        "description: Persisted snapshot of absolute internal markdown links that do not resolve",
        "---",
        "",
        "{/* Auto-generated by wagents docs generate - do not edit */}",
        "",
        f"**Status:** {status} ({data['broken_count']} of {data['total_pages_scanned']} pages scanned)",
        "",
        data["note"],
        "",
        "## Broken links",
        "",
        "| Page | Target |",
        "| ---- | ------ |",
    ]
    for entry in data["broken_internal_links"]:
        parts.append(f"| `{entry['page']}` | `{entry['target']}` |")
    if not data["broken_internal_links"]:
        parts.append("| _None_ | — |")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# docs-graph-snapshot (T-313a-d) — historical/trend
# ---------------------------------------------------------------------------

_GRAPH_SNAPSHOT_HISTORY_WINDOW = 90


def collect_docs_graph_snapshot() -> dict[str, Any]:
    """Snapshot today's graph metrics and append to a rolling trend history."""
    insights = collect_site_graph_insights()
    today = date.today().isoformat()
    json_path = REPORTS_JSON_DIR / "docs-graph-snapshot.json"
    history: list[dict[str, Any]] = []
    if json_path.exists():
        try:
            prior = json.loads(json_path.read_text(encoding="utf-8"))
            history = [h for h in prior.get("history", []) if h.get("date") != today]
        except (OSError, json.JSONDecodeError):
            history = []
    history.append({
        "date": today,
        "total_pages": insights["total_pages"],
        "total_internal_links": insights["total_internal_links"],
        "orphan_count": insights["orphan_count"],
    })
    history.sort(key=lambda h: h["date"])
    return {
        "latest": insights,
        "history": history[-_GRAPH_SNAPSHOT_HISTORY_WINDOW:],
    }


def render_docs_graph_snapshot_mdx(data: dict[str, Any]) -> str:
    latest = data["latest"]
    parts = [
        "---",
        "title: Docs Graph Snapshot",
        "description: Trend of page count, internal links, and orphan pages over time",
        "---",
        "",
        "{/* Auto-generated by wagents docs generate - do not edit */}",
        "",
        f"Latest snapshot: {latest['total_pages']} pages, {latest['total_internal_links']} internal links, "
        f"{latest['orphan_count']} orphans. See [Site Graph Insights](/reports/site-graph-insights/) for detail.",
        "",
        "## Trend (most recent first)",
        "",
        "| Date | Pages | Internal Links | Orphans |",
        "| ---- | ----- | --------------- | ------- |",
    ]
    for entry in reversed(data["history"]):
        parts.append(
            f"| {entry['date']} | {entry['total_pages']} | {entry['total_internal_links']} | {entry['orphan_count']} |"
        )
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# maintainer-ops-dashboard (T-800a-h, W14)
# ---------------------------------------------------------------------------


def collect_maintainer_ops_dashboard() -> dict[str, Any]:
    """Aggregate all generated-reports JSON payloads into one maintainer view."""
    sections: dict[str, Any] = {}
    report_files = sorted(REPORTS_JSON_DIR.glob("*.json")) if REPORTS_JSON_DIR.is_dir() else []
    for path in report_files:
        if path.name == "maintainer-ops-dashboard.json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {"error": "unreadable"}
        sections[path.stem] = {
            "path": str(path.relative_to(ROOT)),
            "keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
            "summary": _summarize_report_payload(path.stem, payload),
        }
    return {
        "report_count": len(sections),
        "reports_dir": str(REPORTS_JSON_DIR.relative_to(ROOT)),
        "sections": sections,
        "all_populated": len(sections) >= max(len(REPORT_SPECS) - 1, 1),
    }


def _summarize_report_payload(slug: str, payload: Any) -> str:
    if not isinstance(payload, dict):
        return "non-object payload"
    if slug == "docs-dependency-drift":
        return "drift detected" if payload.get("drift_detected") else "no drift"
    if slug == "llms-txt-coverage":
        return f"{payload.get('pages_missing_title', 0)} missing title"
    if slug == "site-graph-insights":
        return f"{payload.get('orphan_count', 0)} orphans"
    if slug == "docs-link-check":
        return f"{payload.get('broken_count', 0)} broken links"
    if slug == "docs-graph-snapshot":
        history = payload.get("history") or []
        return f"{len(history)} snapshots"
    return f"{len(payload)} top-level keys"


def render_maintainer_ops_dashboard_mdx(data: dict[str, Any]) -> str:
    status = "🟢 All sections populated" if data["all_populated"] else "🟡 Partial coverage"
    report_page_slugs = {spec.slug for spec in REPORT_SPECS}
    parts = [
        "---",
        "title: Maintainer Ops Dashboard",
        "description: Aggregated view of generated-reports JSON for maintainer observability",
        "---",
        "",
        "{/* Auto-generated by wagents docs generate - do not edit */}",
        "",
        f"**Status:** {status}",
        "",
        "Synthesizes machine-readable payloads from `docs/public/generated-reports/*.json`. "
        "Use `/skill-quality-dashboard` or MCP `ci-artifacts` for programmatic access.",
        "",
        "## Report sections",
        "",
        "| Report | Summary | JSON |",
        "| ------ | ------- | ---- |",
    ]
    for slug, section in sorted(data.get("sections", {}).items()):
        report_label = f"[{slug}](/reports/{slug}/)" if slug in report_page_slugs else slug
        parts.append(f"| {report_label} | {section.get('summary', '—')} | `{section.get('path', '')}` |")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Registry + drivers
# ---------------------------------------------------------------------------

REPORT_SPECS: tuple[ReportSpec, ...] = (
    ReportSpec(
        slug="docs-dependency-drift",
        title="Docs Dependency Drift",
        description="Drift between docs npm dependencies, astro.config.mjs, and the docs artifact registry",
        collect=collect_docs_dependency_drift,
        render_mdx=render_docs_dependency_drift_mdx,
    ),
    ReportSpec(
        slug="llms-txt-coverage",
        title="llms.txt Coverage",
        description="Content pages missing the title/description fields starlight-llms-txt needs",
        collect=collect_llms_txt_coverage,
        render_mdx=render_llms_txt_coverage_mdx,
    ),
    ReportSpec(
        slug="site-graph-insights",
        title="Site Graph Insights",
        description="Internal link graph summary derived from generated docs content",
        collect=collect_site_graph_insights,
        render_mdx=render_site_graph_insights_mdx,
    ),
    ReportSpec(
        slug="docs-link-check",
        title="Docs Link Check",
        description="Persisted snapshot of absolute internal markdown links that do not resolve",
        collect=collect_docs_link_check,
        render_mdx=render_docs_link_check_mdx,
    ),
    ReportSpec(
        slug="docs-graph-snapshot",
        title="Docs Graph Snapshot",
        description="Trend of page count, internal links, and orphan pages over time",
        collect=collect_docs_graph_snapshot,
        render_mdx=render_docs_graph_snapshot_mdx,
        historical=True,
    ),
    ReportSpec(
        slug="maintainer-ops-dashboard",
        title="Maintainer Ops Dashboard",
        description="Aggregated maintainer view of all generated-reports JSON payloads",
        collect=collect_maintainer_ops_dashboard,
        render_mdx=render_maintainer_ops_dashboard_mdx,
    ),
)


def _write_report(spec: ReportSpec) -> dict[str, Any]:
    data = spec.collect()
    mdx = spec.render_mdx(data)
    REPORTS_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_JSON_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_CONTENT_DIR / f"{spec.slug}.mdx").write_text(mdx, encoding="utf-8")
    (REPORTS_JSON_DIR / f"{spec.slug}.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return data


def write_reports_index_page() -> None:
    """Write reports/index.mdx linking every registered report."""
    parts = [
        "---",
        "title: Reports",
        "description: Generated maintainer observability reports for the docs site and asset catalog",
        "---",
        "",
        "import { CardGrid, LinkCard } from '@astrojs/starlight/components';",
        "",
        "Each report below is regenerated by `wagents docs generate` and mirrored as machine-readable JSON "
        "under `docs/public/generated-reports/<slug>.json` for MCP-native consumption.",
        "",
        "<CardGrid>",
    ]
    for spec in REPORT_SPECS:
        parts.append(
            f'  <LinkCard title="{spec.title}" href="/reports/{spec.slug}/" description="{spec.description}" />'
        )
    parts.extend(["</CardGrid>", ""])
    REPORTS_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_CONTENT_DIR / "index.mdx").write_text("\n".join(parts), encoding="utf-8")


def write_reports_pages() -> None:
    """Generate every registered report's MDX + JSON output, plus the reports index.

    Runs two full passes. Several collectors depend on the reports tree itself
    being fully populated: `docs-dependency-drift` asserts the reports
    directories exist, and `llms-txt-coverage` / `site-graph-insights` /
    `docs-link-check` scan every content page under `CONTENT_DIR`, which
    includes the reports pages written by this same function. The first pass
    bootstraps that state (creating any missing report pages); the second
    pass recomputes every report against the now-complete, stable page set,
    which is the fixed point `--check` compares future runs against.
    """
    for _ in range(2):
        for spec in REPORT_SPECS:
            _write_report(spec)
        write_reports_index_page()


def _docs_graph_snapshot_stale_reasons(spec: ReportSpec, mdx_path: Path, json_path: Path) -> list[str]:
    reasons: list[str] = []
    if not mdx_path.exists() or not json_path.exists():
        reasons.append(
            "docs/src/content/docs/reports/docs-graph-snapshot.mdx or its JSON payload is missing; "
            "run `uv run wagents docs generate --no-installed`"
        )
        return reasons

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        reasons.append(
            "docs/public/generated-reports/docs-graph-snapshot.json is stale; "
            "run `uv run wagents docs generate --no-installed`"
        )
        return reasons

    if not isinstance(payload, dict):
        reasons.append(
            "docs/public/generated-reports/docs-graph-snapshot.json is stale; "
            "run `uv run wagents docs generate --no-installed`"
        )
        return reasons

    expected_latest = collect_site_graph_insights()
    if payload.get("latest") != expected_latest:
        reasons.append(
            "docs/public/generated-reports/docs-graph-snapshot.json is stale; "
            "run `uv run wagents docs generate --no-installed`"
        )

    try:
        expected_mdx = spec.render_mdx(payload)
    except (KeyError, TypeError):
        reasons.append(
            "docs/public/generated-reports/docs-graph-snapshot.json is stale; "
            "run `uv run wagents docs generate --no-installed`"
        )
        return reasons

    try:
        actual_mdx = mdx_path.read_text(encoding="utf-8")
    except OSError:
        actual_mdx = None
    if actual_mdx != expected_mdx:
        reasons.append(
            "docs/src/content/docs/reports/docs-graph-snapshot.mdx is stale; "
            "run `uv run wagents docs generate --no-installed`"
        )
    return reasons


def reports_stale_reasons() -> list[str]:
    """Return remediation messages for any report whose on-disk output is stale."""
    reasons: list[str] = []
    for spec in REPORT_SPECS:
        mdx_path = REPORTS_CONTENT_DIR / f"{spec.slug}.mdx"
        json_path = REPORTS_JSON_DIR / f"{spec.slug}.json"
        if spec.historical:
            if spec.slug == "docs-graph-snapshot":
                reasons.extend(_docs_graph_snapshot_stale_reasons(spec, mdx_path, json_path))
                continue
            if not mdx_path.exists() or not json_path.exists():
                reasons.append(
                    f"docs/src/content/docs/reports/{spec.slug}.mdx or its JSON payload is missing; "
                    "run `uv run wagents docs generate --no-installed`"
                )
            continue
        data = spec.collect()
        expected_mdx = spec.render_mdx(data)
        expected_json = json.dumps(data, indent=2, sort_keys=True) + "\n"
        if not mdx_path.exists() or mdx_path.read_text(encoding="utf-8") != expected_mdx:
            reasons.append(
                f"docs/src/content/docs/reports/{spec.slug}.mdx is stale; "
                "run `uv run wagents docs generate --no-installed`"
            )
        if not json_path.exists() or json_path.read_text(encoding="utf-8") != expected_json:
            reasons.append(
                f"docs/public/generated-reports/{spec.slug}.json is stale; "
                "run `uv run wagents docs generate --no-installed`"
            )
    index_path = REPORTS_CONTENT_DIR / "index.mdx"
    if not index_path.exists():
        reasons.append(
            "docs/src/content/docs/reports/index.mdx missing; run `uv run wagents docs generate --no-installed`"
        )
    return reasons
