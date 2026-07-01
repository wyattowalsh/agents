"""RTK (Rust Token Killer) diagnostics and sync planning."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from wagents import ROOT
from wagents.context import get_repo_root_optional

CONFIG_RELATIVE_PATH = Path("config") / "rtk-integration.json"
RTK_REQUIRED_INIT_FLAGS = ("--agent", "--auto-patch", "--codex", "--copilot", "--dry-run", "--gemini", "--opencode")
RTK_SYNC_APPLY_TIMEOUT_SECONDS = 120


def _repo_root(root: Path | None = None) -> Path:
    if root is not None:
        return root
    return get_repo_root_optional() or ROOT


def load_rtk_policy(root: Path | None = None) -> dict[str, Any]:
    """Load the repo RTK policy map."""
    path = _repo_root(root) / CONFIG_RELATIVE_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _make_check(name: str, status: str, summary: str, remediation: str | None = None) -> dict[str, str]:
    check = {"name": name, "status": status, "summary": summary}
    if remediation:
        check["remediation"] = remediation
    return check


def _config_string_list(value: object, *, strip_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        return []
    items = [str(item) for item in value]
    if strip_empty:
        return [item for item in items if item.strip()]
    return items


def _run_capture(argv: list[str], *, cwd: Path | None = None, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(argv, 127, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else f"timed out after {timeout}s"
        return subprocess.CompletedProcess(argv, 124, stdout, stderr)


def _first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _parse_version(version_text: str) -> tuple[int, ...] | None:
    match = re.search(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", version_text)
    if not match:
        return None
    return tuple(int(part) for part in match.groups(default="0"))


def _version_at_least(current: str, minimum: str) -> bool:
    parsed_current = _parse_version(current)
    parsed_minimum = _parse_version(minimum)
    if parsed_current is None or parsed_minimum is None:
        return False
    width = max(len(parsed_current), len(parsed_minimum))
    padded_current = parsed_current + (0,) * (width - len(parsed_current))
    padded_minimum = parsed_minimum + (0,) * (width - len(parsed_minimum))
    return padded_current >= padded_minimum


def _command_output(proc: subprocess.CompletedProcess[str]) -> str:
    return "\n".join(part for part in (proc.stdout, proc.stderr) if part).strip()


def _rtk_sync_command_error(argv: list[str]) -> str | None:
    if len(argv) >= 2 and argv[0] == "rtk" and argv[1] == "init":
        return None
    return "only rtk init commands are executable"


def _capture_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    return str(value).strip()


def _line_status_for_markers(output: str, markers: list[str]) -> tuple[str, str]:
    if not markers:
        return "ok", "no marker expectations"
    matched_lines = [
        line.strip() for line in output.splitlines() if any(marker and marker in line for marker in markers)
    ]
    if not matched_lines:
        return "warn", f"no expected marker found: {', '.join(markers)}"
    if any(line.startswith("[ok]") for line in matched_lines):
        return "ok", matched_lines[0]
    if any(line.startswith("[warn]") for line in matched_lines):
        return "warn", matched_lines[0]
    if any(line.startswith("[--]") for line in matched_lines):
        return "warn", matched_lines[0]
    return "ok", matched_lines[0]


def collect_rtk_doctor_checks(root: Path | None = None) -> list[dict[str, str]]:
    """Collect structured RTK doctor checks."""
    repo_root = _repo_root(root)
    checks: list[dict[str, str]] = []
    try:
        policy = load_rtk_policy(repo_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [
            _make_check(
                "rtk-policy",
                "fail",
                f"Could not load {CONFIG_RELATIVE_PATH}: {exc}",
                "Restore the RTK policy file or run from the agents repo.",
            )
        ]

    checks.append(_make_check("rtk-policy", "ok", str(repo_root / CONFIG_RELATIVE_PATH)))

    binary = shutil.which("rtk")
    if not binary:
        checks.append(
            _make_check(
                "rtk-binary",
                "fail",
                "rtk not found on PATH",
                str(policy.get("install", {}).get("macos") or "Install RTK first."),
            )
        )
        return checks

    checks.append(_make_check("rtk-binary", "ok", f"Found at {binary}"))

    version_proc = _run_capture(["rtk", "--version"], cwd=repo_root)
    version_text = _first_line(_command_output(version_proc)) or "unknown"
    minimum = str(policy.get("min_rtk_version") or "0")
    if version_proc.returncode != 0:
        checks.append(_make_check("rtk-version", "fail", version_text, "Fix the rtk binary on PATH."))
    elif _version_at_least(version_text, minimum):
        checks.append(_make_check("rtk-version", "ok", f"{version_text} (minimum {minimum})"))
    else:
        checks.append(
            _make_check(
                "rtk-version",
                "warn",
                f"{version_text} is below configured minimum {minimum}",
                str(policy.get("install", {}).get("macos") or "Upgrade RTK."),
            )
        )

    gain_proc = _run_capture(["rtk", "gain"], cwd=repo_root, timeout=15)
    gain_output = _command_output(gain_proc)
    if gain_proc.returncode == 0 and ("Tokens saved" in gain_output or "RTK Token Savings" in gain_output):
        checks.append(_make_check("rtk-package-identity", "ok", "rtk gain produced RTK savings output"))
    else:
        checks.append(
            _make_check(
                "rtk-package-identity",
                "fail",
                _first_line(gain_output) or "rtk gain failed",
                "Confirm PATH points to rtk-ai/rtk, not another rtk package.",
            )
        )

    help_proc = _run_capture(["rtk", "init", "--help"], cwd=repo_root)
    help_output = _command_output(help_proc)
    missing_flags = [flag for flag in RTK_REQUIRED_INIT_FLAGS if flag not in help_output]
    if help_proc.returncode != 0:
        checks.append(_make_check("rtk-init-help", "fail", _first_line(help_output) or "rtk init --help failed"))
    elif missing_flags:
        checks.append(
            _make_check(
                "rtk-init-flags",
                "fail",
                f"Missing expected flags: {', '.join(missing_flags)}",
                "Update RTK or revise config/rtk-integration.json.",
            )
        )
    else:
        checks.append(_make_check("rtk-init-flags", "ok", "Expected init flags are present"))

    harnesses = policy.get("harnesses", {})
    if not isinstance(harnesses, dict):
        checks.append(_make_check("rtk-harness-policy", "fail", "policy.harnesses must be an object"))
        return checks

    show_cache: dict[str, subprocess.CompletedProcess[str]] = {}
    for harness, config in sorted(harnesses.items()):
        if not isinstance(config, dict):
            checks.append(_make_check(f"rtk-{harness}", "fail", "harness config must be an object"))
            continue
        init_commands = _config_string_list(config.get("init"))
        mode = str(config.get("mode") or "unknown")
        if not init_commands:
            checks.append(_make_check(f"rtk-{harness}", "ok", f"{mode}: not applicable"))
            continue
        if any(command.startswith("repo:") for command in init_commands):
            checks.append(
                _make_check(
                    f"rtk-{harness}",
                    "warn",
                    f"{mode}: repo-deferred custom integration",
                    str(config.get("notes") or "Implement the repo shim before applying."),
                )
            )
            continue
        show_commands = _config_string_list(config.get("show"))
        command = show_commands[0] if show_commands else "rtk init --show"
        if command not in show_cache:
            show_cache[command] = _run_capture(shlex.split(command), cwd=repo_root)
        proc = show_cache[command]
        output = _command_output(proc)
        if proc.returncode != 0:
            checks.append(
                _make_check(
                    f"rtk-{harness}",
                    "warn",
                    f"{mode}: show command failed: {_first_line(output) or command}",
                    init_commands[0],
                )
            )
            continue
        markers = _config_string_list(config.get("expected_show_any"), strip_empty=False)
        status, summary = _line_status_for_markers(output, markers)
        remediation = init_commands[0] if status != "ok" else None
        checks.append(_make_check(f"rtk-{harness}", status, f"{mode}: {summary}", remediation))

    return checks


def rtk_doctor_report(root: Path | None = None) -> dict[str, Any]:
    checks = collect_rtk_doctor_checks(root=root)
    counts = {
        "ok": sum(1 for check in checks if check["status"] == "ok"),
        "warn": sum(1 for check in checks if check["status"] == "warn"),
        "fail": sum(1 for check in checks if check["status"] == "fail"),
    }
    return {"ok": counts["fail"] == 0, "summary": {"total": len(checks), **counts}, "checks": checks}


def rtk_self_doctor_check(root: Path | None = None) -> dict[str, str]:
    """Return a cheap non-fatal self-doctor row for RTK."""
    repo_root = _repo_root(root)
    binary = shutil.which("rtk")
    if not binary:
        return _make_check("rtk", "warn", "rtk not on PATH; optional RTK fleet integration unavailable")
    version_proc = _run_capture(["rtk", "--version"], cwd=repo_root)
    version = _first_line(_command_output(version_proc)) or binary
    if version_proc.returncode != 0:
        return _make_check("rtk", "warn", f"rtk found at {binary} but --version failed")
    return _make_check("rtk", "ok", f"{binary} - {version}")


def _parse_platforms(platforms: str | None, policy: dict[str, Any]) -> list[str]:
    harnesses = policy.get("harnesses", {})
    if not isinstance(harnesses, dict):
        raise ValueError("policy.harnesses must be an object")
    if platforms is None or not platforms.strip():
        return [str(key) for key in harnesses]
    selected = [item.strip() for item in platforms.split(",") if item.strip()]
    unknown = [item for item in selected if item not in harnesses]
    if unknown:
        raise ValueError(f"Unknown RTK platform(s): {', '.join(unknown)}")
    return selected


def build_rtk_sync_plan(
    *,
    platforms: str | None = None,
    dry_run: bool = True,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build a sync command plan from the RTK policy file."""
    repo_root = _repo_root(root)
    policy = load_rtk_policy(repo_root)
    selected = _parse_platforms(platforms, policy)
    harnesses = policy["harnesses"]
    env = {str(key): str(value) for key, value in (policy.get("telemetry_env") or {}).items()}
    commands: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for harness in selected:
        config = harnesses[harness]
        init_commands = _config_string_list(config.get("init"))
        if not init_commands:
            skipped.append({"platform": harness, "reason": str(config.get("notes") or "not applicable")})
            continue
        for command in init_commands:
            if command.startswith("repo:"):
                skipped.append({"platform": harness, "reason": f"deferred repo command: {command}"})
                continue
            argv = shlex.split(command)
            command_error = _rtk_sync_command_error(argv)
            if command_error:
                skipped.append({"platform": harness, "reason": f"unsupported sync command: {command_error}: {command}"})
                continue
            commands.append({
                "platform": harness,
                "tier": str(config.get("tier") or ""),
                "mode": str(config.get("mode") or ""),
                "command": command,
                "argv": argv,
                "dry_run": dry_run,
            })

    return {
        "dry_run": dry_run,
        "repo_root": str(repo_root),
        "env": env,
        "commands": commands,
        "skipped": skipped,
    }


