#!/usr/bin/env python3
"""Rotate the private MCPHub bearer and enforce the disabled Things runtime."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import stat
import tempfile
from pathlib import Path

MAX_ENV_BYTES = 128 * 1024
TOKEN_KEY = b"MCPHUB_BEARER_TOKEN"
TOKEN_LINE = re.compile(rb"(?m)^MCPHUB_BEARER_TOKEN=([^\r\n]*)$")
SAFE_RUNTIME_ASSIGNMENTS = (
    (b"MCPHUB_PUBLIC_URL", b"https://mcp.w4w.dev/mcp/things"),
    (b"MCPHUB_REMOTE_MODE", b"disabled"),
    (b"MCPHUB_TUNNEL_ENABLED", b"false"),
)


class RotationError(ValueError):
    """Raised when rotation cannot preserve the private env-file contract."""


def _current_uid() -> int:
    if not hasattr(os, "getuid"):
        raise RotationError("owner validation requires a POSIX runtime")
    return os.getuid()


def _validate_parent(path: Path) -> None:
    parent = path.parent
    metadata = parent.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or parent.is_symlink():
        raise RotationError("env parent must be a non-symlink directory")
    if metadata.st_uid != _current_uid() or metadata.st_mode & 0o022:
        raise RotationError("env parent has unsafe ownership or mode")
    if parent.resolve(strict=True) != parent:
        raise RotationError("env parent must not traverse a symlink")


def _read_private_regular(path: Path) -> tuple[bytes, os.stat_result]:
    if not path.is_absolute():
        raise RotationError("env file must be absolute")
    _validate_parent(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or path.is_symlink():
        raise RotationError("env file must be a non-symlink regular file")
    if before.st_uid != _current_uid():
        raise RotationError("env file owner mismatch")
    if before.st_nlink != 1:
        raise RotationError("env file must have exactly one link")
    if stat.S_IMODE(before.st_mode) & 0o077:
        raise RotationError("env file must be owner-only")
    if before.st_size <= 0 or before.st_size > MAX_ENV_BYTES:
        raise RotationError("env file size is outside the bounded limit")

    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise RotationError("env file identity changed while opening")
        if opened.st_nlink != 1:
            raise RotationError("env file link count changed while opening")
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 64 * 1024))
            if not chunk:
                raise RotationError("env file ended before its recorded size")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks), opened
    finally:
        os.close(descriptor)


def _replace_token(data: bytes) -> bytes:
    matches = list(TOKEN_LINE.finditer(data))
    if len(matches) != 1:
        raise RotationError("env file must contain exactly one bearer-token assignment")
    if not matches[0].group(1):
        raise RotationError("current bearer-token assignment is empty")
    replacement = TOKEN_KEY + b"=" + secrets.token_urlsafe(48).encode("ascii")
    return data[: matches[0].start()] + replacement + data[matches[0].end() :]


def _set_unique_assignment(data: bytes, key: bytes, value: bytes) -> bytes:
    pattern = re.compile(rb"(?m)^" + re.escape(key) + rb"=([^\r\n]*)$")
    matches = list(pattern.finditer(data))
    if len(matches) > 1:
        raise RotationError("runtime assignment must not be duplicated")
    replacement = key + b"=" + value
    if matches:
        match = matches[0]
        return data[: match.start()] + replacement + data[match.end() :]
    separator = b"" if data.endswith(b"\n") else b"\n"
    return data + separator + replacement + b"\n"


def rotate_bearer_token(path: Path) -> None:
    original, opened = _read_private_regular(path)
    replacement = _replace_token(original)
    for key, value in SAFE_RUNTIME_ASSIGNMENTS:
        replacement = _set_unique_assignment(replacement, key, value)
    current = path.lstat()
    if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
        raise RotationError("env file identity changed before replacement")
    if current.st_nlink != 1:
        raise RotationError("env file link count changed before replacement")

    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(replacement)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)
    readback, metadata = _read_private_regular(path)
    if readback != replacement or stat.S_IMODE(metadata.st_mode) != 0o600:
        raise RotationError("rotated env file failed exact private readback")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    return parser


def main() -> int:
    try:
        args = _parser().parse_args()
        rotate_bearer_token(args.env_file)
    except (OSError, RotationError):
        print(json.dumps({"status": "error", "reasonCode": "MCPHUB_BEARER_ROTATION_FAILED"}))
        return 1
    print(
        json.dumps({
            "status": "rotated",
            "key": TOKEN_KEY.decode("ascii"),
            "runtimeMode": "local-disabled",
        })
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
