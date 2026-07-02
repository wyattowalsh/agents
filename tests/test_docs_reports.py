"""Tests for generated docs report renderers."""

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
