from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_promote_candidate_node_runtime",
        ROOT / "scripts" / "promote_candidate_node_runtime.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_validate_prefix_requires_exact_versions_and_integrity(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "node_modules" / "example"
    package.mkdir(parents=True)
    (tmp_path / "package.json").write_text('{"dependencies":{"example":"1.0.0"}}\n')
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "packages": {
                    "node_modules/example": {
                        "version": "1.0.0",
                        "integrity": "sha512:test",
                    }
                }
            }
        )
    )
    (package / "package.json").write_text(
        '{"name":"example","version":"1.0.0","bin":{"example":"cli.js"}}\n'
    )
    (package / "cli.js").write_text("#!/usr/bin/env node\n")

    bins = module.validate_prefix(tmp_path, {"example": "1.0.0"})

    assert bins == {"example": package / "cli.js"}


def test_symlink_promotion_and_restore_round_trip(tmp_path: Path) -> None:
    module = _module()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    old = tmp_path / "old"
    new = tmp_path / "new"
    old.write_text("old\n")
    new.write_text("new\n")
    (bin_dir / "tool").symlink_to(old)
    preimage = module.snapshot_bins(bin_dir, {"tool"})

    module.promote_bins(bin_dir, {"tool": new}, preimage)
    assert (bin_dir / "tool").resolve() == new

    module.restore_bins(bin_dir, preimage)
    assert (bin_dir / "tool").resolve() == old
