"""Regression tests for the research skill helper scripts."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, rel_path: str):
    path = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scanner = _load_module("research_scanner", "skills/research/scripts/research-scanner.py")
formatter = _load_module("research_finding_formatter", "skills/research/scripts/finding-formatter.py")
deduper = _load_module("research_source_deduplicator", "skills/research/scripts/source-deduplicator.py")
journal = _load_module("research_journal_store", "skills/research/scripts/journal-store.py")


@pytest.fixture
def journal_dir(tmp_path, monkeypatch):
    jdir = tmp_path / "research"
    jdir.mkdir()
    monkeypatch.setattr(journal, "JOURNAL_DIR", jdir)
    monkeypatch.setattr(journal, "ARCHIVE_DIR", jdir / "archive")
    return jdir


def _cmd_save(args: argparse.Namespace, capsys) -> dict:
    journal.cmd_save(args)
    out = capsys.readouterr().out
    return json.loads(out)


def test_scanner_preserves_mixed_case_technology_entities():
    result = scanner.scan("PostgreSQL vs SQLite vs DuckDB for analytical workloads")

    assert result["suggested_mode"] == "compare"
    assert result["comparison_detected"] is True
    assert "technology" in result["domain_signals"]
    assert {"PostgreSQL", "SQLite", "DuckDB"}.issubset(set(result["entities"]))
    assert "ostgreSQL" not in result["entities"]


def test_formatter_normalizes_legacy_source_fields_without_duplicate_source_text():
    raw = {
        "claim": "PostgreSQL supports MVCC",
        "confidence_raw": 0.8,
        "source_url": "https://www.postgresql.org/docs/current/mvcc.html",
        "source_tool": "docs",
        "excerpt": "PostgreSQL provides a rich set of tools for developers to manage concurrent access.",
        "cross_validation": "agrees across 2 independent sources",
    }

    normalized = formatter.normalize_finding(raw, 1)
    rendered = formatter.format_markdown([normalized])

    assert normalized["confidence"] == 0.8
    assert normalized["source_count"] == 1
    assert normalized["evidence"][0]["url"].startswith("https://www.postgresql.org")
    assert "agrees across 2 independent sources across" not in rendered


def test_deduplicator_preserves_legacy_sources_and_applies_confidence_caps():
    result = deduper.deduplicate(
        [
            [
                {
                    "claim": "DuckDB is suited for in-process analytical workloads",
                    "confidence_raw": 0.6,
                    "source_url": "https://duckdb.org/docs/",
                    "source_tool": "docs",
                    "excerpt": "DuckDB is an in-process analytical database.",
                }
            ],
            [
                {
                    "claim": "DuckDB is suited for in-process analytical workloads",
                    "confidence_raw": 0.7,
                    "source_url": "https://github.com/duckdb/duckdb",
                    "source_tool": "repo",
                    "excerpt": "DuckDB is an analytical in-process SQL database.",
                }
            ],
        ],
        threshold=1.0,
        verbose=False,
    )

    assert len(result) == 1
    finding = result[0]
    assert finding["source_count"] == 2
    assert finding["independent_source_count"] == 2
    assert finding["confidence"] == 0.69
    assert {ev["url"] for ev in finding["evidence"]} == {
        "https://duckdb.org/docs/",
        "https://github.com/duckdb/duckdb",
    }


def test_deduplicator_normalizes_descriptive_cross_validation_for_caps():
    result = deduper.deduplicate(
        [
            [
                {
                    "claim": "PostgreSQL supports MVCC",
                    "confidence": 0.9,
                    "cross_validation": "agrees across 2 independent sources",
                    "evidence": [
                        {"url": "https://www.postgresql.org/docs/current/mvcc.html", "tool": "docs"},
                        {"url": "https://www.postgresql.org/docs/current/transaction-iso.html", "tool": "docs"},
                    ],
                }
            ]
        ],
        threshold=1.0,
        verbose=False,
    )

    assert result[0]["confidence"] == 0.9
    assert result[0]["independent_source_count"] == 2


def test_journal_frontmatter_roundtrip_with_hyphenated_keys_and_escaped_quotes():
    meta = {
        "query": 'He said "hi"',
        "session-type": "research",
        "mean_confidence": 0.75,
        "tags": ["alpha", "beta"],
    }
    text = journal.serialize_frontmatter(meta) + "\n\n# Body\n\n---\n\nAfter rule\n"

    parsed, body = journal.parse_frontmatter(text)

    assert parsed == meta
    assert "After rule" in body


def test_journal_update_appends_state_and_preserves_body(journal_dir, capsys):
    created = _cmd_save(
        argparse.Namespace(
            query="What is PostgreSQL MVCC?",
            tier="standard",
            mode="investigate",
            status="In Progress",
            findings=None,
            update=None,
            wave=None,
            state=None,
        ),
        capsys,
    )
    path = Path(created["path"])
    original_body = path.read_text(encoding="utf-8")
    findings = [{"claim": "PostgreSQL uses MVCC", "confidence": 0.6}]

    updated = _cmd_save(
        argparse.Namespace(
            query=None,
            tier="standard",
            mode="investigate",
            status=None,
            findings=json.dumps(findings),
            update=str(path),
            wave=1,
            state=json.dumps({
                "next_action": "Wave 2",
                "leads_pending": ["https://example.com/a", "https://example.com/b"],
                "gaps": ["topic X needs more sources"],
            }),
        ),
        capsys,
    )

    text = path.read_text(encoding="utf-8")
    meta, body = journal.parse_frontmatter(text)
    loaded = journal.parse_findings_blocks(body)

    assert updated["action"] == "updated"
    assert "# Research: What is PostgreSQL MVCC?" in text
    assert original_body.split("# Research:")[1].splitlines()[0] in text
    assert meta["last_wave"] == 1
    assert meta["findings_count"] == 1
    assert meta["mean_confidence"] == 0.6
    assert "<!-- STATE" in body
    assert "wave_completed: 1" in body
    assert "FINDINGS_WAVE_1" in body
    assert journal.parse_state_blocks(body)[-1]["leads_pending"] == [
        "https://example.com/a",
        "https://example.com/b",
    ]
    assert journal.parse_state_blocks(body)[-1]["gaps"] == ["topic X needs more sources"]
    assert loaded[1][0]["claim"] == "PostgreSQL uses MVCC"


def test_journal_resolve_rejects_paths_outside_research_dir(journal_dir, tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text("---\nquery: outside\n---\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        journal._resolve_path(str(outside))


def test_journal_delete_requires_confirmation(journal_dir, capsys, monkeypatch):
    created = _cmd_save(
        argparse.Namespace(
            query="Delete confirmation test",
            tier="quick",
            mode="investigate",
            status="In Progress",
            findings=None,
            update=None,
            wave=None,
            state=None,
        ),
        capsys,
    )
    path = Path(created["path"])

    monkeypatch.setattr("builtins.input", lambda: "no")
    with pytest.raises(SystemExit):
        journal.cmd_delete(argparse.Namespace(target=str(path), force=False))
    assert path.exists()

    journal.cmd_delete(argparse.Namespace(target=str(path), force=True))
    json.loads(capsys.readouterr().out)
    assert not path.exists()