def run_rtk_sync_plan(plan: dict[str, Any], *, cwd: Path | None = None) -> list[dict[str, Any]]:
    """Execute a previously built sync plan."""
    if plan.get("dry_run"):
        return [
            {
                "platform": command["platform"],
                "command": command["command"],
                "returncode": 0,
                "dry_run": True,
            }
            for command in plan.get("commands", [])
        ]
    env = os.environ.copy()
    env.update({str(key): str(value) for key, value in (plan.get("env") or {}).items()})
    results: list[dict[str, Any]] = []
    for command in plan.get("commands", []):
        argv = [str(item) for item in command.get("argv", [])]
        command_error = _rtk_sync_command_error(argv)
        if command_error:
            results.append({
                "platform": command.get("platform"),
                "command": command.get("command"),
                "returncode": 2,
                "stdout": "",
                "stderr": command_error,
            })
            continue
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd or Path(plan["repo_root"]),
                env=env,
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                check=False,
                timeout=RTK_SYNC_APPLY_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            results.append({
                "platform": command.get("platform"),
                "command": command.get("command"),
                "returncode": 124,
                "stdout": _capture_text(getattr(exc, "stdout", None) or getattr(exc, "output", None)),
                "stderr": f"timed out after {RTK_SYNC_APPLY_TIMEOUT_SECONDS}s",
                "timeout_seconds": RTK_SYNC_APPLY_TIMEOUT_SECONDS,
            })
            continue
        except FileNotFoundError as exc:
            results.append({
                "platform": command.get("platform"),
                "command": command.get("command"),
                "returncode": 127,
                "stdout": "",
                "stderr": str(exc),
            })
            continue
        results.append({
            "platform": command.get("platform"),
            "command": command.get("command"),
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        })
    return results


def run_rtk_gain(
    *,
    history: bool = False,
    project: bool = False,
    graph: bool = False,
    rtk_format: str = "text",
    root: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    argv = ["rtk", "gain", "--format", rtk_format]
    if history:
        argv.append("--history")
    if project:
        argv.append("--project")
    if graph:
        argv.append("--graph")
    return _run_capture(argv, cwd=_repo_root(root), timeout=30)
