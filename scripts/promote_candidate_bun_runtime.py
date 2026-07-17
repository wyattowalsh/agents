#!/usr/bin/env python3
"""Promote the audited candidate Bun prefix with an exact rollback rehearsal."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ACTIVATION_SCRIPT = ROOT / "scripts" / "record_candidate_runtime_activation.py"
NODE_PROMOTION_SCRIPT = ROOT / "scripts" / "promote_candidate_node_runtime.py"
DEFAULT_RUNTIME_ROOT = Path.home() / ".local" / "share" / "wagents" / "candidate-runtime" / "bun"
DEFAULT_BIN_DIR = Path.home() / ".local" / "bin"
STATE_DIR = Path.home() / ".local" / "share" / "wagents" / "candidate-runtime" / "receipts"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def expected_packages() -> dict[str, str]:
    activation = load_module(ACTIVATION_SCRIPT, "_candidate_bun_activation")
    result: dict[str, str] = {}
    for rows in activation.runtime_specs().values():
        for seed in rows:
            if seed.get("package_manager") != "bun" or seed.get("kind") == "plugin":
                continue
            name = str(seed.get("package_name") or "")
            version = str(seed.get("version") or "")
            if name in result and result[name] != version:
                raise ValueError(f"conflicting target versions for {name}")
            result[name] = version
    return result


def validate_prefix(prefix: Path, expected: dict[str, str]) -> dict[str, Path]:
    lock_path = prefix / "bun.lock"
    package_path = prefix / "package.json"
    if not lock_path.is_file() or not package_path.is_file():
        raise ValueError("candidate Bun prefix requires package.json and bun.lock")
    declared = json.loads(package_path.read_text(encoding="utf-8")).get("dependencies", {})
    if set(declared) != set(expected):
        raise ValueError("candidate Bun prefix dependency set does not match runtime targets")

    bins: dict[str, Path] = {}
    for name, version in sorted(expected.items()):
        package_root = prefix / "node_modules" / name
        manifest_path = package_root / "package.json"
        if not manifest_path.is_file():
            raise ValueError(f"missing installed package: {name}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("version") != version:
            raise ValueError(f"version mismatch for {name}")
        package_bins = manifest.get("bin") or {}
        if isinstance(package_bins, str):
            package_bins = {name.rsplit("/", 1)[-1]: package_bins}
        for bin_name, relative in package_bins.items():
            target = package_root / str(relative)
            if not target.is_file():
                raise ValueError(f"missing bin target for {name}: {bin_name}")
            if bin_name in bins and bins[bin_name] != target:
                raise ValueError(f"conflicting bin name: {bin_name}")
            bins[str(bin_name)] = target
    return bins


def surface_digest(runtime_root: Path, bins: dict[str, dict[str, Any]], node: Any) -> str:
    payload = {
        "runtime_root_exists": runtime_root.exists(),
        "bun_lock_sha256": (
            node.sha256_file(runtime_root / "bun.lock")
            if (runtime_root / "bun.lock").is_file()
            else None
        ),
        "bins": bins,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME_ROOT)
    parser.add_argument("--bin-dir", type=Path, default=DEFAULT_BIN_DIR)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    node = load_module(NODE_PROMOTION_SCRIPT, "_candidate_bun_node_promotion")
    staging = args.staging.expanduser().resolve()
    runtime_root = args.runtime_root.expanduser().resolve()
    bin_dir = args.bin_dir.expanduser().resolve()
    if runtime_root.exists():
        raise ValueError(f"managed runtime root already exists: {runtime_root}")
    expected = expected_packages()
    targets = validate_prefix(staging, expected)
    relocated_targets = {name: runtime_root / target.relative_to(staging) for name, target in targets.items()}
    preimage = node.snapshot_bins(bin_dir, set(targets))
    preimage_digest = surface_digest(runtime_root, preimage, node)
    preview = {
        "package_count": len(expected),
        "bin_count": len(targets),
        "staging": str(staging),
        "runtime_root": str(runtime_root),
        "preimage_digest": preimage_digest,
    }
    if not args.apply:
        print(json.dumps({"ok": True, "mode": "preview", **preview}, indent=2))
        return 0

    runtime_root.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(staging, runtime_root)
        node.promote_bins(bin_dir, relocated_targets, preimage)
        promoted_digest = surface_digest(runtime_root, node.snapshot_bins(bin_dir, set(targets)), node)

        node.restore_bins(bin_dir, preimage)
        os.replace(runtime_root, staging)
        rollback_digest = surface_digest(runtime_root, node.snapshot_bins(bin_dir, set(targets)), node)
        if rollback_digest != preimage_digest:
            raise RuntimeError("rollback rehearsal did not restore the exact preimage")

        os.replace(staging, runtime_root)
        node.promote_bins(bin_dir, relocated_targets, preimage)
        final_digest = surface_digest(runtime_root, node.snapshot_bins(bin_dir, set(targets)), node)
        if final_digest != promoted_digest:
            raise RuntimeError("final promotion differs from the rehearsed promotion")
    except Exception:
        node.restore_bins(bin_dir, preimage)
        if runtime_root.exists() and not staging.exists():
            os.replace(runtime_root, staging)
        raise

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "version": 1,
        "recorded_at": datetime.now(UTC).isoformat(),
        **preview,
        "rollback_digest": rollback_digest,
        "promoted_surface_digest": final_digest,
        "promoted_bins": sorted(targets),
    }
    state_path = STATE_DIR / "candidate-bun-runtime-latest.json"
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "mode": "applied", "state_path": str(state_path), **state}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
