"""Tests for generated docs report renderers."""

import json

from wagents import docs_reports
from wagents.docs_reports import render_maintainer_ops_dashboard_mdx


def test_maintainer_dashboard_links_only_registered_report_pages():
    mdx = render_maintainer_ops_dashboard_mdx({
        "all_populated": True,
        "sections": {
            "docs-link-check": {
                "summary": "0 broken links",
                "path": "docs/public/generated-reports/docs-link-check.json",
            },
            "hook-perf-baseline-bundle": {
                "summary": "4 top-level keys",
                "path": "docs/public/generated-reports/hook-perf-baseline-bundle.json",
            },
        },
    })

    assert "[docs-link-check](/reports/docs-link-check/)" in mdx
    assert "| hook-perf-baseline-bundle | 4 top-level keys |" in mdx
    assert "/reports/hook-perf-baseline-bundle/" not in mdx


def test_site_graph_counts_static_mdx_href_links(tmp_path, monkeypatch):
    content_dir = tmp_path / "docs"
    agents_dir = content_dir / "agents"
    agents_dir.mkdir(parents=True)
    (content_dir / "index.mdx").write_text(
        '---\ntitle: Home\n---\n<LinkCard title="Agents" href="/agents/" description="Browse agents." />\n',
        encoding="utf-8",
    )
    (agents_dir / "index.mdx").write_text(
        '---\ntitle: Agents\n---\n<LinkCard title="Recorder" href="/agents/agent-change-recorder/" />\n',
        encoding="utf-8",
    )
    (agents_dir / "agent-change-recorder.mdx").write_text(
        "---\ntitle: Recorder\n---\nAgent details.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(docs_reports, "CONTENT_DIR", content_dir)

    report = docs_reports.collect_site_graph_insights()

    assert report["total_internal_links"] == 2
    assert "/agents/agent-change-recorder" not in report["orphan_pages"]


def test_dependency_drift_allows_accounted_non_integration_plugins(tmp_path, monkeypatch):
    docs_dir = tmp_path / "docs"
    config_dir = tmp_path / "config"
    docs_dir.mkdir()
    config_dir.mkdir()
    (docs_dir / "package.json").write_text(
        json.dumps({
            "dependencies": {
                "starlight-announcement": "^1.0.0",
                "starlight-package-managers": "^1.0.0",
                "starlight-unaccounted": "^1.0.0",
            }
        }),
        encoding="utf-8",
    )
    (docs_dir / "astro.config.mjs").write_text(
        "import starlightAnnouncement from 'starlight-announcement';\n"
        "export default { integrations: [starlightAnnouncement()] };\n",
        encoding="utf-8",
    )
    (config_dir / "docs-artifact-registry.json").write_text(
        json.dumps({
            "docs_dependency_drift": {
                "accounted_plugin_dependencies": {
                    "starlight-package-managers": "used directly as an MDX component",
                }
            },
            "artifacts": [],
            "source_registries": [],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(docs_reports, "ROOT", tmp_path)
    monkeypatch.setattr(docs_reports, "DOCS_DIR", docs_dir)

    report = docs_reports.collect_docs_dependency_drift()
    mdx = docs_reports.render_docs_dependency_drift_mdx(report)

    assert report["accounted_plugin_dependencies"] == {
        "starlight-package-managers": "used directly as an MDX component",
    }
    assert report["unregistered_plugin_dependencies"] == ["starlight-unaccounted"]
    assert report["drift_detected"] is True
    assert "`starlight-package-managers` ✅ accounted — used directly as an MDX component" in mdx
    assert "`starlight-unaccounted` ⚠️ not referenced in astro.config.mjs or accounted registry" in mdx
