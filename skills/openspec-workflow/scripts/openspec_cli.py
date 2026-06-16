#!/usr/bin/env python3
"""OpenSpec CLI wrapper for the openspec-workflow skill.

Runs OpenSpec through `npx -y @fission-ai/openspec@latest` as a portable skill
script with no repo control-plane dependency.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
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
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str

    def json_stdout(self) -> Any | None:
        if not self.stdout.strip():
            return None
        return json.loads(self.stdout)


def build_openspec_argv(args: Sequence[str], *, package: str = OPENSPEC_PACKAGE) -> list[str]:
    """Build an `npx` command for running OpenSpec without a repo dependency."""
    return ["npx", "-y", package, *args]


def format_min_node_version() -> str:
    return ".".join(str(part) for part in OPENSPEC_MIN_NODE_VERSION)


def parse_node_version(version_text: str) -> tuple[int, int, int] | None:
    match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", version_text.strip())
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def node_version_supported(version_text: str) -> bool | None:
    version = parse_node_version(version_text)
    if version is None:
        return None
    return version >= OPENSPEC_MIN_NODE_VERSION


def select_openspec_tools(
    *,
    agents: Sequence[str] | None = None,
    tools: Sequence[str] | None = None,
) -> tuple[str, ...]:
    selected: list[str] = []
    for agent in agents or []:
        try:
            selected.append(OPENSPEC_TOOL_BY_AGENT[agent])
        except KeyError as exc:
            supported = ", ".join(sorted(OPENSPEC_TOOL_BY_AGENT))
            raise ValueError(f"unknown agent {agent!r}; supported agents: {supported}") from exc
    selected.extend(tools or [])
    return tuple(dict.fromkeys(selected))


def run_openspec(
    args: Sequence[str],
    *,
    cwd: Path = REPO_ROOT,
    package: str = OPENSPEC_PACKAGE,
    capture: bool = True,
) -> OpenSpecCommandResult:
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
    root: Path = REPO_ROOT,
    package: str = OPENSPEC_PACKAGE,
    check_cli: bool = False,
    validate: bool = False,
) -> dict[str, Any]:
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


def _emit_json(data: Any) -> None:
    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _emit_text(lines: Sequence[str]) -> None:
    for line in lines:
        print(line)


def _emit_command_result(result: OpenSpecCommandResult, *, format_: str, success_message: str) -> int:
    try:
        parsed_stdout = result.json_stdout()
    except json.JSONDecodeError:
        parsed_stdout = None

    payload: dict[str, object] = {
        "argv": result.argv,
        "returncode": result.returncode,
        "stdout": parsed_stdout if parsed_stdout is not None else result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
    if format_ == "json":
        _emit_json(payload)
    else:
        text_lines = [success_message, f"command: {shlex.join(result.argv)}", f"exit: {result.returncode}"]
        if result.stdout.strip():
            text_lines.extend(["stdout:", result.stdout.strip()])
        if result.stderr.strip():
            text_lines.extend(["stderr:", result.stderr.strip()])
        _emit_text(text_lines)
    return result.returncode


def _emit_dry_run(argv: list[str], *, format_: str) -> int:
    command = shlex.join(argv)
    if format_ == "json":
        _emit_json({"argv": argv, "command": command})
    else:
        print(command)
    return 0


def _add_format_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format")


def cmd_doctor(args: argparse.Namespace) -> int:
    report = build_doctor_report(
        root=REPO_ROOT,
        package=args.package,
        check_cli=args.check_cli,
        validate=args.validate,
    )
    if args.format == "json":
        _emit_json(report)
        return 0

    node = report["node"]
    npx = report["npx"]
    project = report["project"]
    lines = [
        f"OpenSpec package: {report['package']}",
        f"Node: {node.get('version') or 'missing'} supported={node.get('supported')}",
        f"npx: {npx.get('version') or 'missing'}",
        f"config: {project['configExists']} {project['config']}",
        f"specs: {project['specsExists']}",
        f"changes: {project['changesExists']}",
        f"schemas: {project['schemasExists']}",
        "tool mapping:",
    ]
    lines.extend(f"  {agent} -> {tool}" for agent, tool in sorted(OPENSPEC_TOOL_BY_AGENT.items()))
    generated = report.get("generatedArtifacts") or []
    if generated:
        lines.append("generated artifacts present:")
        lines.extend(f"  {path}" for path in generated)
    for check in report.get("checks") or []:
        lines.append(f"check {check.get('name')}: exit={check.get('returncode')}")
    _emit_text(lines)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    openspec_args = ["status", "--change", args.change, "--json"]
    if args.schema:
        openspec_args.extend(["--schema", args.schema])
    result = run_openspec(openspec_args, cwd=REPO_ROOT, package=args.package)
    return _emit_command_result(result, format_=args.format, success_message=f"OpenSpec status for {args.change}")


def cmd_instructions(args: argparse.Namespace) -> int:
    openspec_args = ["instructions", args.artifact, "--change", args.change, "--json"]
    if args.schema:
        openspec_args.extend(["--schema", args.schema])
    result = run_openspec(openspec_args, cwd=REPO_ROOT, package=args.package)
    return _emit_command_result(
        result,
        format_=args.format,
        success_message=f"OpenSpec instructions for {args.artifact}",
    )


def cmd_validate(args: argparse.Namespace) -> int:
    openspec_args = ["validate", "--all", "--json"]
    if args.strict:
        openspec_args.append("--strict")
    if args.concurrency is not None:
        openspec_args.extend(["--concurrency", str(args.concurrency)])
    result = run_openspec(openspec_args, cwd=REPO_ROOT, package=args.package)
    return _emit_command_result(result, format_=args.format, success_message="OpenSpec validation")


def cmd_init(args: argparse.Namespace) -> int:
    openspec_args = ["init"]
    if args.path is not None:
        openspec_args.append(str(args.path))
    if args.all_tools:
        tools_arg = "all"
    else:
        default_agents = tuple(OPENSPEC_TOOL_BY_AGENT) if not args.agent and not args.tool else tuple(args.agent)
        try:
            selected = select_openspec_tools(agents=default_agents, tools=args.tool)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        tools_arg = ",".join(selected) if selected else "none"
    openspec_args.extend(["--tools", tools_arg, "--profile", args.profile])
    if args.force:
        openspec_args.append("--force")
    argv = build_openspec_argv(openspec_args, package=args.package)
    if not args.apply:
        return _emit_dry_run(argv, format_=args.format)
    result = run_openspec(openspec_args, cwd=REPO_ROOT, package=args.package, capture=False)
    return result.returncode


def cmd_update(args: argparse.Namespace) -> int:
    openspec_args = ["update"]
    if args.path is not None:
        openspec_args.append(str(args.path))
    if args.force:
        openspec_args.append("--force")
    argv = build_openspec_argv(openspec_args, package=args.package)
    if not args.apply:
        return _emit_dry_run(argv, format_=args.format)
    result = run_openspec(openspec_args, cwd=REPO_ROOT, package=args.package, capture=False)
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenSpec workflow wrapper for repo and downstream AI tools.")
    parser.add_argument("--package", default=OPENSPEC_PACKAGE, help="OpenSpec npm package spec")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Diagnose OpenSpec toolchain and project state")
    _add_format_argument(doctor)
    doctor.add_argument("--check-cli", action="store_true", help="Run `openspec --version` through npx")
    doctor.add_argument("--validate", action="store_true", help="Run `openspec validate --all --json`")
    doctor.set_defaults(handler=cmd_doctor)

    init = subparsers.add_parser("init", help="Materialize downstream OpenSpec skills/commands locally")
    _add_format_argument(init)
    init.add_argument("--path", type=Path, help="Target directory, defaults to repo root")
    init.add_argument("-a", "--agent", action="append", default=[], help="Repo agent ID to configure")
    init.add_argument("--tool", action="append", default=[], help="Raw OpenSpec tool ID to configure")
    init.add_argument("--all-tools", action="store_true", help="Pass `--tools all` to OpenSpec")
    init.add_argument("--profile", default="core", choices=("core", "custom"), help="OpenSpec profile")
    init.add_argument("--force", action="store_true", help="Pass `--force` to OpenSpec")
    init.add_argument("--apply", action="store_true", help="Execute instead of printing the command")
    init.set_defaults(handler=cmd_init)

    update = subparsers.add_parser("update", help="Refresh generated OpenSpec AI tool artifacts")
    _add_format_argument(update)
    update.add_argument("--path", type=Path, help="Target directory, defaults to repo root")
    update.add_argument("--force", action="store_true", help="Pass `--force` to OpenSpec")
    update.add_argument("--apply", action="store_true", help="Execute instead of printing the command")
    update.set_defaults(handler=cmd_update)

    status = subparsers.add_parser("status", help="Read change artifact status as JSON")
    _add_format_argument(status)
    status.add_argument("--change", required=True, help="OpenSpec change name")
    status.add_argument("--schema", help="Schema override")
    status.set_defaults(handler=cmd_status)

    instructions = subparsers.add_parser("instructions", help="Get AI-readable next-step instructions")
    _add_format_argument(instructions)
    instructions.add_argument("artifact", nargs="?", default="apply", help="Artifact ID")
    instructions.add_argument("--change", required=True, help="OpenSpec change name")
    instructions.add_argument("--schema", help="Schema override")
    instructions.set_defaults(handler=cmd_instructions)

    validate = subparsers.add_parser("validate", help="Validate all OpenSpec specs and changes")
    _add_format_argument(validate)
    validate.add_argument("--strict", action=argparse.BooleanOptionalAction, default=True)
    validate.add_argument("--concurrency", type=int, help="Validation concurrency")
    validate.set_defaults(handler=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())