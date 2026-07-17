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


def test_validate_prefix_uses_root_inspector_cli_for_public_aliases(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "node_modules" / "@modelcontextprotocol" / "inspector"
    cli = package / "cli" / "build" / "cli.js"
    cli.parent.mkdir(parents=True)
    cli.write_text("#!/usr/bin/env node\n")
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"@modelcontextprotocol/inspector":"0.22.0"}}\n'
    )
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "packages": {
                    "node_modules/@modelcontextprotocol/inspector": {
                        "version": "0.22.0",
                        "integrity": "sha512:test",
                    }
                }
            }
        )
    )
    (package / "package.json").write_text(
        '{"name":"@modelcontextprotocol/inspector","version":"0.22.0",'
        '"bin":{"mcp-inspector":"cli/build/cli.js"}}\n'
    )

    bins = module.validate_prefix(
        tmp_path,
        {"@modelcontextprotocol/inspector": "0.22.0"},
    )

    assert bins["mcp-inspector"] == cli
    assert bins["mcp-inspector-cli"] == cli


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


def test_inspector_alias_repair_is_cwd_independent_and_reversible(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _module()
    runtime_root = tmp_path / "runtime"
    package = runtime_root / "node_modules" / "@modelcontextprotocol" / "inspector"
    target = package / "cli" / "build" / "cli.js"
    target.parent.mkdir(parents=True)
    target.write_text("#!/usr/bin/env node\n")
    (package / "package.json").write_text('{"name":"@modelcontextprotocol/inspector"}\n')
    dependency = runtime_root / "node_modules" / "@modelcontextprotocol" / "inspector-cli"
    dependency.mkdir(parents=True)
    dependency_target = dependency / "cli.js"
    dependency_target.write_text("#!/usr/bin/env node\n")
    (runtime_root / "package-lock.json").write_text("{}\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "mcp-inspector").symlink_to(dependency_target)
    (bin_dir / "mcp-inspector-cli").symlink_to(dependency_target)
    state_dir = tmp_path / "receipts"
    monkeypatch.setattr(module, "STATE_DIR", state_dir)

    result = module.repair_inspector_aliases(runtime_root, bin_dir, apply=True)

    assert result["preimage_digest"] == result["rollback_digest"]
    assert (bin_dir / "mcp-inspector").resolve() == target
    assert (bin_dir / "mcp-inspector-cli").resolve() == target
    assert (package / "cli" / "package.json").is_symlink()
    assert (package / "cli" / "package.json").resolve() == package / "package.json"
