"""CLI contract tests for scripts/bootstrap-dev-env.sh."""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "bootstrap-dev-env.sh"
SYNC_PY = ROOT / "scripts" / "sync_agent_stack.py"
SYNC_SH = ROOT / "scripts" / "bootstrap-dev-env" / "sync.sh"
LOCAL_ONLY = ROOT / "scripts" / "mcphub" / "start-local-only.sh"

FLEET = ("repo-core", "cursor", "claude-code", "codex", "grok", "opencode")
REMAPPED = ("claude", "gemini", "copilot")
ALLOW_CALL_RE = re.compile(r"platform_filter_allows\(\s*platforms_filter((?:,\s*\"[^\"]+\")+)\s*\)")
ORDER_RE = re.compile(r'^_STACK_PLATFORM_ORDER="([^"]+)"$', re.MULTILINE)
PLATFORMS_RE = re.compile(r"--platforms\s+(\S+)")


def _run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    merged.setdefault("NO_COLOR", "1")
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=False,
        cwd=str(ROOT),
        env=merged,
    )


def _scraped_allowlist() -> set[str]:
    text = SYNC_PY.read_text(encoding="utf-8")
    names: set[str] = set()
    for match in ALLOW_CALL_RE.finditer(text):
        names.update(re.findall(r'"([^"]+)"', match.group(1)))
    return names


def _bash_platform_order() -> list[str]:
    text = SYNC_SH.read_text(encoding="utf-8")
    match = ORDER_RE.search(text)
    assert match, "_STACK_PLATFORM_ORDER missing from sync.sh"
    return match.group(1).split()


def _planned_platforms(stderr: str) -> list[str]:
    match = PLATFORMS_RE.search(stderr)
    assert match, f"no --platforms in stderr:\n{stderr}"
    return [token for token in match.group(1).split(",") if token]


def test_help_mentions_dry_run() -> None:
    result = _run("--help")
    assert result.returncode == 0
    assert "dry-run" in result.stdout
    assert "Never" in result.stdout
    assert "Cursor" in result.stdout
    assert "Claude Code" in result.stdout
    assert "Codex" in result.stdout
    assert "Grok Build" in result.stdout
    assert "OpenCode" in result.stdout


def test_unknown_flag_exits_2() -> None:
    result = _run("--not-a-real-flag")
    assert result.returncode == 2
    assert "Unknown option" in result.stderr


def test_dry_run_json_schema_and_no_home_mutation(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    result = _run(
        "--dry-run",
        "--format",
        "json",
        env={
            "HOME": str(home),
            "WAGENTS_REPO_ROOT": str(ROOT),
            "XDG_RUNTIME_DIR": str(tmp_path / "run"),
        },
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["schema"] == "wagents.bootstrap-dev-env.v1"
    assert report["ok"] is True
    assert report["mode"] == "dry-run"
    assert "profile" in report
    assert isinstance(report["phases"], list)
    assert isinstance(report["harnesses"], list)
    leftover = [path for path in home.rglob("*") if path.is_file()]
    assert leftover == []
    assert "ensure-running.sh" not in result.stdout
    assert "ensure-running.sh" not in result.stderr
    assert "mcphub-up" not in result.stderr


def test_forced_fleet_platforms_csv(tmp_path: Path) -> None:
    result = _run(
        "--dry-run",
        "--format",
        "json",
        "--harness",
        "cursor",
        "--harness",
        "claude-code",
        "--harness",
        "codex",
        "--harness",
        "grok",
        "--harness",
        "opencode",
        env={
            "HOME": str(tmp_path / "home"),
            "WAGENTS_REPO_ROOT": str(ROOT),
            "XDG_RUNTIME_DIR": str(tmp_path / "run"),
        },
    )
    assert result.returncode == 0, result.stderr
    assert "--platforms repo-core,cursor,claude-code,codex,grok,opencode" in result.stderr


def test_harness_subset_platforms_csv(tmp_path: Path) -> None:
    result = _run(
        "--dry-run",
        "--format",
        "json",
        "--harness",
        "grok",
        "--harness",
        "opencode",
        env={
            "HOME": str(tmp_path / "home"),
            "WAGENTS_REPO_ROOT": str(ROOT),
            "XDG_RUNTIME_DIR": str(tmp_path / "run"),
        },
    )
    assert result.returncode == 0, result.stderr
    assert "--platforms repo-core,grok,opencode" in result.stderr
    assert "cursor" not in _planned_platforms(result.stderr)


def test_auto_never_emits_remapped_platform_tokens(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("cursor", "claude", "codex", "grok", "opencode", "gemini", "copilot"):
        stub = bin_dir / name
        stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        stub.chmod(0o755)
    path_dirs = [str(bin_dir)]
    for cmd in ("uv", "node", "npx", "git", "bash"):
        found = shutil.which(cmd)
        if found:
            parent = str(Path(found).parent)
            if parent not in path_dirs:
                path_dirs.append(parent)
    for extra in ("/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"):
        if extra not in path_dirs:
            path_dirs.append(extra)
    result = _run(
        "--dry-run",
        "--format",
        "json",
        env={
            "HOME": str(tmp_path / "home"),
            "WAGENTS_REPO_ROOT": str(ROOT),
            "XDG_RUNTIME_DIR": str(tmp_path / "run"),
            "PATH": os.pathsep.join(path_dirs),
        },
    )
    assert result.returncode == 0, result.stderr
    planned = _planned_platforms(result.stderr)
    assert planned == list(FLEET)
    assert not any(token in REMAPPED for token in planned)
    assert "gemini" not in result.stderr.split("--platforms", 1)[-1].splitlines()[0]
    assert "copilot" not in result.stderr.split("--platforms", 1)[-1].splitlines()[0]


def test_scraped_allowlist_covers_planned_tokens() -> None:
    allow = _scraped_allowlist()
    assert set(FLEET) <= allow
    bash_order = _bash_platform_order()
    assert bash_order[:6] == list(FLEET)
    unknown = [name for name in bash_order if name not in allow]
    assert unknown == [], f"bash emits unknown stack tokens: {unknown}"


def test_default_does_not_start_mcphub(tmp_path: Path) -> None:
    result = _run(
        "--dry-run",
        "--format",
        "json",
        env={
            "HOME": str(tmp_path / "home"),
            "WAGENTS_REPO_ROOT": str(ROOT),
            "XDG_RUNTIME_DIR": str(tmp_path / "run"),
        },
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    starts = [item for item in report["phases"] if item["id"] == "mcphub-start"]
    assert starts
    assert starts[0]["status"] == "skip"
    assert "start-local-only" not in result.stderr
    assert "Would start local MCPHub" not in result.stderr


def test_mcphub_dry_run_uses_start_local_only() -> None:
    result = _run("--dry-run", "--mcphub", "--format", "json")
    assert result.returncode == 0, result.stderr
    combined = f"{result.stdout}\n{result.stderr}"
    assert "start-local-only" in combined
    assert "ensure-running.sh" not in combined
    report = json.loads(result.stdout)
    phase_ids = {item["id"] for item in report["phases"]}
    assert "mcphub-start" in phase_ids


def test_start_local_only_never_starts_tunnel() -> None:
    text = LOCAL_ONLY.read_text(encoding="utf-8")
    assert "MCPHUB_TUNNEL_ENABLED=false" in text
    assert "mcphub_start_tunnel" not in text
    assert "ensure-running.sh" not in text
    mode = LOCAL_ONLY.stat().st_mode
    assert mode & stat.S_IXUSR
