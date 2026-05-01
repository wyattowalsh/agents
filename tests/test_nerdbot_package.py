"""Package-level tests for the Nerdbot CLI shell."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

NERDBOT_ROOT = Path(__file__).resolve().parents[1] / "skills" / "nerdbot"
SRC_DIR = NERDBOT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nerdbot.cli import build_parser, build_plan_payload, main  # noqa: E402
from nerdbot.contracts import (  # noqa: E402
    CLAIM_RECORD_FIELDS,
    GENERATED_ARTIFACTS,
    GRAPH_EDGE_FIELDS,
    MODES,
    OPERATION_JOURNAL_PATH,
    QUERY_RESULT_FIELDS,
    REFERENCE_DOCS,
    REQUIRED_EXPANSION_LANES,
    REVIEW_QUEUE_PATH,
    REVIEW_STATUSES,
    SCHEMA_ENTITIES,
    SOURCE_RECORD_FIELDS,
    VERSION,
    WATCH_EVENT_FIELDS,
)
from nerdbot.evidence import ClaimRecord, ReviewItem, apply_confidence_cap  # noqa: E402
from nerdbot.graph import extract_edges  # noqa: E402
from nerdbot.replay import dry_run_replay  # noqa: E402
from nerdbot.research import ResearchJournalEntry, should_ingest_from_research  # noqa: E402
from nerdbot.retrieval import query_lexical  # noqa: E402
from nerdbot.sources import build_source_record, pointer_stub_text  # noqa: E402
from nerdbot.watch import classify_watch_event  # noqa: E402


def _venv_executable(venv_dir: Path, name: str) -> Path:
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    suffix = ".exe" if sys.platform == "win32" else ""
    executable = name if name.endswith(suffix) else f"{name}{suffix}"

    return venv_dir / bin_dir / executable


def test_parser_exposes_baseline_commands() -> None:
    parser = build_parser()

    help_text = parser.format_help()

    for command in ("bootstrap", "inventory", "lint", "plan", "modes"):
        assert command in help_text


def test_no_args_renders_mode_gallery(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main([])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Nerdbot Workflow Gallery" in captured.out
    assert "Safe starts:" in captured.out


def test_plan_payload_keeps_required_expansion_lanes_visible() -> None:
    payload = build_plan_payload("ingest", "./incoming/source.pdf")

    for lane in REQUIRED_EXPANSION_LANES:
        assert lane in payload["expansion_lanes_not_deferred"]


def test_contract_reference_docs_exist() -> None:
    for rel_path in REFERENCE_DOCS:
        assert (NERDBOT_ROOT / "references" / rel_path).is_file(), rel_path


def test_plan_command_is_read_only_and_successful(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["plan", "--mode", "query", "--target", ".", "--compact"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["mode"] == "query"
    assert payload["read_only_default"] is True


def test_plan_payload_includes_argv_safe_next_command() -> None:
    payload = build_plan_payload("create", "./kb with spaces")

    assert payload["suggested_next_command"] == "nerdbot bootstrap --root 'kb with spaces' --dry-run"
    assert payload["suggested_next_argv"] == ["nerdbot", "bootstrap", "--root", "kb with spaces", "--dry-run"]


def test_plan_guide_is_human_scannable(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["plan", "--mode", "query", "--target", ".", "--view", "guide"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[ask] Nerdbot query plan" in captured.out
    assert "Gate path:" in captured.out
    assert "Safety promises:" in captured.out


def test_modes_gallery_lists_all_modes(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["modes"])

    captured = capsys.readouterr()

    assert exit_code == 0
    for mode in MODES:
        assert mode in captured.out


def test_modes_command_is_documented_in_compatibility_map() -> None:
    compatibility_doc = (NERDBOT_ROOT / "references" / "current-state-and-compatibility.md").read_text(encoding="utf-8")

    assert "`nerdbot modes`" in compatibility_doc
    assert f"package version `{VERSION}`" in compatibility_doc


def test_all_modes_are_available_to_argparse() -> None:
    parser = build_parser()

    for mode in MODES:
        parsed = parser.parse_args(["plan", "--mode", mode])
        assert parsed.mode == mode


def test_cli_error_paths_emit_json_objects(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["inventory", "--root", str(NERDBOT_ROOT / "missing-kb"), "--compact"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert isinstance(payload, dict)
    assert payload["command"] == "inventory"
    assert payload["status"] == "error"
    assert payload["errors"]


def test_cli_wrappers_delegate_to_legacy_scripts(tmp_path) -> None:
    root = tmp_path / "kb"

    assert main(["bootstrap", "--root", str(root), "--dry-run", "--compact"]) == 0
    assert main(["bootstrap", "--root", str(root), "--compact"]) == 0
    assert main(["inventory", "--root", str(root), "--compact"]) == 0
    assert main(["lint", "--root", str(root), "--fail-on", "none", "--compact"]) == 0


def test_schema_contract_entities_are_documented() -> None:
    schema_doc = (NERDBOT_ROOT / "references" / "schema-contracts.md").read_text(encoding="utf-8")

    for entity, fields in SCHEMA_ENTITIES.items():
        pattern = rf"\| {re.escape(entity)} \| ([^|]+) \|"
        match = re.search(pattern, schema_doc)
        assert match, entity
        for field in fields:
            assert field in match.group(1), f"{entity}: {field}"


@pytest.mark.parametrize(
    ("extra", "dependency"),
    [
        ("crawl", "crawlee"),
        ("docs", "docling-slim"),
        ("vlm", "docling"),
    ],
)
def test_optional_extras_match_documented_lanes(extra: str, dependency: str) -> None:
    pyproject = (NERDBOT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    extra_block = re.search(rf"{extra} = \[\n(?P<body>.*?)\n\]", pyproject, re.DOTALL)

    assert extra_block, extra
    assert dependency in extra_block.group("body")


def test_source_record_contract_and_pointer_stub() -> None:
    record = build_source_record("https://example.com/report.pdf", capture_method="static", content=b"hello")

    payload = record.to_dict()
    stub = pointer_stub_text(record, "private source")

    assert tuple(payload) == SOURCE_RECORD_FIELDS
    assert payload["checksum"]
    assert record.source_id in stub
    assert "Pointer reason: private source" in stub


def test_evidence_review_and_confidence_contracts() -> None:
    claim = ClaimRecord(
        claim_id="claim-1",
        claim="Nerdbot keeps raw sources append-only.",
        wiki_path="wiki/index.md",
        source_id="src-1",
        evidence_path="raw/sources/a.md",
        evidence_type="source",
        freshness_class="fast",
        confidence=apply_confidence_cap(0.95, "fast"),
    )
    review_item = ReviewItem("rev-1", "query", "wiki/index.md", "medium", "Save back answer gap")

    assert tuple(claim.to_dict()) == CLAIM_RECORD_FIELDS
    assert claim.confidence == 0.55
    assert review_item.status in REVIEW_STATUSES


def test_retrieval_graph_watch_replay_and_research_contracts(tmp_path: Path) -> None:
    (tmp_path / "wiki").mkdir()
    (tmp_path / "indexes").mkdir()
    (tmp_path / "wiki" / "index.md").write_text(
        "# Alpha\n\nSee [[wiki/beta]] and [source](../indexes/source-map.md).\n",
        encoding="utf-8",
    )
    (tmp_path / "indexes" / "source-map.md").write_text("# Source Map\n\nAlpha source coverage.\n", encoding="utf-8")

    results = query_lexical(tmp_path, "alpha source")
    edges = extract_edges("wiki/index.md", (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8"))
    watch_decision = classify_watch_event(".obsidian/workspace.json", "modified")
    replay = dry_run_replay("op-1", ["wiki/index.md", "activity/log.md"], {"wiki/index.md"})
    journal = ResearchJournalEntry("journal-only", "What changed?", ("https://example.com",), "record-only")

    assert tuple(results[0].to_dict()) == QUERY_RESULT_FIELDS
    assert tuple(edges[0].to_dict()) == GRAPH_EDGE_FIELDS
    assert tuple(watch_decision.to_dict()) == WATCH_EVENT_FIELDS
    assert replay.status == "review-needed"
    assert should_ingest_from_research(journal.policy, approved=False) is False
    assert OPERATION_JOURNAL_PATH == "activity/operations.jsonl"
    assert REVIEW_QUEUE_PATH == "indexes/review-queue.md"
    assert GENERATED_ARTIFACTS["fts_index"].startswith("indexes/generated/")


def test_installed_wheel_smoke_exposes_console_and_legacy_scripts(tmp_path: Path) -> None:
    expected_assets = sorted(path.name for path in (NERDBOT_ROOT / "assets").iterdir() if path.is_file())
    expected_modules = sorted(
        path.stem
        for path in (NERDBOT_ROOT / "src" / "nerdbot").glob("*.py")
        if path.stem != "__init__" and not path.stem.startswith("_")
    )
    expected_scripts = sorted(path.name for path in (NERDBOT_ROOT / "scripts").glob("kb_*.py"))

    dist_dir = tmp_path / "dist"
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dist_dir), str(NERDBOT_ROOT)],
        check=True,
        text=True,
        capture_output=True,
    )
    wheel = next(dist_dir.glob("nerdbot-*.whl"))
    venv_dir = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    python = _venv_executable(venv_dir, "python")
    nerdbot = _venv_executable(venv_dir, "nerdbot")
    subprocess.run([str(python), "-m", "pip", "install", str(wheel)], check=True, stdout=subprocess.PIPE)
    venv_env = os.environ.copy()
    venv_env.pop("PYTHONPATH", None)

    help_run = subprocess.run([str(nerdbot), "--help"], check=True, text=True, stdout=subprocess.PIPE, env=venv_env)
    modes_run = subprocess.run(
        [str(nerdbot), "modes", "--view", "json", "--compact"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        env=venv_env,
    )
    plan_run = subprocess.run(
        [str(nerdbot), "plan", "--mode", "query", "--target", str(tmp_path), "--compact"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        env=venv_env,
    )
    import_run = subprocess.run(
        [
            str(python),
            "-c",
            textwrap.dedent(
                f"""
                import importlib
                import json
                import pkgutil
                from importlib.resources import files

                import nerdbot
                from nerdbot.contracts import REFERENCE_DOCS
                from nerdbot.legacy import kb_bootstrap, kb_inventory, kb_lint

                expected_assets = {json.dumps(expected_assets)}
                expected_modules = {json.dumps(expected_modules)}
                expected_references = {json.dumps(sorted(REFERENCE_DOCS))}
                expected_scripts = {json.dumps(expected_scripts)}

                public_modules = sorted(
                    module.name for module in pkgutil.iter_modules(nerdbot.__path__) if not module.name.startswith("_")
                )
                if public_modules != expected_modules:
                    raise AssertionError(f"public modules mismatch: {{public_modules}} != {{expected_modules}}")

                for module_name in public_modules:
                    importlib.import_module(f"nerdbot.{{module_name}}")

                package_root = files("nerdbot")
                for asset in expected_assets:
                    if not (package_root / "assets" / asset).is_file():
                        raise AssertionError(f"missing packaged asset: {{asset}}")
                for script in expected_scripts:
                    if not (package_root / "scripts" / script).is_file():
                        raise AssertionError(f"missing packaged script: {{script}}")
                for reference in expected_references:
                    if not (package_root / "references" / reference).is_file():
                        raise AssertionError(f"missing packaged reference: {{reference}}")

                kb_bootstrap(); kb_inventory(); kb_lint()
                """
            ),
        ],
        check=True,
        env=venv_env,
    )

    assert "bootstrap" in help_run.stdout
    assert json.loads(modes_run.stdout)["modes"]
    assert json.loads(plan_run.stdout)["suggested_next_argv"][0] == "nerdbot"
    assert import_run.returncode == 0
