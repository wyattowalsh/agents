#!/usr/bin/env python3
"""Atomically merge tracked MCPHub settings with local-only auth state."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from stat import S_ISREG
from typing import Any

LOCAL_BEARER_KEY_ID = "d40d8b3e-a716-5a92-bde7-3a563bd74212"
PRESERVED_AUTH_COLLECTIONS = ("oauthClients", "oauthTokens", "users")
LOCAL_AUTH_COLLECTIONS = ("bearerKeys", *PRESERVED_AUTH_COLLECTIONS)


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def load_private_runtime(path: Path) -> dict[str, Any]:
    if not path.exists() and not path.is_symlink():
        return {}
    metadata = path.lstat()
    if (
        not S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or metadata.st_nlink != 1
        or (hasattr(os, "getuid") and metadata.st_uid != os.getuid())
        or metadata.st_mode & 0o077
    ):
        raise ValueError(f"runtime settings path is not a private owner-owned regular file: {path}")
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def local_auth_collection(payload: dict[str, Any], name: str) -> list[Any]:
    value = payload.get(name)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"runtime {name} must be a JSON array")
    return value


def merge_runtime_settings(
    tracked: dict[str, Any],
    current: dict[str, Any],
    *,
    bearer_token: str,
) -> dict[str, Any]:
    merged = dict(tracked)
    preserved = {name: local_auth_collection(current, name) for name in PRESERVED_AUTH_COLLECTIONS}
    token = bearer_token.strip()
    if not token or token.startswith("replace-with-local-") or token == "${MCPHUB_BEARER_TOKEN}":
        raise ValueError("the current local bearer token is required")

    for name in LOCAL_AUTH_COLLECTIONS:
        merged.pop(name, None)
    merged["bearerKeys"] = [
        {
            "id": LOCAL_BEARER_KEY_ID,
            "name": "local-control-plane",
            "token": token,
            "enabled": True,
            "kind": "system",
            "accessType": "all",
            "allowedGroups": [],
            "allowedServers": [],
        }
    ]

    for name, collection in preserved.items():
        if collection:
            merged[name] = collection
    return merged


def private_json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2) + "\n").encode("utf-8")


def write_private_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        if path.read_bytes() != payload or path.stat().st_mode & 0o777 != 0o600:
            raise OSError(f"private atomic write verification failed: {path}")
    finally:
        temporary.unlink(missing_ok=True)


def apply_runtime_settings(path: Path, payload: dict[str, Any]) -> None:
    write_private_bytes(path, private_json_bytes(payload))


def reject_legacy_full_backup(path: Path) -> None:
    backup = path.with_name(f"{path.name}.bak")
    if backup.exists() or backup.is_symlink():
        raise ValueError("legacy full private settings backup must be removed under explicit approval")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracked", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    tracked = load_object(args.tracked)
    reject_legacy_full_backup(args.runtime)
    current = load_private_runtime(args.runtime)
    merged = merge_runtime_settings(
        tracked,
        current,
        bearer_token=os.environ.get("MCPHUB_BEARER_TOKEN", ""),
    )

    if args.check:
        if current != merged:
            print("runtime settings drift detected", file=sys.stderr)
            return 1
        print("runtime settings are reconciled")
        return 0

    if current != merged:
        apply_runtime_settings(args.runtime, merged)

    counts = {name: len(local_auth_collection(merged, name)) for name in PRESERVED_AUTH_COLLECTIONS}
    print("installed current local bearer: 1")
    print("preserved local auth collections: " + ", ".join(f"{name}={count}" for name, count in counts.items()))
    if current == merged:
        print("runtime settings already reconciled; no file replaced")
    else:
        print("replaced private runtime settings without creating an auth-bearing backup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
