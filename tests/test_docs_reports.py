"""Tests for generated docs report renderers."""

import json

import pytest

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


def test_maintainer_dashboard_summarizes_docs_link_check_broken_count(tmp_path, monkeypatch):
    reports_json_dir = tmp_path / "docs" / "public" / "generated-reports"
    reports_json_dir.mkdir(parents=True)
    (reports_json_dir / "docs-link-check.json").write_text(
        json.dumps({"broken_count": 2, "broken_internal_links": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr(docs_reports, "ROOT", tmp_path)
    monkeypatch.setattr(docs_reports, "REPORTS_JSON_DIR", reports_json_dir)

    dashboard = docs_reports.collect_maintainer_ops_dashboard()

    assert dashboard["sections"]["docs-link-check"]["summary"] == "2 broken links"


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


def test_content_page_iterator_excludes_generated_reports(tmp_path, monkeypatch):
    content_dir = tmp_path / "docs"
    reports_dir = content_dir / "reports"
    reports_dir.mkdir(parents=True)
    (content_dir / "index.mdx").write_text("---\ntitle: Home\n---\n", encoding="utf-8")
    (reports_dir / "site-graph-insights.mdx").write_text(
        "---\ntitle: Generated report\n---\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(docs_reports, "CONTENT_DIR", content_dir)
    monkeypatch.setattr(docs_reports, "REPORTS_CONTENT_DIR", reports_dir)

    pages = docs_reports.iter_content_pages()

    assert pages == [content_dir / "index.mdx"]


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


def _graph_snapshot_spec():
    return next(spec for spec in docs_reports.REPORT_SPECS if spec.slug == "docs-graph-snapshot")


def _write_graph_snapshot(
    reports_dir,
    reports_json_dir,
    payload,
    mdx_text=None,
):
    reports_dir.mkdir(parents=True, exist_ok=True)
    reports_json_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "index.mdx").write_text("---\ntitle: Reports\n---\n", encoding="utf-8")
    (reports_json_dir / "docs-graph-snapshot.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if mdx_text is None:
        mdx_text = docs_reports.render_docs_graph_snapshot_mdx(payload)
    (reports_dir / "docs-graph-snapshot.mdx").write_text(mdx_text, encoding="utf-8")


def _prepare_graph_snapshot_stale_test(tmp_path, monkeypatch, current_latest):
    reports_dir = tmp_path / "content" / "reports"
    reports_json_dir = tmp_path / "public" / "generated-reports"
    monkeypatch.setattr(docs_reports, "REPORTS_CONTENT_DIR", reports_dir)
    monkeypatch.setattr(docs_reports, "REPORTS_JSON_DIR", reports_json_dir)
    monkeypatch.setattr(docs_reports, "REPORT_SPECS", (_graph_snapshot_spec(),))
    monkeypatch.setattr(docs_reports, "collect_site_graph_insights", lambda: current_latest)
    return reports_dir, reports_json_dir


def test_collect_docs_graph_snapshot_replaces_today_history_row(tmp_path, monkeypatch):
    current_latest = {"total_pages": 3, "total_internal_links": 4, "orphan_count": 0}
    reports_json_dir = tmp_path / "public" / "generated-reports"
    reports_json_dir.mkdir(parents=True)
    (reports_json_dir / "docs-graph-snapshot.json").write_text(
        json.dumps(
            {
                "latest": {"total_pages": 1, "total_internal_links": 1, "orphan_count": 1},
                "history": [
                    {"date": "2026-07-05", "total_pages": 1, "total_internal_links": 1, "orphan_count": 1},
                    {"date": "2026-07-06", "total_pages": 1, "total_internal_links": 1, "orphan_count": 1},
                    {"date": "not-a-date", "total_pages": 9, "total_internal_links": 9, "orphan_count": 9},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(docs_reports, "REPORTS_JSON_DIR", reports_json_dir)
    monkeypatch.setattr(docs_reports, "collect_site_graph_insights", lambda: current_latest)
    payload = docs_reports.collect_docs_graph_snapshot("2026-07-06")

    assert payload == {
        "latest": current_latest,
        "history": [
            {"date": "2026-07-05", "total_pages": 1, "total_internal_links": 1, "orphan_count": 1},
            {"date": "2026-07-06", "total_pages": 3, "total_internal_links": 4, "orphan_count": 0},
        ],
    }


def test_collect_docs_graph_snapshot_drops_noncanonical_today_history_alias(tmp_path, monkeypatch):
    current_latest = {"total_pages": 3, "total_internal_links": 4, "orphan_count": 0}
    reports_json_dir = tmp_path / "public" / "generated-reports"
    reports_json_dir.mkdir(parents=True)
    (reports_json_dir / "docs-graph-snapshot.json").write_text(
        json.dumps(
            {
                "latest": current_latest,
                "history": [
                    {"date": "20260706", "total_pages": 1, "total_internal_links": 1, "orphan_count": 1},
                    {"date": "2026-W28-1", "total_pages": 2, "total_internal_links": 2, "orphan_count": 2},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(docs_reports, "REPORTS_JSON_DIR", reports_json_dir)
    monkeypatch.setattr(docs_reports, "collect_site_graph_insights", lambda: current_latest)
    payload = docs_reports.collect_docs_graph_snapshot("2026-07-06")

    assert payload == {
        "latest": current_latest,
        "history": [{"date": "2026-07-06", "total_pages": 3, "total_internal_links": 4, "orphan_count": 0}],
    }


def test_reports_stale_reasons_detects_stale_docs_graph_snapshot_latest(tmp_path, monkeypatch):
    current_latest = {"total_pages": 2, "total_internal_links": 1, "orphan_count": 0}
    reports_dir, reports_json_dir = _prepare_graph_snapshot_stale_test(tmp_path, monkeypatch, current_latest)
    stale_payload = {
        "latest": {"total_pages": 1, "total_internal_links": 1, "orphan_count": 0},
        "history": [{"date": "2026-07-06", "total_pages": 1, "total_internal_links": 1, "orphan_count": 0}],
    }
    _write_graph_snapshot(reports_dir, reports_json_dir, stale_payload)

    reasons = docs_reports.reports_stale_reasons()

    assert "docs/public/generated-reports/docs-graph-snapshot.json is stale" in "\n".join(reasons)


def test_reports_stale_reasons_preserves_committed_docs_graph_history(tmp_path, monkeypatch):
    current_latest = {"total_pages": 2, "total_internal_links": 1, "orphan_count": 0}
    reports_dir, reports_json_dir = _prepare_graph_snapshot_stale_test(tmp_path, monkeypatch, current_latest)
    stale_payload = {
        "latest": current_latest,
        "history": [{"date": "2026-07-06", "total_pages": 1, "total_internal_links": 1, "orphan_count": 0}],
    }
    _write_graph_snapshot(reports_dir, reports_json_dir, stale_payload)

    reasons = docs_reports.reports_stale_reasons()

    assert not [reason for reason in reasons if "docs-graph-snapshot" in reason]


def test_docs_graph_check_does_not_add_a_wall_clock_history_row(tmp_path, monkeypatch):
    current_latest = {"total_pages": 2, "total_internal_links": 1, "orphan_count": 0}
    reports_dir, reports_json_dir = _prepare_graph_snapshot_stale_test(tmp_path, monkeypatch, current_latest)
    current_payload = {
        "latest": current_latest,
        "history": [{"date": "2026-07-06", "total_pages": 2, "total_internal_links": 1, "orphan_count": 0}],
    }
    _write_graph_snapshot(reports_dir, reports_json_dir, current_payload)

    reasons = docs_reports.reports_stale_reasons()

    assert not [reason for reason in reasons if "docs-graph-snapshot" in reason]
    assert json.loads((reports_json_dir / "docs-graph-snapshot.json").read_text()) == current_payload


def test_collect_docs_graph_snapshot_is_deterministic_for_explicit_date(tmp_path, monkeypatch):
    current_latest = {"total_pages": 2, "total_internal_links": 1, "orphan_count": 0}
    reports_dir, reports_json_dir = _prepare_graph_snapshot_stale_test(tmp_path, monkeypatch, current_latest)
    current_payload = {
        "latest": current_latest,
        "history": [{"date": "2026-07-05", "total_pages": 1, "total_internal_links": 1, "orphan_count": 1}],
    }
    _write_graph_snapshot(reports_dir, reports_json_dir, current_payload)

    first = docs_reports.collect_docs_graph_snapshot("2026-07-06")
    _write_graph_snapshot(reports_dir, reports_json_dir, first)
    second = docs_reports.collect_docs_graph_snapshot("2026-07-06")

    assert second == first


def test_collect_docs_graph_snapshot_rejects_invalid_explicit_date(tmp_path, monkeypatch):
    current_latest = {"total_pages": 2, "total_internal_links": 1, "orphan_count": 0}
    _prepare_graph_snapshot_stale_test(tmp_path, monkeypatch, current_latest)

    with pytest.raises(ValueError, match="snapshot date must use YYYY-MM-DD"):
        docs_reports.collect_docs_graph_snapshot("2026-7-6")


def test_reports_stale_reasons_detects_stale_docs_graph_snapshot_mdx(tmp_path, monkeypatch):
    current_latest = {"total_pages": 2, "total_internal_links": 1, "orphan_count": 0}
    reports_dir, reports_json_dir = _prepare_graph_snapshot_stale_test(tmp_path, monkeypatch, current_latest)
    current_payload = {
        "latest": current_latest,
        "history": [{"date": "2026-07-06", "total_pages": 2, "total_internal_links": 1, "orphan_count": 0}],
    }
    _write_graph_snapshot(reports_dir, reports_json_dir, current_payload, mdx_text="stale\n")

    reasons = docs_reports.reports_stale_reasons()

    assert "docs/src/content/docs/reports/docs-graph-snapshot.mdx is stale" in "\n".join(reasons)


def test_reports_stale_reasons_detects_malformed_docs_graph_snapshot_json(tmp_path, monkeypatch):
    current_latest = {"total_pages": 2, "total_internal_links": 1, "orphan_count": 0}
    reports_dir, reports_json_dir = _prepare_graph_snapshot_stale_test(tmp_path, monkeypatch, current_latest)
    reports_dir.mkdir(parents=True)
    reports_json_dir.mkdir(parents=True)
    (reports_dir / "docs-graph-snapshot.mdx").write_text("stale\n", encoding="utf-8")
    (reports_json_dir / "docs-graph-snapshot.json").write_text("{not json", encoding="utf-8")

    reasons = docs_reports.reports_stale_reasons()

    assert "docs/public/generated-reports/docs-graph-snapshot.json is stale" in "\n".join(reasons)


def test_reports_stale_reasons_detects_non_object_docs_graph_snapshot_json(tmp_path, monkeypatch):
    current_latest = {"total_pages": 2, "total_internal_links": 1, "orphan_count": 0}
    reports_dir, reports_json_dir = _prepare_graph_snapshot_stale_test(tmp_path, monkeypatch, current_latest)
    _write_graph_snapshot(reports_dir, reports_json_dir, [], mdx_text="stale\n")

    reasons = docs_reports.reports_stale_reasons()

    assert "docs/public/generated-reports/docs-graph-snapshot.json is stale" in "\n".join(reasons)


def test_reports_stale_reasons_accepts_current_docs_graph_snapshot(tmp_path, monkeypatch):
    current_latest = {"total_pages": 2, "total_internal_links": 1, "orphan_count": 0}
    reports_dir, reports_json_dir = _prepare_graph_snapshot_stale_test(tmp_path, monkeypatch, current_latest)
    current_payload = {
        "latest": current_latest,
        "history": [{"date": "2026-07-06", "total_pages": 2, "total_internal_links": 1, "orphan_count": 0}],
    }
    _write_graph_snapshot(reports_dir, reports_json_dir, current_payload)

    reasons = docs_reports.reports_stale_reasons()

    assert not [reason for reason in reasons if "docs-graph-snapshot" in reason]
