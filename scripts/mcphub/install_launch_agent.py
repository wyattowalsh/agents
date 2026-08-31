#!/usr/bin/env python3
"""Atomically install the MCPHub LaunchAgent plist without loading or starting it."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import stat
import tempfile
from pathlib import Path
from typing import Any

LABEL = "com.wyattowalsh.mcphub"
SOURCE_RELATIVE = Path("config/launchd/com.wyattowalsh.mcphub.plist")
PLACEHOLDER = b"/path/to/agents"


class InstallError(ValueError):
    """Raised when LaunchAgent installation cannot stay exact and atomic."""


def _current_uid() -> int:
    if not hasattr(os, "getuid"):
        raise InstallError("owner validation requires a POSIX runtime")
    return os.getuid()


def _validate_directory(path: Path, label: str) -> None:
    if not path.is_absolute():
        raise InstallError(f"{label} must be absolute")
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or path.is_symlink():
        raise InstallError(f"{label} must be a non-symlink directory")
    if metadata.st_uid != _current_uid() or metadata.st_mode & 0o022:
        raise InstallError(f"{label} has unsafe ownership or mode")
    if path.resolve(strict=True) != path:
        raise InstallError(f"{label} must not traverse a symlink")


def _read_regular(path: Path, label: str) -> bytes:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or path.is_symlink() or before.st_nlink != 1:
        raise InstallError(f"{label} must be a single-link regular file")
    if before.st_uid != _current_uid() or before.st_mode & 0o022:
        raise InstallError(f"{label} has unsafe ownership or mode")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_nlink) != (before.st_dev, before.st_ino, 1):
            raise InstallError(f"{label} identity changed while opening")
        data = os.read(descriptor, opened.st_size + 1)
        if len(data) != opened.st_size:
            raise InstallError(f"{label} size changed while reading")
        return data
    finally:
        os.close(descriptor)


def _parse_plist(data: bytes) -> dict[str, Any]:
    payload = plistlib.loads(data)
    if not isinstance(payload, dict):
        raise InstallError("LaunchAgent plist root must be a dictionary")
    return payload


def render_launch_agent(repo_root: Path) -> bytes:
    _validate_directory(repo_root, "repository root")
    source = repo_root / SOURCE_RELATIVE
    source_bytes = _read_regular(source, "LaunchAgent template")
    if source_bytes.count(PLACEHOLDER) != 2:
        raise InstallError("LaunchAgent template must contain exactly two repository placeholders")
    rendered = source_bytes.replace(PLACEHOLDER, os.fsencode(repo_root))
    payload = _parse_plist(rendered)
    expected_runner = str(repo_root / "scripts/mcphub/launch-agent-run.sh")
    if payload.get("Label") != LABEL:
        raise InstallError("LaunchAgent label drifted")
    if payload.get("ProgramArguments") != [expected_runner]:
        raise InstallError("LaunchAgent program arguments drifted")
    if payload.get("WorkingDirectory") != str(repo_root):
        raise InstallError("LaunchAgent working directory drifted")
    if payload.get("RunAtLoad") is not True:
        raise InstallError("LaunchAgent must start when explicitly bootstrapped")
    if "EnvironmentVariables" in payload:
        raise InstallError("LaunchAgent must not embed environment or credential values")
    return rendered


def _validate_destination(path: Path) -> None:
    if not path.is_absolute():
        raise InstallError("LaunchAgent destination must be absolute")
    _validate_directory(path.parent, "LaunchAgent destination parent")
    if not path.exists() and not path.is_symlink():
        return
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink() or metadata.st_nlink != 1:
        raise InstallError("LaunchAgent destination must be a single-link regular file")
    if metadata.st_uid != _current_uid() or metadata.st_mode & 0o022:
        raise InstallError("LaunchAgent destination has unsafe ownership or mode")


def _matches(path: Path, expected: bytes) -> bool:
    try:
        _validate_destination(path)
        actual = _read_regular(path, "LaunchAgent destination")
    except FileNotFoundError:
        return False
    return actual == expected and stat.S_IMODE(path.stat().st_mode) == 0o600


def install_launch_agent(repo_root: Path, destination: Path, *, check: bool) -> str:
    expected = render_launch_agent(repo_root)
    _validate_destination(destination)
    if check:
        if not _matches(destination, expected):
            raise InstallError("installed LaunchAgent plist is missing or drifted")
        return "current"

    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(expected)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        temporary_bytes = _read_regular(temporary, "staged LaunchAgent")
        if temporary_bytes != expected or stat.S_IMODE(temporary.stat().st_mode) != 0o600:
            raise InstallError("staged LaunchAgent readback failed")
        _parse_plist(temporary_bytes)
        os.replace(temporary, destination)
        directory_descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)

    if not _matches(destination, expected):
        raise InstallError("installed LaunchAgent readback failed")
    return "installed"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path.home() / "Library/LaunchAgents/com.wyattowalsh.mcphub.plist",
    )
    parser.add_argument("--check", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        status = install_launch_agent(args.repo_root, args.destination, check=args.check)
    except (InstallError, OSError, plistlib.InvalidFileException):
        print(json.dumps({"status": "error", "reasonCode": "MCPHUB_LAUNCH_AGENT_INSTALL_FAILED"}))
        return 1
    print(json.dumps({"status": status, "service": LABEL, "started": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
