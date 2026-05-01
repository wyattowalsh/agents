"""OpenSpec integration helpers for repo and downstream agent workflows."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wagents import ROOT

OPENSPEC_PACKAGE = "@fission-ai/openspec@latest"
OPENSPEC_TELEMETRY_ENV = "OPENSPEC_TELEMETRY"
OPENSPEC_MIN_NODE_VERSION = (20, 19, 0)

OPENSPEC_TOOL_BY_AGENT: dict[str, str] = {
    "antigravity": "antigravity",
    "claude-code": "claude",
    "codex": "codex",
    "crush": "crush",
    "cursor": "cursor",
    "gemini-cli": "gemini",
    "github-copilot": "github-copilot",
    "opencode": "opencode",
}

OPENSPEC_CORE_WORKFLOWS = ("propose", "explore", "apply", "archive")
OPENSPEC_EXPANDED_WORKFLOWS = (
    "propose",
    "explore",
    "new",
    "continue",
    "ff",
    "apply",
    "verify",
    "sync",
    "archive",
    "bulk-archive",
    "onboard",
)

OPENSPEC_GENERATED_PATHS = (
    ".agent/",
    ".claude/commands/",
    ".codex/",
    ".crush/",
    ".cursor/commands/",
    ".cursor/skills/",
    ".gemini/commands/",
    ".gemini/skills/",
    ".github/prompts/",
    ".github/skills/",
    ".opencode/commands/",
    ".opencode/skills/",
)


@dataclass(frozen=True)
class OpenSpecCommandResult:
    """Normalized result for an OpenSpec subprocess invocation."""

    argv: list[str]
    returncode: int
    stdout: str
    stderr: str

    def json_stdout(self) -> Any | None:
        """Parse stdout as JSON when OpenSpec returned structured output."""
        if not self.stdout.strip():
            return None
        return json.loads(self.stdout)


def format_min_node_version() -> str:
    """Return the OpenSpec minimum Node.js version as a display string."""
    return ".".join(str(part) for part in OPENSPEC_MIN_NODE_VERSION)


def parse_node_version(version_text: str) -> tuple[int, int, int] | None:
    """Parse a Node.js version string like `v20.19.0`."""
    match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", version_text.strip())
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def node_version_supported(version_text: str) -> bool | None:
    """Return whether a Node.js version satisfies OpenSpec's minimum."""
    version = parse_node_version(version_text)
    if version is None:
        return None
    return version >= OPENSPEC_MIN_NODE_VERSION


def select_openspec_tools(
    *,
    agents: Sequence[str] | None = None,
    tools: Sequence[str] | None = None,
) -> tuple[str, ...]:
    """Resolve repo agent IDs and raw OpenSpec tool IDs into OpenSpec tool IDs."""
    selected: list[str] = []
    for agent in agents or []:
        try:
            selected.append(OPENSPEC_TOOL_BY_AGENT[agent])
        except KeyError as exc:
            supported = ", ".join(sorted(OPENSPEC_TOOL_BY_AGENT))
            raise ValueError(f"unknown agent {agent!r}; supported agents: {supported}") from exc
    selected.extend(tools or [])
    return tuple(dict.fromkeys(selected))


def build_openspec_argv(args: Sequence[str], *, package: str = OPENSPEC_PACKAGE) -> list[str]:
    """Build an `npx` command for running OpenSpec without a repo dependency."""
    return ["npx", "-y", package, *args]


def run_openspec(
    args: Sequence[str],
    *,
    cwd: Path = ROOT,
    package: str = OPENSPEC_PACKAGE,
    capture: bool = True,
) -> OpenSpecCommandResult:
    """Run OpenSpec with telemetry disabled by default for repo automation."""
    argv = build_openspec_argv(args, package=package)
    env = os.environ.copy()
    env.setdefault(OPENSPEC_TELEMETRY_ENV, "0")
    result = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=capture,
        check=False,
    )
    return OpenSpecCommandResult(
        argv=argv,
        returncode=result.returncode,
        stdout=result.stdout or "",
        stderr=result.stderr or "",
    )


def _tool_version(tool: str) -> dict[str, Any]:
    """Return presence and version details for a local executable."""
    path = shutil.which(tool)
    payload: dict[str, Any] = {"tool": tool, "path": path, "available": path is not None}
    if path is None:
        return payload
    result = subprocess.run([tool, "--version"], text=True, capture_output=True, check=False)
    payload["returncode"] = result.returncode
    payload["version"] = (result.stdout or result.stderr).strip()
    return payload


def build_doctor_report(
    *,
    root: Path = ROOT,
    package: str = OPENSPEC_PACKAGE,
    check_cli: bool = False,
    validate: bool = False,
) -> dict[str, Any]:
    """Build a diagnostic report for OpenSpec integration health."""
    node = _tool_version("node")
    npx = _tool_version("npx")
    node_supported = node_version_supported(str(node.get("version") or ""))

    openspec_dir = root / "openspec"
    generated_paths = [path for path in OPENSPEC_GENERATED_PATHS if (root / path).exists()]
    telemetry_value = os.environ.get(OPENSPEC_TELEMETRY_ENV, "0")
    report: dict[str, Any] = {
        "package": package,
        "telemetryEnv": {OPENSPEC_TELEMETRY_ENV: telemetry_value},
        "minimumNode": format_min_node_version(),
        "node": {**node, "supported": node_supported},
        "npx": npx,
        "project": {
            "config": str(openspec_dir / "config.yaml"),
            "configExists": (openspec_dir / "config.yaml").exists(),
            "specsExists": (openspec_dir / "specs").exists(),
            "changesExists": (openspec_dir / "changes").exists(),
            "schemasExists": (openspec_dir / "schemas").exists(),
        },
        "toolMapping": OPENSPEC_TOOL_BY_AGENT,
        "generatedArtifacts": generated_paths,
        "checks": [],
    }

    if check_cli:
        result = run_openspec(["--version"], cwd=root, package=package)
        report["checks"].append(
            {
                "name": "openspec-version",
                "argv": result.argv,
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        )

    if validate:
        result = run_openspec(["validate", "--all", "--json"], cwd=root, package=package)
        check: dict[str, Any] = {
            "name": "openspec-validate",
            "argv": result.argv,
            "returncode": result.returncode,
            "stderr": result.stderr.strip(),
        }
        try:
            check["json"] = result.json_stdout()
        except json.JSONDecodeError:
            check["stdout"] = result.stdout.strip()
        report["checks"].append(check)

    return report
