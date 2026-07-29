#!/usr/bin/env python3
"""Reproduce candidate plugin provenance digests from clean pinned checkouts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wagents.candidate_plugin_provenance import (
    load_plugin_provenance_lock,
    plugin_lock_entry_sha256,
    verify_upstream_projection,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
LOCK_PATH = MANIFEST_DIR / "plugin-provenance-lock.json"
DEFAULT_OUTPUT = MANIFEST_DIR / "plugin-provenance-audit-evidence.json"


def parse_checkouts(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        plugin_id, separator, raw_path = value.partition("=")
        if not separator or not plugin_id or not raw_path:
            raise ValueError("--checkout values must use plugin-id=/absolute/path")
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            raise ValueError("plugin provenance checkout paths must be absolute")
        if plugin_id in result:
            raise ValueError(f"duplicate plugin provenance checkout mapping: {plugin_id}")
        result[plugin_id] = path
    return result


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.wagents-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def build_evidence(checkouts: dict[str, Path]) -> dict[str, Any]:
    entries = load_plugin_provenance_lock(LOCK_PATH)
    if set(checkouts) != set(entries):
        raise ValueError(
            "checkout mappings must exactly cover the provenance lock: "
            f"expected {sorted(entries)}, found {sorted(checkouts)}"
        )
    rows: list[dict[str, Any]] = []
    for plugin_id, entry in sorted(entries.items()):
        digest = verify_upstream_projection(checkouts[plugin_id], entry)
        rows.append({
            "plugin_id": plugin_id,
            "audited_source_commit_sha": entry["audited_source_commit_sha"],
            "upstream_git_tree_oid": entry["upstream_git_tree_oid"],
            "source_projection": entry["source_projection"],
            "approved_content_sha256": digest,
            "provenance_lock_entry_sha256": plugin_lock_entry_sha256(entry),
            "verification_status": "passed",
        })
    return {
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "lock_path": str(LOCK_PATH.relative_to(ROOT)),
        "lock_sha256": hashlib.sha256(LOCK_PATH.read_bytes()).hexdigest(),
        "network_accessed": False,
        "plugin_count": len(rows),
        "plugins": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", action="append", default=[])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = build_evidence(parse_checkouts(args.checkout))
    if args.check:
        if not args.output.is_file():
            raise ValueError(f"plugin provenance evidence is missing: {args.output}")
        current = json.loads(args.output.read_text(encoding="utf-8"))
        comparable = {key: value for key, value in payload.items() if key != "generated_at"}
        current_comparable = {key: value for key, value in current.items() if key != "generated_at"}
        if comparable != current_comparable:
            raise ValueError("plugin provenance evidence is stale")
    else:
        atomic_json(args.output, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
