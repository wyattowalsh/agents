from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "skill-package-manifest-enricher"
SCRIPT = SKILL_DIR / "scripts" / "enrich_manifest.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("skill_package_manifest_enricher_script", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ENRICHER = _load_script()


def _write_skill(
    root: Path,
    *,
    name: str = "sample-skill",
    frontmatter: str | None = None,
    eval_count: int = 0,
) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        frontmatter
        or f"""---
name: {name}
description: >-
  Folded package
  description.
compatibility: "Python: 3.11+"
metadata:
  owner: test
---
# Sample Skill
""",
        encoding="utf-8",
    )
    if eval_count:
        evals_dir = skill_dir / "evals"
        evals_dir.mkdir()
        evals_dir.joinpath("evals.json").write_text(
            json.dumps({"skill_name": name, "evals": [{"id": f"case-{index}"} for index in range(eval_count)]}),
            encoding="utf-8",
        )
    return skill_dir


def _write_json(path: Path, payload: dict[str, Any]) -> bytes:
    raw = json.dumps(payload, indent=2).encode()
    path.write_bytes(raw)
    return raw


def test_frontmatter_uses_safe_yaml_scalar_list_and_mapping_semantics() -> None:
    parsed = ENRICHER._parse_frontmatter(
        """---
name: "quoted-name"
description: >-
  folded
  description
literal: |-
  line one
  ---
  line two
keep: |+
  final newline

tags:
  - one
  - "two: quoted"
metadata:
  nested:
    enabled: true
---
# Body
"""
    )

    assert parsed["name"] == "quoted-name"
    assert parsed["description"] == "folded description"
    assert parsed["literal"] == "line one\n---\nline two"
    assert parsed["keep"] == "final newline\n\n"
    assert parsed["tags"] == ["one", "two: quoted"]
    assert parsed["metadata"] == {"nested": {"enabled": True}}


def test_malformed_yaml_fails_before_apply_write(tmp_path: Path) -> None:
    skill_dir = _write_skill(
        tmp_path,
        frontmatter="""---
name: sample-skill
description: [unterminated
---
# Broken
""",
    )
    output = skill_dir / "manifest.enriched.json"
    original = b'{"upstream":"unchanged"}\n'
    output.write_bytes(original)

    with pytest.raises(ENRICHER.EnrichmentError, match=r"invalid SKILL.md YAML frontmatter"):
        ENRICHER.enrich_manifest(skill_dir, apply=True)

    assert output.read_bytes() == original


