from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_candidate_bun_promotion_test",
        ROOT / "scripts" / "promote_candidate_bun_runtime.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _package(prefix: Path, name: str, version: str, bin_name: str) -> None:
    root = prefix / "node_modules" / name
    root.mkdir(parents=True)
    (root / "dist").mkdir()
    (root / "dist" / "cli.js").write_text("#!/usr/bin/env node\n", encoding="utf-8")
    (root / "package.json").write_text(
        json.dumps({"name": name, "version": version, "bin": {bin_name: "dist/cli.js"}}) + "\n",
        encoding="utf-8",
    )


def test_validate_prefix_requires_exact_versions_and_bins(tmp_path: Path) -> None:
    module = _module()
    prefix = tmp_path / "prefix"
    prefix.mkdir()
    (prefix / "package.json").write_text(
        json.dumps({"dependencies": {"@example/one": "1.0.0"}}) + "\n",
        encoding="utf-8",
    )
    (prefix / "bun.lock").write_text("lockfileVersion = 1\n", encoding="utf-8")
    _package(prefix, "@example/one", "1.0.0", "one")

    assert module.validate_prefix(prefix, {"@example/one": "1.0.0"}) == {
        "one": prefix / "node_modules" / "@example/one" / "dist" / "cli.js"
    }
    with pytest.raises(ValueError, match="version mismatch"):
        module.validate_prefix(prefix, {"@example/one": "2.0.0"})
