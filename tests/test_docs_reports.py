"""Tests for generated docs report renderers."""

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