def test_catalog_targets_are_derived_and_bound_while_upstream_keys_survive(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path, eval_count=2)
    catalog = tmp_path / "catalog.json"
    raw = _write_json(
        catalog,
        {
            "customSkillIndex": [
                {"name": "sample-skill", "targetAgents": ["codex", "cursor", "codex"]},
            ],
            "allSkillIndex": [
                {"name": "sample-skill", "targetAgents": ["codex", "cursor"]},
            ],
        },
    )
    upstream = tmp_path / "manifest.json"
    _write_json(upstream, {"upstream_key": {"preserve": True}, "harness_targets": ["stale"]})
    output = tmp_path / "result" / "manifest.enriched.json"

    result = ENRICHER.enrich_manifest(
        skill_dir,
        apply=True,
        catalog_metadata=catalog,
        catalog_source_label="evidence/catalog.json",
        upstream_manifest=upstream,
        output_path=output,
    )
    manifest = result["manifest"]

    assert result["applied"] is True
    assert output.is_file()
    assert manifest["upstream_key"] == {"preserve": True}
    assert manifest["description"] == "Folded package description."
    assert manifest["compatibility_notes"] == "Python: 3.11+"
    assert manifest["eval_case_count"] == 2
    assert manifest["harness_targets"] == ["codex", "cursor"]
    assert manifest["harness_targets_status"] == "catalog"
    assert manifest["harness_targets_source"] == "evidence/catalog.json"
    assert manifest["harness_targets_source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert isinstance(manifest["packaged_at"], str)
    assert json.loads(output.read_text(encoding="utf-8")) == manifest


def test_sync_rows_are_fallback_when_catalog_has_no_selected_skill(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path)
    catalog = tmp_path / "catalog.json"
    _write_json(catalog, {"customSkillIndex": [{"name": "other", "targetAgents": ["cursor"]}]})
    sync = tmp_path / "sync.json"
    raw = _write_json(
        sync,
        {
            "skills": [
                {"name": "sample-skill", "target_agents": ["opencode", "claude-code"]},
            ]
        },
    )

    manifest = ENRICHER.enrich_manifest(
        skill_dir,
        apply=False,
        catalog_metadata=catalog,
        sync_metadata=sync,
    )["manifest"]

    assert manifest["harness_targets"] == ["opencode", "claude-code"]
    assert manifest["harness_targets_status"] == "sync"
    assert manifest["harness_targets_source"] == "sync/sync.json"
    assert manifest["harness_targets_source_sha256"] == hashlib.sha256(raw).hexdigest()


def test_structured_sync_report_derives_only_active_skill_agents(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path)
    sync = tmp_path / "sync-report.json"
    _write_json(
        sync,
        {
            "agents": [
                {"agent": "codex", "already_present": ["sample-skill [repo-owned]"], "skipped": []},
                {"agent": "cursor", "missing": [{"name": "sample-skill"}], "skipped": []},
                {"agent": "opencode", "missing": [], "skipped": ["sample-skill [repo-owned]"]},
            ]
        },
    )

    manifest = ENRICHER.enrich_manifest(skill_dir, apply=False, sync_metadata=sync)["manifest"]

    assert manifest["harness_targets"] == ["codex", "cursor"]
    assert manifest["harness_targets_status"] == "sync"


def test_missing_target_metadata_is_honestly_unavailable(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path)

    manifest = ENRICHER.enrich_manifest(skill_dir, apply=False)["manifest"]

    assert manifest["harness_targets"] == []
    assert manifest["harness_targets_status"] == "unavailable"
    assert manifest["harness_targets_source"] == "unavailable"
    assert manifest["harness_targets_source_sha256"] == ""


def test_preview_never_mutates_existing_sidecar(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path)
    output = skill_dir / "manifest.enriched.json"
    original = b'{\n  "upstream": "keep"\n}\n'
    output.write_bytes(original)

    result = ENRICHER.enrich_manifest(skill_dir, apply=False)

    assert result["applied"] is False
    assert result["manifest"]["upstream"] == "keep"
    assert output.read_bytes() == original
    assert "packaged_at" not in result["manifest"]


def test_absolute_metadata_path_never_becomes_manifest_source_label(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path)
    catalog = tmp_path / "private" / "catalog.json"
    catalog.parent.mkdir()
    _write_json(
        catalog,
        {"customSkillIndex": [{"name": "sample-skill", "targetAgents": ["codex"]}]},
    )

    manifest = ENRICHER.enrich_manifest(
        skill_dir,
        apply=False,
        catalog_metadata=catalog.resolve(),
    )["manifest"]
    source = manifest["harness_targets_source"]

    assert source == "catalog/catalog.json"
    assert not Path(source).is_absolute()
    assert str(tmp_path) not in source


def test_unsafe_explicit_source_label_is_rejected_before_write(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path)
    catalog = tmp_path / "catalog.json"
    _write_json(
        catalog,
        {"customSkillIndex": [{"name": "sample-skill", "targetAgents": ["codex"]}]},
    )

    with pytest.raises(ENRICHER.EnrichmentError, match="portable relative path"):
        ENRICHER.enrich_manifest(
            skill_dir,
            apply=True,
            catalog_metadata=catalog,
            catalog_source_label=str(catalog.resolve()),
        )

    assert not (skill_dir / "manifest.enriched.json").exists()


def test_installed_copy_runs_without_repo_imports_or_repo_metadata(tmp_path: Path) -> None:
    source_tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported_roots = {
        node.module.partition(".")[0]
        for node in ast.walk(source_tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    imported_roots.update(
        alias.name.partition(".")[0]
        for node in ast.walk(source_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert "wagents" not in imported_roots

    installed_script = tmp_path / "installed" / "skill-package-manifest-enricher" / "scripts" / SCRIPT.name
    installed_script.parent.mkdir(parents=True)
    shutil.copy2(SCRIPT, installed_script)
    target = _write_skill(tmp_path / "targets")
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [
            sys.executable,
            str(installed_script),
            "--skill-dir",
            str(target),
            "--dry-run",
        ],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["manifest"]["harness_targets"] == []
    assert payload["manifest"]["harness_targets_status"] == "unavailable"
    assert not (target / "manifest.enriched.json").exists()


def test_cli_apply_preserves_upstream_and_cli_dry_run_does_not_write(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path)
    upstream = tmp_path / "upstream.json"
    _write_json(upstream, {"upstream": ["preserved"]})
    output = tmp_path / "enriched.json"

    preview = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--skill-dir",
            str(skill_dir),
            "--manifest",
            str(upstream),
            "--output",
            str(output),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert preview.returncode == 0, preview.stderr or preview.stdout
    assert not output.exists()

    applied = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--skill-dir",
            str(skill_dir),
            "--manifest",
            str(upstream),
            "--output",
            str(output),
            "--apply",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert applied.returncode == 0, applied.stderr or applied.stdout
    assert json.loads(output.read_text(encoding="utf-8"))["upstream"] == ["preserved"]
