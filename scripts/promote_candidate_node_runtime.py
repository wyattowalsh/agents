#!/usr/bin/env python3
"""Promote an audited candidate Node prefix with an exact rollback rehearsal."""

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
DEFAULT_RUNTIME_ROOT = Path.home() / ".local" / "share" / "wagents" / "candidate-runtime" / "npm"
DEFAULT_BIN_DIR = Path.home() / ".local" / "bin"
STATE_DIR = Path.home() / ".local" / "share" / "wagents" / "candidate-runtime" / "receipts"
PRESERVED_REGULAR_BINS = {"gws"}


def activation_module():
    spec = importlib.util.spec_from_file_location("_candidate_node_activation", ACTIVATION_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ACTIVATION_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_packages() -> dict[str, str]:
    module = activation_module()
    result: dict[str, str] = {}
    for rows in module.runtime_specs().values():
        for seed in rows:
            if seed.get("package_manager") != "npm" or seed.get("kind") == "plugin":
                continue
            name = str(seed.get("package_name") or "")
            version = str(seed.get("version") or "")
            if name in result and result[name] != version:
                raise ValueError(f"conflicting target versions for {name}")
            result[name] = version
    return result


def validate_prefix(prefix: Path, expected: dict[str, str]) -> dict[str, Path]:
    lock_path = prefix / "package-lock.json"
    package_path = prefix / "package.json"
    if not lock_path.is_file() or not package_path.is_file():
        raise ValueError("candidate prefix requires package.json and package-lock.json")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    declared = json.loads(package_path.read_text(encoding="utf-8")).get("dependencies", {})
    if set(declared) != set(expected):
        raise ValueError("candidate prefix dependency set does not match runtime targets")

    bins: dict[str, Path] = {}
    for name, version in sorted(expected.items()):
        package_root = prefix / "node_modules" / name
        manifest_path = package_root / "package.json"
        lock_row = lock.get("packages", {}).get(f"node_modules/{name}", {})
        if not manifest_path.is_file():
            raise ValueError(f"missing installed package: {name}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("version") != version or lock_row.get("version") != version:
            raise ValueError(f"version mismatch for {name}")
        if not lock_row.get("integrity"):
            raise ValueError(f"missing lock integrity for {name}")
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
    if "@modelcontextprotocol/inspector" in expected:
        inspector_cli = (
            prefix
            / "node_modules"
            / "@modelcontextprotocol"
            / "inspector"
            / "cli"
            / "build"
            / "cli.js"
        )
        if not inspector_cli.is_file():
            raise ValueError("MCP Inspector root-package CLI is missing")
        bins["mcp-inspector"] = inspector_cli
        bins["mcp-inspector-cli"] = inspector_cli
    return bins


def snapshot_bins(bin_dir: Path, names: set[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name in sorted(names):
        path = bin_dir / name
        if path.is_symlink():
            result[name] = {"kind": "symlink", "target": os.readlink(path)}
        elif path.is_file():
            result[name] = {
                "kind": "file",
                "sha256": sha256_file(path),
                "mode": path.stat().st_mode & 0o777,
            }
        elif path.exists():
            raise ValueError(f"unsupported preimage at {path}")
        else:
            result[name] = {"kind": "missing"}
    return result


def surface_digest(runtime_root: Path, bins: dict[str, dict[str, Any]]) -> str:
    payload = {
        "runtime_root_exists": runtime_root.exists(),
        "package_lock_sha256": (
            sha256_file(runtime_root / "package-lock.json")
            if (runtime_root / "package-lock.json").is_file()
            else None
        ),
        "bins": bins,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic_symlink(target: Path, destination: Path) -> None:
    temporary = destination.with_name(f".{destination.name}.wagents-{os.getpid()}")
    if temporary.exists() or temporary.is_symlink():
        temporary.unlink()
    temporary.symlink_to(target)
    os.replace(temporary, destination)


def promote_bins(bin_dir: Path, targets: dict[str, Path], preimage: dict[str, dict[str, Any]]) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name, target in sorted(targets.items()):
        destination = bin_dir / name
        if preimage[name]["kind"] == "file":
            if name not in PRESERVED_REGULAR_BINS:
                raise ValueError(f"refusing to replace regular executable: {destination}")
            if sha256_file(destination) != preimage[name]["sha256"]:
                raise ValueError(f"preserved executable changed during activation: {destination}")
            continue
        atomic_symlink(target, destination)


def restore_bins(bin_dir: Path, preimage: dict[str, dict[str, Any]]) -> None:
    for name, row in sorted(preimage.items()):
        destination = bin_dir / name
        kind = row["kind"]
        if kind == "file":
            if not destination.is_file() or destination.is_symlink():
                raise ValueError(f"preserved file disappeared during rollback: {destination}")
            if sha256_file(destination) != row["sha256"]:
                raise ValueError(f"preserved file changed during rollback: {destination}")
        elif kind == "symlink":
            temporary = destination.with_name(f".{destination.name}.wagents-restore-{os.getpid()}")
            if temporary.exists() or temporary.is_symlink():
                temporary.unlink()
            temporary.symlink_to(str(row["target"]))
            os.replace(temporary, destination)
        elif kind == "missing":
            if destination.is_symlink() or destination.is_file():
                destination.unlink()
            elif destination.exists():
                raise ValueError(f"rollback found unsupported path: {destination}")


def repair_inspector_aliases(runtime_root: Path, bin_dir: Path, *, apply: bool) -> dict[str, Any]:
    target = (
        runtime_root
        / "node_modules"
        / "@modelcontextprotocol"
        / "inspector"
        / "cli"
        / "build"
        / "cli.js"
    )
    if not target.is_file():
        raise ValueError(f"MCP Inspector root-package CLI is missing: {target}")
    metadata_dir = target.parents[1]
    package_manifest = metadata_dir.parent / "package.json"
    metadata_path = metadata_dir / "package.json"
    if not package_manifest.is_file():
        raise ValueError(f"MCP Inspector package manifest is missing: {package_manifest}")
    if metadata_path.exists() and not metadata_path.is_symlink():
        raise ValueError(f"refusing to replace Inspector metadata file: {metadata_path}")
    targets = {"mcp-inspector": target, "mcp-inspector-cli": target}
    preimage = snapshot_bins(bin_dir, set(targets))
    metadata_preimage = snapshot_bins(metadata_dir, {"package.json"})

    def repair_snapshot() -> dict[str, dict[str, Any]]:
        return {
            **{f"bin:{name}": row for name, row in snapshot_bins(bin_dir, set(targets)).items()},
            "metadata:inspector-cli-package": snapshot_bins(metadata_dir, {"package.json"})[
                "package.json"
            ],
        }

    preimage_digest = surface_digest(runtime_root, repair_snapshot())
    preview = {
        "repair": "mcp-inspector-cli-alias",
        "target": str(target),
        "metadata_compatibility_link": str(metadata_path),
        "preimage_digest": preimage_digest,
    }
    if not apply:
        return {"ok": True, "mode": "preview", **preview}

    try:
        promote_bins(bin_dir, targets, preimage)
        atomic_symlink(Path("..") / "package.json", metadata_path)
        promoted_digest = surface_digest(runtime_root, repair_snapshot())
        restore_bins(bin_dir, preimage)
        restore_bins(metadata_dir, metadata_preimage)
        rollback_digest = surface_digest(runtime_root, repair_snapshot())
        if rollback_digest != preimage_digest:
            raise RuntimeError("Inspector alias rollback did not restore the exact preimage")
        promote_bins(bin_dir, targets, preimage)
        atomic_symlink(Path("..") / "package.json", metadata_path)
        final_digest = surface_digest(runtime_root, repair_snapshot())
        if final_digest != promoted_digest:
            raise RuntimeError("Inspector alias final promotion differs from rehearsal")
    except Exception:
        restore_bins(bin_dir, preimage)
        restore_bins(metadata_dir, metadata_preimage)
        raise

    repair: dict[str, Any] = {
        **preview,
        "rollback_digest": rollback_digest,
        "promoted_surface_digest": final_digest,
        "promoted_bins": sorted(targets),
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    state_path = STATE_DIR / "candidate-node-runtime-latest.json"
    state: dict[str, Any] = (
        json.loads(state_path.read_text(encoding="utf-8"))
        if state_path.is_file()
        else {"version": 1}
    )
    raw_repairs = state.get("post_promotion_repairs", [])
    if not isinstance(raw_repairs, list):
        raise ValueError("Node promotion repairs must be a list")
    repairs: list[dict[str, Any]] = [
        item
        for item in raw_repairs
        if isinstance(item, dict) and item.get("repair") != repair["repair"]
    ]
    repairs.append(repair)
    state["post_promotion_repairs"] = repairs
    raw_bins = state.get("promoted_bins", [])
    if not isinstance(raw_bins, list) or any(not isinstance(item, str) for item in raw_bins):
        raise ValueError("Node promoted bins must be a string list")
    state["promoted_bins"] = sorted({*raw_bins, *targets})
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "mode": "applied", "state_path": str(state_path), **repair}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", type=Path)
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME_ROOT)
    parser.add_argument("--bin-dir", type=Path, default=DEFAULT_BIN_DIR)
    parser.add_argument("--repair-inspector-aliases", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    runtime_root = args.runtime_root.expanduser().resolve()
    bin_dir = args.bin_dir.expanduser().resolve()
    if args.repair_inspector_aliases:
        print(json.dumps(repair_inspector_aliases(runtime_root, bin_dir, apply=args.apply), indent=2))
        return 0
    if args.staging is None:
        parser.error("--staging is required unless --repair-inspector-aliases is used")
    staging = args.staging.expanduser().resolve()
    if runtime_root.exists():
        raise ValueError(f"managed runtime root already exists: {runtime_root}")
    targets = validate_prefix(staging, expected_packages())
    relocated_targets = {
        name: runtime_root / target.relative_to(staging)
        for name, target in targets.items()
    }
    preimage = snapshot_bins(bin_dir, set(targets))
    preimage_digest = surface_digest(runtime_root, preimage)
    preview = {
        "package_count": len(expected_packages()),
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
        promote_bins(bin_dir, relocated_targets, preimage)
        promoted_snapshot = snapshot_bins(bin_dir, set(targets))
        promoted_digest = surface_digest(runtime_root, promoted_snapshot)

        restore_bins(bin_dir, preimage)
        os.replace(runtime_root, staging)
        rollback_snapshot = snapshot_bins(bin_dir, set(targets))
        rollback_digest = surface_digest(runtime_root, rollback_snapshot)
        if rollback_digest != preimage_digest:
            raise RuntimeError("rollback rehearsal did not restore the exact preimage")

        os.replace(staging, runtime_root)
        promote_bins(bin_dir, relocated_targets, preimage)
        final_snapshot = snapshot_bins(bin_dir, set(targets))
        final_digest = surface_digest(runtime_root, final_snapshot)
        if final_digest != promoted_digest:
            raise RuntimeError("final promotion differs from the rehearsed promotion")
    except Exception:
        restore_bins(bin_dir, preimage)
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
        "preserved_regular_bins": sorted(PRESERVED_REGULAR_BINS & set(targets)),
        "promoted_bins": sorted(set(targets) - PRESERVED_REGULAR_BINS),
    }
    state_path = STATE_DIR / "candidate-node-runtime-latest.json"
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "mode": "applied", "state_path": str(state_path), **state}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
