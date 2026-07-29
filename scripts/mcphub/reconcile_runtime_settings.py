#!/usr/bin/env python3
"""Atomically merge tracked MCPHub settings with local-only auth state."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

LOCAL_AUTH_COLLECTIONS = ("bearerKeys", "oauthClients", "oauthTokens", "users")


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
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
    preserved = {name: local_auth_collection(current, name) for name in LOCAL_AUTH_COLLECTIONS}

    keys = preserved["bearerKeys"]
    token = bearer_token.strip()
    if not keys and token and not token.startswith("replace-with-local-"):
        keys = [
            {
                "id": str(uuid.uuid4()),
                "name": "local-control-plane",
                "token": token,
                "enabled": True,
                "kind": "system",
                "accessType": "all",
                "allowedGroups": [],
                "allowedServers": [],
            }
        ]
        preserved["bearerKeys"] = keys

    for name, collection in preserved.items():
        if collection:
            merged[name] = collection
        else:
            merged.pop(name, None)
    return merged


def write_private_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracked", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()

    tracked = load_object(args.tracked)
    current = load_object(args.runtime) if args.runtime.is_file() else {}
    merged = merge_runtime_settings(
        tracked,
        current,
        bearer_token=os.environ.get("MCPHUB_BEARER_TOKEN", ""),
    )
    write_private_json(args.runtime, merged)

    counts = {name: len(local_auth_collection(merged, name)) for name in LOCAL_AUTH_COLLECTIONS}
    print("preserved local auth collections: " + ", ".join(f"{name}={count}" for name, count in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
