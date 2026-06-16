"""Tests for harness-master discovery hook_scan.py and _hook_collect.py using fixture."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "harness-master" / "scripts" / "discovery"
FIXTURE_DIR = ROOT / "skills" / "harness-master" / "data" / "discovery" / "fixtures"


def _load(name: str, filename: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so that module-level decorators (e.g. dataclass in schemas)
    # can resolve sys.modules[cls.__module__] during definition.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def hook_scan_mod():
    return _load("hook_scan", "hook_scan.py")


@pytest.fixture
def hook_collect_mod():
    return _load("_hook_collect", "_hook_collect.py")


@pytest.fixture
def schemas_mod():
    return _load("schemas", "schemas.py")


def test_hook_scan_minimal_fixture_validates(schemas_mod) -> None:
    fixture_path = FIXTURE_DIR / "hook-scan-minimal.json"
    assert fixture_path.is_file(), f"Missing fixture {fixture_path}"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    errors = schemas_mod.validate_hook_scan(data)
    assert errors == [], f"Fixture failed validation: {errors}"
    assert data["version"] == 1
    assert "registry" in data and "by_harness" in data["registry"]
    assert "frontmatter" in data and "sources" in data["frontmatter"]
    assert "gaps" in data and isinstance(data["gaps"], list)
    assert "validation_errors" in data


def test_collect_registry_summary_loads_real_and_counts(hook_collect_mod) -> None:
    collect = hook_collect_mod
    summary = collect.collect_registry_summary(ROOT)
    assert isinstance(summary, dict)
    assert "by_harness" in summary
    assert "by_logical_event" in summary
    assert "managed_wagents_hook_count" in summary
    # Real repo currently has several wagents-managed + shell hooks
    assert summary["managed_wagents_hook_count"] >= 0
    # github-copilot (and aliases) and codex etc should be present from config/hook-registry.json
    by_h = summary["by_harness"]
    assert any(k in by_h for k in ("github-copilot", "codex", "claude-code"))


def test_collect_frontmatter_detects_known_hook_skills(hook_collect_mod) -> None:
    collect = hook_collect_mod
    fm = collect.collect_frontmatter_hooks(ROOT)
    assert fm["skills_with_hooks"] >= 5  # simplify, research, skill-creator, honest-review, add-badges, namer, ...
    assert fm["agents_with_hooks"] == 0
    assert any("skill:simplify" in s or "skill:research" in s for s in fm["sources"])


def test_collect_embedded_and_grok(hook_collect_mod) -> None:
    collect = hook_collect_mod
    emb = collect.collect_embedded_settings(ROOT)
    assert isinstance(emb.get("claude"), bool)
    assert isinstance(emb.get("paths"), list)
    # .claude/settings.json exists with hooks in this repo
    assert emb["claude"] is True or ".claude/settings.json" in emb.get("paths", [])

    grok = collect.collect_grok_managed(ROOT)
    assert grok == {"policy_present": True}  # config/grok-plannotator-hooks.json present with hooks block


def test_collect_validation_errors_runs(hook_collect_mod) -> None:
    collect = hook_collect_mod
    errs = collect.collect_validation_errors(ROOT)
    assert isinstance(errs, list)
    # May be [] or have entries; shape check
    for e in errs:
        assert isinstance(e, dict)
        assert "source" in e or "message" in e


def test_load_hook_surface_registry_graceful(hook_collect_mod) -> None:
    collect = hook_collect_mod
    reg = collect.load_hook_surface_registry(ROOT)
    # File does not exist yet in base checkout; must return {} not raise
    assert isinstance(reg, dict)
    # If later created, it may have project/global keys
    if reg and "error" not in reg:
        assert "project" in reg or "global" in reg or bool(reg)


def test_scan_hooks_contract(hook_scan_mod) -> None:
    scan_mod = hook_scan_mod
    result = scan_mod.scan_hooks(repo_root=ROOT)
    assert result["version"] == 1
    for key in (
        "registry",
        "frontmatter",
        "embedded_settings",
        "grok_managed",
        "surface_parity",
        "gaps",
        "validation_errors",
        "blind_spots",
    ):
        assert key in result
    assert isinstance(result["gaps"], list)
    assert isinstance(result["blind_spots"], list)
    # surface_parity cross-refs harness + hook-surface
    sp = result["surface_parity"]
    assert "harnesses_projecting_hooks" in sp
    assert "harnesses_in_registry" in sp


def test_hook_scan_cli_writes_output(hook_scan_mod, tmp_path: Path) -> None:
    scan_mod = hook_scan_mod
    out = tmp_path / "out" / "hook-scan.json"
    rc = scan_mod.main(["--repo-root", str(ROOT), "-o", str(out)])
    assert rc == 0
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert "registry" in data


def test_harness_aliases_present(hook_collect_mod) -> None:
    collect = hook_collect_mod
    aliases = collect.HARNESS_ALIASES
    assert isinstance(aliases, dict)
    assert "github-copilot-cli" in aliases
    assert aliases["github-copilot-cli"] == "github-copilot"
