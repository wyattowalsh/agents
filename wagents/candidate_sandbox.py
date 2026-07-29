"""Fail-closed process isolation for untrusted candidate runtime probes."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

SANDBOX_EXECUTABLE = Path("/usr/bin/sandbox-exec")
SANDBOX_REQUIRED_ENV = "WAGENTS_CANDIDATE_SANDBOX_REQUIRED"
SANDBOX_READ_ROOTS_ENV = "WAGENTS_CANDIDATE_SANDBOX_READ_ROOTS"
SANDBOX_WRITE_ROOTS_ENV = "WAGENTS_CANDIDATE_SANDBOX_WRITE_ROOTS"
SANDBOX_NETWORK_ENV = "WAGENTS_CANDIDATE_SANDBOX_NETWORK"
SANDBOX_PTY_ENV = "WAGENTS_CANDIDATE_SANDBOX_PTY"
SANDBOX_FILE_WATCH_ENV = "WAGENTS_CANDIDATE_SANDBOX_FILE_WATCH"
SANDBOX_CONTROL_ENV_KEYS = frozenset(
    {
        SANDBOX_REQUIRED_ENV,
        SANDBOX_READ_ROOTS_ENV,
        SANDBOX_WRITE_ROOTS_ENV,
        SANDBOX_NETWORK_ENV,
        SANDBOX_PTY_ENV,
        SANDBOX_FILE_WATCH_ENV,
    }
)

NetworkPolicy = Literal["none", "loopback", "external"]
NETWORK_POLICIES = frozenset({"none", "loopback", "external"})
_NPM_PACKAGE_NAME = re.compile(r"^(?:@[a-z0-9._-]+/)?[a-z0-9._-]+$", re.IGNORECASE)

_SYSTEM_READ_ROOTS = (
    Path("/System"),
    Path("/usr/bin"),
    Path("/usr/lib"),
    Path("/usr/libexec"),
    Path("/usr/sbin"),
    Path("/usr/share"),
    Path("/bin"),
    Path("/sbin"),
    Path("/Library/Apple"),
    Path("/private/etc/ssl"),
    Path("/private/var/db/timezone"),
)


def _canonical_roots(paths: Iterable[str | Path]) -> tuple[Path, ...]:
    roots: set[Path] = set()
    for value in paths:
        path = Path(value).expanduser()
        try:
            roots.add(path.resolve(strict=False))
        except OSError as error:
            raise RuntimeError(f"candidate sandbox root could not be resolved: {path}: {error}") from None
    return tuple(sorted(roots, key=str))


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(path.expanduser()))


def _read_roots(paths: Iterable[str | Path]) -> tuple[Path, ...]:
    """Preserve every lexical symlink hop needed to reach an allowed read root."""

    roots: set[Path] = set()
    for value in paths:
        pending = _lexical_absolute(Path(value))
        visited: set[Path] = set()
        while pending not in visited:
            visited.add(pending)
            roots.add(pending)
            parts = pending.parts
            prefix = Path(parts[0])
            for index, part in enumerate(parts[1:], start=1):
                prefix /= part
                if not prefix.is_symlink():
                    continue
                try:
                    target = Path(os.readlink(prefix))
                except OSError as error:
                    raise RuntimeError(
                        f"candidate sandbox symlink could not be read: {prefix}: {error}"
                    ) from None
                if not target.is_absolute():
                    target = prefix.parent / target
                target = _lexical_absolute(target)
                roots.update((prefix, target))
                pending = _lexical_absolute(target.joinpath(*parts[index + 1 :]))
                roots.add(pending)
                break
            else:
                try:
                    roots.add(pending.resolve(strict=False))
                except OSError as error:
                    raise RuntimeError(
                        f"candidate sandbox root could not be resolved: {pending}: {error}"
                    ) from None
                break
        else:
            raise RuntimeError(f"candidate sandbox read root contains a symlink cycle: {pending}")
    return tuple(sorted(roots, key=str))


def _profile_path(path: Path) -> str:
    # JSON strings use the quoting and escaping accepted by sandbox profile strings.
    return json.dumps(str(path), ensure_ascii=True)


def _network_policy(value: str) -> NetworkPolicy:
    if value not in NETWORK_POLICIES:
        choices = ", ".join(sorted(NETWORK_POLICIES))
        raise RuntimeError(f"candidate sandbox network policy must be one of {choices}: {value!r}")
    return cast("NetworkPolicy", value)


def _resolved_network_policy(value: str, legacy_allow_network: bool | None) -> NetworkPolicy:
    if legacy_allow_network is None:
        return _network_policy(value)
    if legacy_allow_network:
        raise RuntimeError("boolean candidate network access is unsupported; choose an explicit policy")
    if value != "none":
        raise RuntimeError("candidate sandbox received conflicting network policies")
    return "none"


def _javascript_package_root(path: Path) -> Path | None:
    """Return the nearest npm package containing path, including scoped packages."""

    current = path if path.is_dir() else path.parent
    for candidate in (current, *current.parents):
        if candidate.name == "node_modules":
            break
        if candidate.parent.name == "node_modules" and (candidate / "package.json").is_file():
            return candidate
        if (
            candidate.parent.parent.name == "node_modules"
            and candidate.parent.name.startswith("@")
            and (candidate / "package.json").is_file()
        ):
            return candidate
    return None


def _dependency_candidate(package_root: Path, dependency: str) -> Path | None:
    current = package_root
    while True:
        candidate = current / "node_modules" / dependency
        if (candidate / "package.json").is_file():
            return candidate.resolve(strict=True)
        if current.parent.name == "node_modules":
            candidate = current.parent / dependency
            if (candidate / "package.json").is_file():
                return candidate.resolve(strict=True)
            current = current.parent.parent
            continue
        if current.parent.parent.name == "node_modules" and current.parent.name.startswith("@"):
            candidate = current.parent.parent / dependency
            if (candidate / "package.json").is_file():
                return candidate.resolve(strict=True)
            current = current.parent.parent.parent
            continue
        break
    return None


def selected_javascript_package_roots(executable: str | Path) -> tuple[Path, ...]:
    """Return one package plus its installed runtime dependency closure, never sibling packages."""

    resolved = Path(executable).resolve(strict=True)
    root = _javascript_package_root(resolved)
    if root is None:
        return (resolved, resolved.parent)

    selected: set[Path] = set()
    pending = [root.resolve(strict=True)]
    while pending:
        package = pending.pop()
        if package in selected:
            continue
        selected.add(package)
        try:
            payload = json.loads((package / "package.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"candidate package metadata is invalid: {package}: {error}") from None
        if not isinstance(payload, dict):
            raise RuntimeError(f"candidate package metadata must be an object: {package}")
        names: set[str] = set()
        for field in ("dependencies", "optionalDependencies", "peerDependencies"):
            dependencies = payload.get(field, {})
            if not isinstance(dependencies, dict):
                raise RuntimeError(f"candidate package {field} must be an object: {package}")
            names.update(str(name) for name in dependencies)
        for name in sorted(names):
            if not _NPM_PACKAGE_NAME.fullmatch(name):
                raise RuntimeError(f"candidate package has an invalid dependency name: {package}: {name!r}")
            dependency = _dependency_candidate(package, name)
            if dependency is not None and dependency not in selected:
                pending.append(dependency)
    return tuple(sorted({resolved, *selected}, key=str))


def selected_macos_runtime_roots(executable: str | Path) -> tuple[Path, ...]:
    """Return one Mach-O runtime and only its selected Homebrew formula dependencies."""

    resolved = Path(executable).resolve(strict=True)
    roots: set[Path] = {resolved, resolved.parent, resolved.parent.parent}
    if sys.platform != "darwin":
        return tuple(sorted(roots, key=str))
    try:
        magic = resolved.read_bytes()[:4]
    except OSError as error:
        raise RuntimeError(f"candidate runtime could not be inspected: {resolved}: {error}") from None
    if magic not in {
        b"\xca\xfe\xba\xbe",
        b"\xcf\xfa\xed\xfe",
        b"\xce\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xfe\xed\xfa\xce",
    }:
        return tuple(sorted(roots, key=str))

    pending = [resolved]
    inspected: set[Path] = set()
    while pending:
        binary = pending.pop()
        if binary in inspected:
            continue
        inspected.add(binary)
        result = subprocess.run(
            ["/usr/bin/otool", "-L", str(binary)],
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"candidate runtime dependency inspection failed: {binary}")
        for line in result.stdout.splitlines()[1:]:
            dependency_text = line.strip().split(" (", 1)[0]
            if not dependency_text.startswith("/"):
                continue
            dependency = Path(dependency_text)
            if not dependency.exists() or dependency_text.startswith(("/System/", "/usr/lib/")):
                continue
            parts = dependency.parts
            if len(parts) >= 5 and parts[:4] == ("/", "opt", "homebrew", "opt"):
                roots.add(Path(*parts[:5]))
            else:
                roots.add(dependency)
            canonical = dependency.resolve(strict=True)
            roots.add(canonical)
            if canonical not in inspected:
                pending.append(canonical)
    return tuple(sorted(roots, key=str))


def _metadata_roots(paths: Iterable[Path]) -> tuple[Path, ...]:
    roots: set[Path] = set()
    for path in paths:
        current = path
        while True:
            roots.add(current)
            if current == current.parent:
                break
            current = current.parent
    return tuple(sorted(roots, key=str))


def macos_sandbox_profile(
    *,
    read_roots: Iterable[str | Path],
    write_roots: Iterable[str | Path],
    network_policy: NetworkPolicy = "none",
    allow_pty: bool = False,
    allow_file_watch: bool = False,
) -> str:
    """Build a deny-by-default macOS Seatbelt profile for one candidate process."""

    reads = _read_roots((*_SYSTEM_READ_ROOTS, *read_roots))
    writes = _canonical_roots(write_roots)
    network_policy = _network_policy(network_policy)
    process_filters = " ".join(f"(subpath {_profile_path(path)})" for path in reads)
    lines = [
        "(version 1)",
        "(deny default)",
        '(import "system.sb")',
        "(allow process-fork)",
        f"(allow process-exec {process_filters})",
        "(allow signal (target self))",
        "(allow sysctl-read)",
    ]
    if reads:
        metadata_filters = " ".join(
            f"(literal {_profile_path(path)})" for path in _metadata_roots(reads)
        )
        lines.append(f"(allow file-read-metadata {metadata_filters})")
        filters = " ".join(f"(subpath {_profile_path(path)})" for path in reads)
        lines.append(f"(allow file-read* {filters})")
    if writes:
        filters = " ".join(f"(subpath {_profile_path(path)})" for path in writes)
        lines.append(f"(allow file-write* {filters})")
    if allow_pty:
        lines.extend(
            (
                "(allow pseudo-tty)",
                '(allow file-read* file-write* file-ioctl (literal "/dev/ptmx"))',
                '(allow file-read* file-write* file-ioctl (regex #"^/dev/ttys[0-9]*"))',
            )
        )
    if allow_file_watch:
        lines.append('(allow mach-lookup (global-name "com.apple.FSEvents"))')
    lines.append("(deny network*)")
    if network_policy == "loopback":
        lines.extend(
            (
                '(allow network-inbound (local ip "localhost:*"))',
                '(allow network-outbound (remote ip "localhost:*"))',
            )
        )
    elif network_policy == "external":
        # External probes receive outbound sockets only; listening remains denied.
        lines.append("(allow network-outbound)")
    return "\n".join(lines) + "\n"


def sandboxed_argv(
    argv: Sequence[str],
    *,
    read_roots: Iterable[str | Path],
    write_roots: Iterable[str | Path],
    network_policy: NetworkPolicy = "none",
    allow_pty: bool = False,
    allow_file_watch: bool = False,
    required: bool = True,
    allow_network: bool | None = None,
) -> list[str]:
    """Wrap an absolute executable with the platform sandbox when running on macOS."""

    if not argv:
        raise RuntimeError("candidate sandbox received an empty argv")
    executable = Path(argv[0])
    if not executable.is_absolute():
        raise RuntimeError(f"candidate sandbox requires an absolute executable: {argv[0]!r}")
    if sys.platform != "darwin":
        if required:
            raise RuntimeError(f"required candidate sandbox is unsupported on platform {sys.platform!r}")
        return list(argv)
    if not SANDBOX_EXECUTABLE.is_file() or not os.access(SANDBOX_EXECUTABLE, os.X_OK):
        raise RuntimeError("required macOS sandbox-exec is unavailable")
    profile = macos_sandbox_profile(
        read_roots=(*read_roots, executable, executable.resolve(strict=False)),
        write_roots=write_roots,
        network_policy=_resolved_network_policy(network_policy, allow_network),
        allow_pty=allow_pty,
        allow_file_watch=allow_file_watch,
    )
    return [str(SANDBOX_EXECUTABLE), "-p", profile, *argv]


def sandbox_environment(
    env: Mapping[str, str],
    *,
    read_roots: Iterable[str | Path],
    write_roots: Iterable[str | Path],
    network_policy: NetworkPolicy = "none",
    allow_pty: bool = False,
    allow_file_watch: bool = False,
    required: bool = True,
    allow_network: bool | None = None,
) -> dict[str, str]:
    """Return an environment declaring a required candidate subprocess sandbox."""

    result = dict(env)
    result[SANDBOX_REQUIRED_ENV] = "1" if required else "0"
    result[SANDBOX_READ_ROOTS_ENV] = json.dumps([str(path) for path in _read_roots(read_roots)])
    result[SANDBOX_WRITE_ROOTS_ENV] = json.dumps([str(path) for path in _canonical_roots(write_roots)])
    result[SANDBOX_NETWORK_ENV] = _resolved_network_policy(network_policy, allow_network)
    result[SANDBOX_PTY_ENV] = "1" if allow_pty else "0"
    result[SANDBOX_FILE_WATCH_ENV] = "1" if allow_file_watch else "0"
    return result


def prepare_sandboxed_subprocess(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
) -> tuple[list[str], dict[str, str]]:
    """Consume sandbox control variables and return launch argv plus a clean child env."""

    child_env = {key: value for key, value in env.items() if key not in SANDBOX_CONTROL_ENV_KEYS}
    if env.get(SANDBOX_REQUIRED_ENV) != "1":
        return list(argv), child_env
    try:
        read_roots = json.loads(env.get(SANDBOX_READ_ROOTS_ENV, "[]"))
        write_roots = json.loads(env.get(SANDBOX_WRITE_ROOTS_ENV, "[]"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"candidate sandbox roots are invalid JSON: {error}") from None
    if not isinstance(read_roots, list) or not all(isinstance(value, str) for value in read_roots):
        raise RuntimeError("candidate sandbox read roots must be a string list")
    if not isinstance(write_roots, list) or not all(isinstance(value, str) for value in write_roots):
        raise RuntimeError("candidate sandbox write roots must be a string list")
    wrapped = sandboxed_argv(
        argv,
        read_roots=(*read_roots, cwd),
        write_roots=write_roots,
        network_policy=_network_policy(env.get(SANDBOX_NETWORK_ENV, "none")),
        allow_pty=env.get(SANDBOX_PTY_ENV) == "1",
        allow_file_watch=env.get(SANDBOX_FILE_WATCH_ENV) == "1",
        required=True,
    )
    return wrapped, child_env
