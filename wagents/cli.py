"""CLI for managing centralized AI agent assets."""

import importlib.util
import json
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from wagents import KEBAB_CASE_PATTERN, ROOT, VERSION
from wagents.catalog import CatalogNode
from wagents.context import (
    REPO_ROOT_ENV,
    bootstrap_cli_context,
    detect_install_mode,
    get_repo_root,
    get_repo_root_optional,
    resolve_repo_script,
)
from wagents.docs import docs_app, regenerate_sidebar_and_indexes
from wagents.installed_inventory import (
    InstalledSkillInventoryRow,
    collect_desired_sync_rows,
    collect_installed_inventory,
    merge_desired_with_installed,
    mirror_grok_skills_from_claude,
    skills_cli_agent_id,
)
from wagents.opencode_sessions import (
    DEFAULT_OPENCODE_DB_PATH,
    DEFAULT_OPENCODE_LOG_DIR,
    diagnose_session,
    redact_report_for_text,
)
from wagents.openspec import (
    OPENSPEC_PACKAGE,
    OPENSPEC_TOOL_BY_AGENT,
    build_doctor_report,
    build_openspec_argv,
    run_openspec,
    select_openspec_tools,
)
from wagents.output import emit_structured_output, normalize_output_format
from wagents.parsing import parse_frontmatter, to_title

# Eval adequacy (structural E3/E4 grader)
from wagents.eval_adequacy import (
    assess_eval_adequacy,
    build_adequacy_report,
    filter_high_risk,
)
from wagents.plugins import load_command_plugins
from wagents.rendering import scaffold_doc_page
from wagents.self_cmd import self_app
from wagents.site_model import (
    REPO_SOURCE,
    SUPPORTED_AGENT_IDS,
    VISUAL_ASSET_BY_ID,
    build_install_command,
    docs_asset_repo_path,
)
from wagents.telemetry import begin_command_telemetry, doctor_telemetry_check, end_command_telemetry


def _skill_creator_scripts() -> Path:
    return get_repo_root() / "skills" / "skill-creator" / "scripts"


def _skill_router_script() -> Path:
    return get_repo_root() / "skills" / "skill-router" / "scripts" / "skill_index.py"


def _run_python_script(script: Path, args: list[str]) -> int:
    repo_root = get_repo_root()
    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")
    return result.returncode


def _skill_router_args(args: list[str]) -> list[str]:
    router_args = [
        *args,
        "--home",
        str(Path.home()),
        "--cwd",
        str(Path.cwd()),
    ]
    repo_root = get_repo_root_optional()
    if repo_root is not None:
        router_args.extend(["--repo-root", str(repo_root)])
    return router_args


def _run_skill_router(args: list[str]) -> int:
    return _run_python_script(_skill_router_script(), _skill_router_args(args))


def _exit_skill_router(args: list[str], *, source: str | None = None) -> None:
    if source is not None:
        _normalize_skill_source(source)
    raise typer.Exit(code=_run_skill_router(args))


# Typer apps
app = typer.Typer(
    help="CLI for managing centralized AI agent assets",
    add_completion=True,
    rich_markup_mode="rich",
)
new_app = typer.Typer(help="Create new assets from reference templates")
app.add_typer(new_app, name="new")
app.add_typer(docs_app, name="docs")
hooks_app = typer.Typer(help="Manage hooks across skills and agents")
app.add_typer(hooks_app, name="hooks")
eval_app = typer.Typer(help="Manage and validate skill evals")
app.add_typer(eval_app, name="eval")
skills_app = typer.Typer(help="Index and search local skills")
app.add_typer(skills_app, name="skills")
catalog_app = typer.Typer(help="Catalog authoring SSOT and generated index management")
app.add_typer(catalog_app, name="catalog")
openspec_app = typer.Typer(help="Manage OpenSpec workflows and downstream AI tool setup")
app.add_typer(openspec_app, name="openspec")
opencode_app = typer.Typer(help="Diagnose OpenCode runtime state")
app.add_typer(opencode_app, name="opencode")
grok_app = typer.Typer(help="Diagnose Grok Build runtime state")
plannotator_app = typer.Typer(help="Install and verify Plannotator for Grok Build")
grok_app.add_typer(plannotator_app, name="plannotator")
app.add_typer(grok_app, name="grok")
app.add_typer(self_app, name="self")

apm_app = typer.Typer(help="APM (Microsoft Agent Package Manager) facade: materialize .apm/ from repo SSOT and doctor")
app.add_typer(apm_app, name="apm")

_PLUGIN_RESULTS = load_command_plugins(app)

PLANNOTATOR_CORE_SYNC_COMMAND = [
    "npx",
    "-y",
    "skills",
    "add",
    "backnotprop/plannotator/apps/skills/core",
    "--skill",
    "plannotator-review",
    "--skill",
    "plannotator-annotate",
    "--skill",
    "plannotator-last",
    "-y",
    "-g",
    "-a",
    skills_cli_agent_id("grok"),
]
PLANNOTATOR_EXTRAS_SYNC_COMMAND = [
    "npx",
    "-y",
    "skills",
    "add",
    "backnotprop/plannotator/apps/skills",
    "--skill",
    "plannotator-compound",
    "--skill",
    "plannotator-setup-goal",
    "--skill",
    "plannotator-visual-explainer",
    "-y",
    "-g",
    "-a",
    skills_cli_agent_id("grok"),
]

OUTPUT_FORMATS = ("text", "json", "jsonl")
SKILL_SOURCES = (
    "all",
    "repo",
    "project",
    "codex",
    "global",
    "claude-code",
    "gemini-cli",
    "github-copilot",
    "opencode",
    "plugin",
)
LOCAL_MCP_DIR_NAMES = {"archives", "cache", "notes", "secrets", "servers"}


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"wagents {VERSION}")
        raise typer.Exit()


def _command_telemetry_label(ctx: typer.Context | None = None) -> str:
    if ctx is not None and ctx.invoked_subcommand:
        return ctx.invoked_subcommand
    return " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "wagents"


@app.callback()
def main(
    ctx: typer.Context,
    version: bool | None = typer.Option(None, "--version", callback=version_callback, help="Show version and exit"),
    repo_root: Annotated[
        Path | None,
        typer.Option(
            "--repo-root",
            envvar=REPO_ROOT_ENV,
            help="Agents repository root (auto-discovered from cwd when omitted)",
        ),
    ] = None,
):
    """CLI for managing centralized AI agent assets."""
    begin_command_telemetry(_command_telemetry_label(ctx))
    bootstrap_cli_context(repo_root)


def _normalize_output_format(format_: str) -> str:
    return normalize_output_format(format_)


def _emit_structured_output(
    format_: str,
    *,
    text_lines: list[str] | None = None,
    json_data: dict | list | None = None,
    jsonl_records: list[dict] | None = None,
) -> None:
    emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data=json_data,
        jsonl_records=jsonl_records,
    )


def _format_error(source: str, message: str) -> str:
    """Render a validation-style error for text output."""
    return f"{source}: {message}"


def _is_git_ignored(path: Path) -> bool:
    """Return whether *path* is ignored by this repo's git rules."""
    try:
        rel_path = path.relative_to(ROOT)
    except ValueError:
        return False
    candidates = [str(rel_path)]
    if path.is_dir():
        candidates.append(str(rel_path / "__wagents_check__"))
    for candidate in candidates:
        try:
            result = subprocess.run(
                ["git", "-C", str(ROOT), "check-ignore", "-q", candidate],
                capture_output=True,
                check=False,
            )
        except OSError:
            return False
        if result.returncode == 0:
            return True
    return False


def _is_local_mcp_dir(path: Path) -> bool:
    """Return whether an MCP subdirectory is reserved for local machine assets."""
    return path.name in LOCAL_MCP_DIR_NAMES or _is_git_ignored(path)


def _normalize_skill_source(source: str) -> str:
    """Normalize and validate a requested skill source."""
    normalized = source.lower()
    if normalized not in SKILL_SOURCES:
        typer.echo(
            f"Error: unsupported source '{source}'. Use one of: {', '.join(SKILL_SOURCES)}",
            err=True,
        )
        raise typer.Exit(code=1)
    return normalized


def _collect_hooks():
    """Collect hooks from settings, skills, and agents."""
    from wagents.parsing import Hook, extract_hooks

    all_hooks: list[Hook] = []

    for settings_name in ["settings.json", "settings.local.json"]:
        settings_file = ROOT / ".claude" / settings_name
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text())
                hooks_dict = data.get("hooks", {})
                all_hooks.extend(extract_hooks(settings_name, hooks_dict))
            except Exception as e:
                typer.echo(
                    f"Warning: could not parse {settings_name}: {e}",
                    err=True,
                )

    skills_dir = ROOT / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            try:
                fm, _ = parse_frontmatter(skill_file.read_text())
                hooks_dict = fm.get("hooks", {})
                if hooks_dict:
                    all_hooks.extend(extract_hooks(f"skill:{skill_dir.name}", hooks_dict))
            except Exception:
                pass

    agents_dir = ROOT / "agents"
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob("*.md")):
            try:
                fm, _ = parse_frontmatter(agent_file.read_text())
                hooks_dict = fm.get("hooks", {})
                if hooks_dict:
                    all_hooks.extend(extract_hooks(f"agent:{agent_file.stem}", hooks_dict))
            except Exception:
                pass

    hook_registry_file = ROOT / "config" / "hook-registry.json"
    if hook_registry_file.exists():
        try:
            hook_registry = json.loads(hook_registry_file.read_text())
            for hook in hook_registry.get("hooks", []):
                if not isinstance(hook, dict):
                    continue
                all_hooks.append(
                    Hook(
                        source=f"registry:{hook.get('id', 'unknown')}",
                        event=str(hook.get("logical_event", "")),
                        matcher=str(hook.get("matcher", "")),
                        handler_type="command",
                        command=str(hook.get("command", "")),
                        prompt="",
                        harness_support=[str(item) for item in hook.get("harnesses", [])],
                        rendered_event="",
                        blocking_mode=str(hook.get("mode", "")),
                    )
                )
        except Exception as e:
            typer.echo(f"Warning: could not parse hook-registry.json: {e}", err=True)

    return all_hooks


def _parse_min_python_version(spec: str) -> tuple[int, int] | None:
    """Extract a minimum major/minor version from a requires-python spec."""
    match = re.search(r">=\s*(\d+)\.(\d+)", spec)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _parse_semver(raw: str) -> tuple[int, int, int] | None:
    """Extract a semantic version from a CLI version string."""
    match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", raw)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _read_command_version(command: list[str]) -> tuple[int, int, int] | None:
    """Read a command version as a semantic version tuple."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError:
        return None

    return _parse_semver(result.stdout or result.stderr)


def _version_satisfies_token(version: tuple[int, int, int], token: str) -> bool | None:
    """Evaluate a semver token against a version."""
    token = token.strip()
    if not token:
        return True
    if token.startswith("^"):
        minimum = _parse_semver(token[1:])
        if minimum is None:
            return None
        maximum = (minimum[0] + 1, 0, 0)
        return minimum <= version < maximum

    for prefix in (">=", "<=", ">", "<"):
        if token.startswith(prefix):
            target = _parse_semver(token[len(prefix) :])
            if target is None:
                return None
            if prefix == ">=":
                return version >= target
            if prefix == "<=":
                return version <= target
            if prefix == ">":
                return version > target
            return version < target

    exact = _parse_semver(token)
    if exact is None:
        return None
    return version == exact


def _version_satisfies_range(version: tuple[int, int, int], spec: str) -> bool | None:
    """Evaluate a semver range with || unions and space-delimited comparators."""
    saw_unknown = False
    clauses = [clause.strip() for clause in spec.split("||") if clause.strip()]
    if not clauses:
        return None

    for clause in clauses:
        clause_unknown = False
        clause_matches = True
        for token in clause.split():
            result = _version_satisfies_token(version, token)
            if result is None:
                clause_unknown = True
                clause_matches = False
                break
            if not result:
                clause_matches = False
                break
        if clause_matches:
            return True
        if clause_unknown:
            saw_unknown = True

    if saw_unknown:
        return None
    return False


def _parse_package_manager_pin(package_manager: str) -> tuple[str, tuple[int, int, int]] | None:
    """Parse a packageManager pin like pnpm@10.11.1."""
    manager, separator, version = package_manager.partition("@")
    if not separator:
        return None
    parsed_version = _parse_semver(version)
    if parsed_version is None:
        return None
    return manager, parsed_version


def _make_doctor_check(
    name: str,
    status: str,
    summary: str,
    remediation: str | None = None,
) -> dict[str, str]:
    """Create a normalized doctor check record."""
    check = {"name": name, "status": status, "summary": summary}
    if remediation:
        check["remediation"] = remediation
    return check


def _collect_doctor_checks() -> list[dict[str, str]]:
    """Collect environment and toolchain diagnostics for the repo."""
    checks: list[dict[str, str]] = []
    tool_paths: dict[str, str | None] = {}

    pyproject_file = ROOT / "pyproject.toml"
    requires_python = ""
    if pyproject_file.exists():
        data = tomllib.loads(pyproject_file.read_text())
        requires_python = str(data.get("project", {}).get("requires-python", ""))

    min_version = _parse_min_python_version(requires_python)
    current_version = (sys.version_info.major, sys.version_info.minor)
    if min_version is None:
        checks.append(
            _make_doctor_check(
                "python-version",
                "warn",
                "Could not determine required Python version from pyproject.toml",
                "Set project.requires-python in pyproject.toml.",
            )
        )
    elif current_version >= min_version:
        checks.append(
            _make_doctor_check(
                "python-version",
                "ok",
                f"Python {current_version[0]}.{current_version[1]} satisfies {requires_python}",
            )
        )
    else:
        checks.append(
            _make_doctor_check(
                "python-version",
                "fail",
                f"Python {current_version[0]}.{current_version[1]} does not satisfy {requires_python}",
                "Install a compatible Python version and run commands through uv.",
            )
        )

    tool_checks = [
        ("uv", "fail", "Install uv: https://docs.astral.sh/uv/"),
        ("node", "warn", "Install Node.js to use docs and install workflows."),
        ("npx", "warn", "Install Node.js so npx is available for wagents install."),
        ("pnpm", "warn", "Install pnpm to manage docs dependencies."),
    ]
    for tool_name, missing_status, remediation in tool_checks:
        tool_path = shutil.which(tool_name)
        tool_paths[tool_name] = tool_path
        if tool_path:
            checks.append(_make_doctor_check(tool_name, "ok", f"Found at {tool_path}"))
        else:
            checks.append(
                _make_doctor_check(
                    tool_name,
                    missing_status,
                    f"{tool_name} is not available on PATH",
                    remediation,
                )
            )

    docs_dir = ROOT / "docs"
    package_json = docs_dir / "package.json"
    lock_file = docs_dir / "pnpm-lock.yaml"
    node_modules = docs_dir / "node_modules"
    docs_package_data: dict[str, object] | None = None
    docs_package_error: str | None = None
    if package_json.exists():
        try:
            docs_package_data = json.loads(package_json.read_text())
        except json.JSONDecodeError as exc:
            docs_package_error = str(exc)

    if tool_paths.get("node") and package_json.exists():
        if docs_package_error:
            checks.append(
                _make_doctor_check(
                    "node-version",
                    "warn",
                    f"Could not parse docs/package.json to determine supported Node range ({docs_package_error})",
                    "Fix docs/package.json so wagents doctor can validate Node support.",
                )
            )
        else:
            node_range = str((docs_package_data or {}).get("engines", {}).get("node", "")).strip()
            node_version = _read_command_version(["node", "--version"])
            if not node_range:
                checks.append(
                    _make_doctor_check(
                        "node-version",
                        "warn",
                        "docs/package.json does not declare engines.node",
                        "Set docs/package.json engines.node to the supported Node semver range.",
                    )
                )
            elif node_version is None:
                checks.append(
                    _make_doctor_check(
                        "node-version",
                        "warn",
                        "Could not determine the installed Node.js version",
                        "Run node --version to verify your Node.js installation.",
                    )
                )
            else:
                supported = _version_satisfies_range(node_version, node_range)
                version_text = ".".join(str(part) for part in node_version)
                if supported is True:
                    checks.append(
                        _make_doctor_check(
                            "node-version",
                            "ok",
                            f"Node {version_text} satisfies docs/package.json engines.node ({node_range})",
                        )
                    )
                elif supported is False:
                    checks.append(
                        _make_doctor_check(
                            "node-version",
                            "warn",
                            f"Node {version_text} does not satisfy docs/package.json engines.node ({node_range})",
                            "Install a supported Node.js version before working on docs.",
                        )
                    )
                else:
                    checks.append(
                        _make_doctor_check(
                            "node-version",
                            "warn",
                            (
                                "Could not evaluate "
                                f"Node {version_text} against docs/package.json engines.node ({node_range})"
                            ),
                            "Use a semver range in docs/package.json that wagents doctor can evaluate.",
                        )
                    )

    if tool_paths.get("pnpm") and package_json.exists():
        if docs_package_error:
            checks.append(
                _make_doctor_check(
                    "pnpm-version",
                    "warn",
                    f"Could not parse docs/package.json to determine the pnpm pin ({docs_package_error})",
                    "Fix docs/package.json so wagents doctor can validate the pnpm pin.",
                )
            )
        else:
            package_manager = str((docs_package_data or {}).get("packageManager", "")).strip()
            parsed_pin = _parse_package_manager_pin(package_manager)
            pnpm_version = _read_command_version(["pnpm", "--version"])
            if not package_manager:
                checks.append(
                    _make_doctor_check(
                        "pnpm-version",
                        "warn",
                        "docs/package.json does not declare packageManager",
                        "Set docs/package.json packageManager to the supported pnpm version.",
                    )
                )
            elif parsed_pin is None or parsed_pin[0] != "pnpm":
                checks.append(
                    _make_doctor_check(
                        "pnpm-version",
                        "warn",
                        f"docs/package.json packageManager is not a pnpm pin ({package_manager})",
                        "Set docs/package.json packageManager to a pnpm@<version> pin.",
                    )
                )
            elif pnpm_version is None:
                checks.append(
                    _make_doctor_check(
                        "pnpm-version",
                        "warn",
                        "Could not determine the installed pnpm version",
                        "Run pnpm --version to verify your pnpm installation.",
                    )
                )
            else:
                version_text = ".".join(str(part) for part in pnpm_version)
                expected_text = ".".join(str(part) for part in parsed_pin[1])
                if pnpm_version == parsed_pin[1]:
                    checks.append(
                        _make_doctor_check(
                            "pnpm-version",
                            "ok",
                            f"pnpm {version_text} matches docs/package.json packageManager ({package_manager})",
                        )
                    )
                else:
                    checks.append(
                        _make_doctor_check(
                            "pnpm-version",
                            "warn",
                            f"pnpm {version_text} does not match docs/package.json packageManager ({package_manager})",
                            f"Install pnpm {expected_text} before working on docs.",
                        )
                    )

    if not docs_dir.exists():
        checks.append(
            _make_doctor_check(
                "docs-deps",
                "warn",
                "docs directory is missing",
                "Restore docs/ if you intend to build the documentation site.",
            )
        )
    elif not package_json.exists() or not lock_file.exists():
        checks.append(
            _make_doctor_check(
                "docs-deps",
                "warn",
                "docs dependency manifests are incomplete",
                "Ensure docs/package.json and docs/pnpm-lock.yaml both exist.",
            )
        )
    elif not node_modules.exists():
        checks.append(
            _make_doctor_check(
                "docs-deps",
                "warn",
                "docs/node_modules is missing",
                "Run pnpm --dir docs install.",
            )
        )
    else:
        node_modules_mtime = node_modules.stat().st_mtime
        stale_inputs = [path.name for path in (package_json, lock_file) if path.stat().st_mtime > node_modules_mtime]
        if stale_inputs:
            checks.append(
                _make_doctor_check(
                    "docs-deps",
                    "warn",
                    f"docs/node_modules may be stale relative to {', '.join(stale_inputs)}",
                    "Run pnpm --dir docs install to refresh docs dependencies.",
                )
            )
        else:
            checks.append(
                _make_doctor_check(
                    "docs-deps",
                    "ok",
                    "docs dependency manifests and node_modules look present",
                )
            )

    pre_commit_config = ROOT / ".pre-commit-config.yaml"
    if pre_commit_config.exists():
        pre_commit_path = shutil.which("pre-commit")
        if pre_commit_path:
            checks.append(_make_doctor_check("pre-commit", "ok", f"Found at {pre_commit_path}"))
        else:
            checks.append(
                _make_doctor_check(
                    "pre-commit",
                    "warn",
                    ".pre-commit-config.yaml exists but pre-commit is not available on PATH",
                    "Install pre-commit to run the repository hooks locally.",
                )
            )

    if importlib.util.find_spec("playwright") is None:
        checks.append(
            _make_doctor_check(
                "playwright-python",
                "warn",
                "Python Playwright package is not installed",
                "Run uv add --dev playwright.",
            )
        )
    else:
        checks.append(
            _make_doctor_check(
                "playwright-python",
                "ok",
                "Python Playwright package is installed",
            )
        )

    browser_cache_candidates = [
        Path.home() / "Library/Caches/ms-playwright",
        Path.home() / ".cache/ms-playwright",
    ]
    browser_cache = next((candidate for candidate in browser_cache_candidates if candidate.exists()), None)
    if browser_cache and any(browser_cache.iterdir()):
        checks.append(
            _make_doctor_check(
                "playwright-browsers",
                "ok",
                f"Playwright browser cache found at {browser_cache}",
            )
        )
    else:
        checks.append(
            _make_doctor_check(
                "playwright-browsers",
                "warn",
                "No Playwright browser cache detected",
                "Run uv run playwright install chromium.",
            )
        )

    wagents_path = shutil.which("wagents")
    checks.append(
        _make_doctor_check(
            "wagents-install-mode",
            "ok",
            detect_install_mode(),
        )
    )
    checks.append(
        _make_doctor_check(
            "wagents-binary",
            "ok" if wagents_path else "warn",
            (
                f"Found at {wagents_path}"
                if wagents_path
                else "wagents is not on PATH (uv run wagents still works in clone)"
            ),
        )
    )
    discovered = get_repo_root_optional()
    checks.append(
        _make_doctor_check(
            "repo-discovery",
            "ok" if discovered else "warn",
            str(discovered) if discovered else f"No agents repo discovered; set {REPO_ROOT_ENV} or run inside clone",
        )
    )
    for plugin in _PLUGIN_RESULTS:
        checks.append(
            _make_doctor_check(
                f"plugin:{plugin.name}",
                plugin.status,
                plugin.summary,
            )
        )
    checks.append(doctor_telemetry_check())

    if pyproject_file.exists():
        pyproject_data = tomllib.loads(pyproject_file.read_text())
        tool_ruff = pyproject_data.get("tool", {}).get("ruff")
        tool_ty = pyproject_data.get("tool", {}).get("ty")
        checks.append(
            _make_doctor_check(
                "python-tooling-config",
                "ok" if tool_ruff and tool_ty else "fail",
                (
                    "pyproject.toml defines [tool.ruff] and [tool.ty]"
                    if tool_ruff and tool_ty
                    else "Missing [tool.ruff] or [tool.ty] in pyproject.toml"
                ),
                "Add Ruff and ty configuration to pyproject.toml.",
            )
        )
    else:
        checks.append(
            _make_doctor_check(
                "python-tooling-config",
                "fail",
                "pyproject.toml is missing",
                "Restore pyproject.toml with [tool.ruff] and [tool.ty] sections.",
            )
        )

    for tool_name, version_args in (("ruff", ["--version"]), ("ty", ["--version"])):
        if not tool_paths.get("uv"):
            checks.append(
                _make_doctor_check(
                    f"{tool_name}-tooling",
                    "warn",
                    f"Cannot verify {tool_name} without uv on PATH",
                    "Install uv and run uv sync before type-checking or linting.",
                )
            )
            continue
        try:
            result = subprocess.run(
                ["uv", "run", tool_name, *version_args],
                capture_output=True,
                text=True,
                check=False,
                cwd=ROOT,
            )
        except OSError:
            checks.append(
                _make_doctor_check(
                    f"{tool_name}-tooling",
                    "warn",
                    f"Could not execute uv run {tool_name}",
                    f"Run uv sync and verify {tool_name} is listed in dependency-groups.dev.",
                )
            )
            continue
        version_line = (result.stdout or result.stderr).strip().splitlines()[:1]
        version_text = version_line[0] if version_line else "unknown version"
        checks.append(
            _make_doctor_check(
                f"{tool_name}-tooling",
                "ok" if result.returncode == 0 else "fail",
                version_text if result.returncode == 0 else f"uv run {tool_name} failed",
                f"Run uv sync and uv run {tool_name} --version to repair the dev toolchain.",
            )
        )

    return checks


def _emit_doctor_report(format_: str, checks: list[dict[str, str]]) -> None:
    """Emit doctor results in text, json, or jsonl format."""
    counts = {
        "ok": sum(1 for check in checks if check["status"] == "ok"),
        "warn": sum(1 for check in checks if check["status"] == "warn"),
        "fail": sum(1 for check in checks if check["status"] == "fail"),
    }
    json_result = {
        "ok": counts["fail"] == 0,
        "summary": {
            "total": len(checks),
            **counts,
        },
        "checks": checks,
    }
    text_lines = [
        (f"Doctor summary: {len(checks)} checks, {counts['ok']} ok, {counts['warn']} warn, {counts['fail']} fail")
    ]
    for check in checks:
        line = f"{check['status'].upper():<4} {check['name']:<20} {check['summary']}"
        if check.get("remediation"):
            line = f"{line} Fix: {check['remediation']}"
        text_lines.append(line)

    jsonl_records: list[dict[str, object]] = [{"type": "check", **check} for check in checks]
    jsonl_records.append({"type": "summary", **json_result["summary"], "ok": json_result["ok"]})

    _emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data=json_result,
        jsonl_records=jsonl_records,
    )


@app.command()
def doctor(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Check environment and toolchain health for this repo."""
    checks = _collect_doctor_checks()
    _emit_doctor_report(format_, checks)
    if any(check["status"] == "fail" for check in checks):
        raise typer.Exit(code=1)


def validate_name(name: str) -> None:
    """Validate asset name is kebab-case and within length limit."""
    if not KEBAB_CASE_PATTERN.match(name):
        typer.echo(f"Error: name must be kebab-case (got '{name}')", err=True)
        raise typer.Exit(code=1)
    if len(name) > 64:
        typer.echo("Error: name exceeds 64 characters", err=True)
        raise typer.Exit(code=1)


@new_app.command("skill")
def new_skill(
    name: str,
    no_docs: bool = typer.Option(False, "--no-docs", help="Skip docs page scaffold"),
):
    """Create a new skill from template."""
    scaffold_script = _skill_creator_scripts() / "scaffold_skill.py"
    code = _run_python_script(scaffold_script, [name])
    if code != 0:
        raise typer.Exit(code=code)
    skill_file = ROOT / "skills" / name / "SKILL.md"
    content = skill_file.read_text()

    if not no_docs:
        fm, body = parse_frontmatter(content)
        node = CatalogNode(
            kind="skill",
            id=name,
            title=to_title(name),
            description=str(fm.get("description", "")),
            metadata=fm,
            body=body,
            source_path=f"skills/{name}/SKILL.md",
        )
        scaffold_doc_page(node)
        regenerate_sidebar_and_indexes()
        typer.echo("Regenerated sidebar and index pages")


@new_app.command("agent")
def new_agent(
    name: str,
    no_docs: bool = typer.Option(False, "--no-docs", help="Skip docs page scaffold"),
):
    """Create a new agent from template."""
    validate_name(name)
    agents_dir = ROOT / "agents"
    agent_file = agents_dir / f"{name}.md"

    if agent_file.exists():
        typer.echo(f"Error: {agent_file} already exists", err=True)
        raise typer.Exit(code=1)

    agents_dir.mkdir(parents=True, exist_ok=True)

    title = to_title(name)
    content = f"""---
name: {name}
description: TODO — When Claude should delegate to this agent

# tools: Read, Glob, Grep, Bash            # Tool allowlist (inherits all if omitted)
# disallowedTools: Write, Edit              # Tool denylist (removed from inherited set)
# model: sonnet                             # Model: sonnet | opus | haiku | inherit
# permissionMode: default                   # default | acceptEdits | delegate | dontAsk | bypassPermissions | plan
# maxTurns: 50                              # Maximum agentic turns before stopping
# skills:                                   # Skills preloaded into agent context
#   - skill-name
# mcpServers:                               # MCP servers available to this agent
#   - server-name
# memory: project                           # Persistent memory: user | project | local
# hooks:                                    # Lifecycle hooks scoped to this agent
#   PreToolUse:
#     - matcher: Bash
#       hooks: [{{command: "echo check"}}]
---

# {title}

This is the agent's system prompt. Everything below the frontmatter
is injected as instructions when this agent is spawned.

## Capabilities

Describe what this agent specializes in.

## Guidelines

Rules and constraints for this agent's behavior.
"""

    agent_file.write_text(content)
    typer.echo(f"Created agents/{name}.md")

    if not no_docs:
        fm, body = parse_frontmatter(content)
        node = CatalogNode(
            kind="agent",
            id=name,
            title=to_title(name),
            description=str(fm.get("description", "")),
            metadata=fm,
            body=body,
            source_path=f"agents/{name}.md",
        )
        scaffold_doc_page(node)
        regenerate_sidebar_and_indexes()
        typer.echo("Regenerated sidebar and index pages")


@new_app.command("mcp")
def new_mcp(
    name: str,
    no_docs: bool = typer.Option(False, "--no-docs", help="Skip docs page scaffold"),
):
    """Create a new MCP server from template."""
    validate_name(name)
    mcp_dir = ROOT / "mcp" / name

    if mcp_dir.exists():
        typer.echo(f"Error: {mcp_dir} already exists", err=True)
        raise typer.Exit(code=1)

    mcp_dir.mkdir(parents=True, exist_ok=True)

    title = to_title(name)

    # Create server.py
    server_content = f'''"""MCP server: {name}."""

from fastmcp import FastMCP

mcp = FastMCP("{title}")


@mcp.tool
def hello(query: str) -> str:
    """Example tool — replace with your implementation."""
    return f"Hello from {name}: {{query}}"
'''
    (mcp_dir / "server.py").write_text(server_content)

    # Create pyproject.toml
    pyproject_content = f"""[project]
name = "mcp-{name}"
version = "0.1.0"
description = "TODO — What this MCP server does"
requires-python = ">=3.13"
dependencies = ["fastmcp>=2"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
    (mcp_dir / "pyproject.toml").write_text(pyproject_content)

    # Create fastmcp.json
    fastmcp_config = {
        "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
        "source": {"path": "server.py", "entrypoint": "mcp"},
        "environment": {"type": "uv"},
    }
    (mcp_dir / "fastmcp.json").write_text(json.dumps(fastmcp_config, indent=2) + "\n")

    # Update root pyproject.toml if needed
    root_pyproject = ROOT / "pyproject.toml"
    content = root_pyproject.read_text()

    workspace_member = f"mcp/{name}"
    if "[tool.uv.workspace]" not in content:
        if not content.endswith("\n"):
            content += "\n"
        content += f'\n[tool.uv.workspace]\nmembers = ["{workspace_member}"]\n'
        root_pyproject.write_text(content)
    elif f'"{workspace_member}"' not in content and f"'{workspace_member}'" not in content:
        workspace_match = re.search(r"(?ms)^\[tool\.uv\.workspace\]\n(?P<body>.*?)(?=^\[|\Z)", content)
        if workspace_match:
            body = workspace_match.group("body")
            members_match = re.search(r"(?ms)^members\s*=\s*\[(?P<members>.*?)\]", body)
            if members_match:
                replacement = f"members = [{members_match.group('members').strip()}]"
                if members_match.group("members").strip():
                    replacement = replacement[:-1] + f', "{workspace_member}"]'
                else:
                    replacement = f'members = ["{workspace_member}"]'
                start = workspace_match.start("body") + members_match.start()
                end = workspace_match.start("body") + members_match.end()
                content = content[:start] + replacement + content[end:]
            else:
                insert_at = workspace_match.start("body")
                content = content[:insert_at] + f'members = ["{workspace_member}"]\n' + content[insert_at:]
            root_pyproject.write_text(content)

    typer.echo(f"Created mcp/{name}/ with server.py, pyproject.toml, and fastmcp.json")

    if not no_docs:
        metadata = {
            "project": {
                "name": f"mcp-{name}",
                "version": "0.1.0",
                "description": "TODO — What this MCP server does",
                "requires-python": ">=3.13",
                "dependencies": ["fastmcp>=2"],
            },
            "fastmcp_config": fastmcp_config,
        }
        node = CatalogNode(
            kind="mcp",
            id=name,
            title=to_title(name),
            description="TODO — What this MCP server does",
            metadata=metadata,
            body=server_content,
            source_path=f"mcp/{name}/server.py",
        )
        scaffold_doc_page(node)
        regenerate_sidebar_and_indexes()
        typer.echo("Regenerated sidebar and index pages")


@app.command()
def validate(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Validate all skills and agents."""
    script = resolve_repo_script("scripts/validate/validate_repo.py")
    raise typer.Exit(
        code=_run_python_script(
            script,
            ["--format", format_, "--repo-root", str(ROOT)],
        )
    )


SUPPORTED_AGENTS = list(SUPPORTED_AGENT_IDS)
UNRESOLVED_PROVENANCE = frozenset({"curated-unresolved", "read-only-discovered"})


def _select_sync_agents(agent: list[str] | None, all_agents: bool) -> tuple[str, ...]:
    """Resolve sync target agents."""
    if agent and all_agents:
        typer.echo("Error: use --agent or --all-agents, not both.", err=True)
        raise typer.Exit(code=1)
    if agent:
        normalized: list[str] = []
        for item in agent:
            if item not in SUPPORTED_AGENTS:
                typer.echo(
                    f"Error: unknown agent '{item}'. Supported: {', '.join(SUPPORTED_AGENTS)}",
                    err=True,
                )
                raise typer.Exit(code=1)
            normalized.append(item)
        return tuple(normalized)
    return tuple(SUPPORTED_AGENTS)


def _row_targets_agent(row: InstalledSkillInventoryRow, agent_id: str) -> bool:
    """Return whether a row should be considered for a target harness."""
    return not row.target_agents or agent_id in row.target_agents


def _command_text(argv: list[str]) -> str:
    """Render a shell-safe command preview."""
    rendered: list[str] = []
    for part in argv:
        if part == "*":
            rendered.append('"*"')
        else:
            rendered.append(shlex.quote(part))
    return " ".join(rendered)


def _sync_command_groups(rows: list[InstalledSkillInventoryRow], agent_id: str) -> list[dict[str, object]]:
    """Group missing skills into exact install commands for one harness."""
    grouped_named: dict[str, list[str]] = {}
    grouped_modes: dict[tuple[str, str], InstalledSkillInventoryRow] = {}
    commands: list[dict[str, object]] = []
    for row in rows:
        if row.selector_mode == "named":
            grouped_named.setdefault(row.install_source, []).append(row.name)
            continue
        grouped_modes[row.install_source, row.selector_mode] = row

    for install_source, names in sorted(grouped_named.items()):
        argv = ["npx", "skills", "add", install_source]
        for name in sorted(set(names)):
            argv.extend(["--skill", name])
        argv.extend(["-y", "-g", "-a", skills_cli_agent_id(agent_id)])
        commands.append({"argv": argv, "text": _command_text(argv)})

    for (_, selector_mode), row in sorted(grouped_modes.items()):
        argv = ["npx", "skills", "add", row.install_source]
        if selector_mode == "wildcard":
            argv.extend(["--skill", "*"])
        argv.extend(["-y", "-g", "-a", skills_cli_agent_id(agent_id)])
        commands.append({"argv": argv, "text": _command_text(argv)})

    return commands


def _sync_row_summary(row: InstalledSkillInventoryRow) -> str:
    """Render a compact sync summary line."""
    suffix = ""
    has_unresolved_reason = row.provenance_status in UNRESOLVED_PROVENANCE and row.unresolved_reason
    has_source_suffix = row.provenance_status in {"installed-external", "verified-curated-external"} and row.source
    if has_unresolved_reason:
        suffix = f" — {row.unresolved_reason}"
    elif has_source_suffix:
        suffix = f" — {row.source}"
    return f"{row.name} [{row.provenance_status}]{suffix}"


def _build_sync_report(
    target_agents: tuple[str, ...],
    *,
    include_installed: bool,
) -> dict[str, object]:
    """Build dry-run/apply data for additive skill sync."""
    # Always collect the full cross-harness inventory so a skill present in any
    # harness is visible when checking what is missing in the requested targets.
    snapshot = collect_installed_inventory()
    merged = merge_desired_with_installed(snapshot, collect_desired_sync_rows())
    report_agents: list[dict[str, object]] = []
    query_by_agent = {query.agent_id: query for query in snapshot.queries}

    verified_rows = [row for row in merged.rows if row.is_repo_owned() or row.is_verified_curated()]
    optional_installed = [row for row in merged.rows if row.provenance_status == "installed-external"]
    unresolved_rows = [row for row in merged.rows if row.provenance_status in UNRESOLVED_PROVENANCE]

    for agent_id in target_agents:
        query = query_by_agent.get(agent_id)
        if query is not None and not query.ok:
            report_agents.append({
                "agent": agent_id,
                "error": query.error,
                "warning": "",
                "missing": [],
                "already_present": [],
                "unresolved": [],
                "skipped": [],
                "commands": [],
            })
            continue

        missing: list[InstalledSkillInventoryRow] = []
        already_present: list[InstalledSkillInventoryRow] = []
        unresolved: list[InstalledSkillInventoryRow] = []
        skipped: list[InstalledSkillInventoryRow] = []

        for row in verified_rows:
            if not _row_targets_agent(row, agent_id):
                skipped.append(row)
                continue
            if agent_id in row.installed_agents:
                already_present.append(row)
            else:
                missing.append(row)

        for row in optional_installed:
            if not include_installed:
                skipped.append(row)
                continue
            if agent_id in row.installed_agents:
                already_present.append(row)
            elif row.is_installable():
                missing.append(row)
            else:
                unresolved.append(row)

        for row in unresolved_rows:
            if include_installed or _row_targets_agent(row, agent_id):
                unresolved.append(row)
            else:
                skipped.append(row)

        command_groups = _sync_command_groups(missing, agent_id)
        report_agents.append({
            "agent": agent_id,
            "error": "",
            "warning": query.error if query is not None and query.ok else "",
            "missing": [_sync_row_summary(row) for row in sorted(missing, key=lambda item: item.name)],
            "already_present": [_sync_row_summary(row) for row in sorted(already_present, key=lambda item: item.name)],
            "unresolved": [_sync_row_summary(row) for row in sorted(unresolved, key=lambda item: item.name)],
            "skipped": [_sync_row_summary(row) for row in sorted(skipped, key=lambda item: item.name)],
            "commands": [command["text"] for command in command_groups],
            "_command_argvs": [command["argv"] for command in command_groups],
        })

    return {
        "inventory_count": len(merged.rows),
        "include_installed": include_installed,
        "agents": report_agents,
    }


def _emit_sync_report(report: dict[str, object], *, dry_run: bool, format_: str = "text") -> None:
    """Emit a skills sync report in text, json, or jsonl format."""
    mode = "dry-run" if dry_run else "apply"
    agent_reports = cast("list[dict[str, object]]", report.get("agents") or [])
    json_payload: dict[str, object] = {
        "mode": mode,
        "inventory_count": report.get("inventory_count"),
        "include_installed": report.get("include_installed"),
        "agents": [
            {key: value for key, value in agent_payload.items() if not str(key).startswith("_")}
            for agent_payload in agent_reports
        ],
    }
    if format_ != "text":
        _emit_structured_output(
            format_,
            json_data=json_payload,
            jsonl_records=[{"type": "skills-sync", **json_payload}],
        )
        return

    typer.echo(f"wagents skills sync ({mode})")
    typer.echo(f"Inventory rows: {report['inventory_count']}")
    typer.echo("")
    for agent_payload in agent_reports:
        typer.echo(f"[{agent_payload['agent']}]")
        error = str(agent_payload.get("error") or "")
        if error:
            typer.echo(f"  error: {error}")
            typer.echo("")
            continue
        warning = str(agent_payload.get("warning") or "")
        if warning:
            typer.echo(f"  warning: {warning}")
        for key in ["missing", "already_present", "unresolved", "skipped"]:
            rows = cast("list[str]", agent_payload.get(key) or [])
            typer.echo(f"  {key.replace('_', '-')} ({len(rows)})")
            for row in rows:
                typer.echo(f"    - {row}")
        commands = cast("list[str]", agent_payload.get("commands") or [])
        typer.echo(f"  commands ({len(commands)})")
        for command in commands:
            typer.echo(f"    {command}")
        typer.echo("")


@app.command()
def install(
    skills: Annotated[list[str] | None, typer.Argument(help="Skill name(s) to install (omit for all)")] = None,
    agent: Annotated[list[str] | None, typer.Option("-a", "--agent", help="Target agent(s), repeatable")] = None,
    global_: bool = typer.Option(True, "-g", "--global/--local", help="Install globally vs project-local"),
    list_: bool = typer.Option(False, "--list", help="List available skills without installing"),
    copy: bool = typer.Option(False, "--copy", help="Copy files instead of symlinking"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation prompts"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Install skills into agent platforms via npx skills."""
    import shutil
    import subprocess

    if not shutil.which("npx"):
        typer.echo("Error: npx not found. Install Node.js first.", err=True)
        raise typer.Exit(code=1)

    cmd = ["npx", "-y", "skills", "add", REPO_SOURCE]

    if list_:
        cmd.append("--list")
    else:
        # Skills
        if skills:
            for s in skills:
                cmd.extend(["--skill", s])
        else:
            cmd.extend(["--skill", "*"])

        # Agents
        if agent:
            for a in agent:
                if a not in SUPPORTED_AGENTS:
                    typer.echo(
                        f"Error: unknown agent '{a}'. Supported: {', '.join(SUPPORTED_AGENTS)}",
                        err=True,
                    )
                    raise typer.Exit(code=1)
                cmd.extend(["-a", skills_cli_agent_id(a)])
        else:
            cmd.extend(["--agent", "*"])

        # Flags
        if global_:
            cmd.append("-g")
        if copy:
            cmd.append("--copy")
        if yes:
            cmd.append("-y")

    capture = _normalize_output_format(format_) != "text"
    result = subprocess.run(cmd, capture_output=capture, text=True)
    mirrored = 0
    if result.returncode == 0 and agent and "grok" in agent:
        mirrored = mirror_grok_skills_from_claude()
    if capture:
        payload: dict[str, object] = {
            "argv": cmd,
            "returncode": result.returncode,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "mirrored_grok_skills": mirrored,
        }
        _emit_structured_output(
            format_,
            json_data=payload,
            jsonl_records=[{"type": "install-result", **payload}],
        )
    elif mirrored:
        typer.echo(f"Mirrored {mirrored} skill(s) into ~/.grok/skills")
    raise typer.Exit(code=result.returncode)


@plannotator_app.command("install")
def grok_plannotator_install(
    extras: bool = typer.Option(
        True,
        "--extras/--no-extras",
        help="Install optional Plannotator extra skills after the core slash commands",
    ),
    hooks: bool = typer.Option(
        True,
        "--hooks/--no-hooks",
        help="Sync repo-managed Plannotator plan-review hooks to ~/.grok/hooks",
    ),
) -> None:
    """Install Plannotator CLI, skills, and optional Grok hooks."""
    from wagents.platforms.base import SyncContext
    from wagents.platforms.grok import sync_grok_plannotator

    if not shutil.which("npx"):
        typer.echo("Error: npx not found. Install Node.js first.", err=True)
        raise typer.Exit(code=1)

    typer.echo("Installing plannotator CLI...")
    install_result = subprocess.run(
        ["bash", "-c", "curl -fsSL https://plannotator.ai/install.sh | bash -s -- --non-interactive --no-extras"],
        capture_output=False,
    )
    if install_result.returncode != 0:
        raise typer.Exit(code=install_result.returncode)

    typer.echo(f"Running: {shlex.join(PLANNOTATOR_CORE_SYNC_COMMAND)}")
    result = subprocess.run(PLANNOTATOR_CORE_SYNC_COMMAND, capture_output=False)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

    if extras:
        typer.echo(f"Running: {shlex.join(PLANNOTATOR_EXTRAS_SYNC_COMMAND)}")
        result = subprocess.run(PLANNOTATOR_EXTRAS_SYNC_COMMAND, capture_output=False)
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)

    mirrored = mirror_grok_skills_from_claude()
    if mirrored:
        typer.echo(f"Mirrored {mirrored} skill(s) into ~/.grok/skills")

    if hooks:
        ctx = SyncContext(apply=True)
        sync_grok_plannotator(ctx)
        typer.echo(f"Wrote {Path.home() / '.grok' / 'hooks' / 'plannotator.json'}")

    typer.echo("Plannotator install complete. Restart Grok Build before using hooks.")


@plannotator_app.command("sync")
def grok_plannotator_sync() -> None:
    """Sync home-local Plannotator hooks, shim, and repo skill overlays."""
    from wagents.platforms.base import SyncContext
    from wagents.platforms.grok import sync_grok_plannotator

    ctx = SyncContext(apply=True)
    sync_grok_plannotator(ctx)
    typer.echo("Plannotator sync complete. Restart Grok Build before using hooks.")


@grok_app.command("doctor")
def grok_doctor(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
) -> None:
    """Report Grok config paths, env vars, MCP block, and skill roots."""
    from wagents.grok_doctor import collect_grok_doctor_checks, grok_doctor_report

    format_ = _normalize_output_format(format_)

    if format_ in {"json", "jsonl"}:
        report = grok_doctor_report()
        checks = report["checks"]
        _emit_doctor_report(format_, checks)
        if not report["ok"]:
            raise typer.Exit(code=1)
        return

    checks = collect_grok_doctor_checks()
    issues = [check["summary"] for check in checks if check["status"] == "fail"]
    warnings = [check["summary"] for check in checks if check["status"] == "warn"]
    lines: list[str] = ["Grok Build doctor", ""]
    for check in checks:
        lines.append(f"{check['name']}: {check['summary']}")
    if warnings:
        lines.append("")
        lines.append("warnings:")
        lines.extend(f"- {item}" for item in warnings)
    if issues:
        lines.append("")
        lines.append("issues:")
        lines.extend(f"- {item}" for item in issues)

    typer.echo("\n".join(lines))
    if issues:
        raise typer.Exit(code=1)


@app.command()
def update(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Refresh installed skills from their recorded sources via npx skills."""
    import shutil
    import subprocess

    if not shutil.which("npx"):
        typer.echo("Error: npx not found. Install Node.js first.", err=True)
        raise typer.Exit(code=1)

    cmd = ["npx", "-y", "skills", "update"]
    capture = _normalize_output_format(format_) != "text"
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if capture:
        payload: dict[str, object] = {
            "argv": cmd,
            "returncode": result.returncode,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
        }
        _emit_structured_output(
            format_,
            json_data=payload,
            jsonl_records=[{"type": "update-result", **payload}],
        )
    raise typer.Exit(code=result.returncode)


@skills_app.command("index")
def skills_index(
    source: str = typer.Option("all", "--source", help="Skill source: all, repo, codex, global, plugin, ..."),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Index locally available skills without loading full skill bodies."""
    _exit_skill_router(["index", "--source", source, "--format", format_], source=source)


@skills_app.command("search")
def skills_search(
    query: str = typer.Argument(..., help="Search query"),
    source: str = typer.Option("all", "--source", help="Skill source: all, repo, codex, global, plugin, ..."),
    limit: int = typer.Option(5, "--limit", "-n", min=1, help="Maximum results"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Search locally available skills with deterministic lexical ranking."""
    _exit_skill_router(
        ["search", query, "--source", source, "--limit", str(limit), "--format", format_],
        source=source,
    )


@skills_app.command("read")
def skills_read(
    name_or_path: str = typer.Argument(..., help="Skill name, directory path, or SKILL.md path"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Read one skill body by exact name or path."""
    _exit_skill_router(["read", name_or_path, "--format", format_])


@skills_app.command("context")
def skills_context(
    query: str = typer.Argument(..., help="Task or capability query"),
    source: str = typer.Option("all", "--source", help="Skill source: all, repo, codex, global, plugin, ..."),
    limit: int = typer.Option(3, "--limit", "-n", min=1, max=5, help="Maximum skill bodies to include"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Build a compact context packet for the best matching skills."""
    _exit_skill_router(
        ["context", query, "--source", source, "--limit", str(limit), "--format", format_],
        source=source,
    )


@skills_app.command("doctor")
def skills_doctor(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Diagnose skill discovery roots and counts."""
    _exit_skill_router(["doctor", "--format", format_])


@skills_app.command("sync")
def skills_sync(
    agent: Annotated[list[str] | None, typer.Option("-a", "--agent", help="Target agent(s), repeatable")] = None,
    all_agents: bool = typer.Option(False, "--all-agents", help="Target all supported agents"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview or execute additive sync"),
    include_installed: bool = typer.Option(
        False,
        "--include-installed",
        help="Include verified one-off installed external skills outside the curated desired set",
    ),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Additively sync repo and curated external skills across supported harnesses."""
    if not shutil.which("npx"):
        typer.echo("Error: npx not found. Install Node.js first.", err=True)
        raise typer.Exit(code=1)

    target_agents = _select_sync_agents(agent, all_agents)
    typer.echo("Collecting cross-harness skill inventory...", err=True)
    report = _build_sync_report(target_agents, include_installed=include_installed)
    agent_reports = cast("list[dict[str, object]]", report.get("agents") or [])
    _emit_sync_report(report, dry_run=dry_run, format_=format_)
    if dry_run:
        return

    grok_mirror_needed = False
    for payload in agent_reports:
        if payload.get("agent") == "grok" and payload.get("_command_argvs"):
            grok_mirror_needed = True
        for argv in cast("list[list[str]]", payload.get("_command_argvs") or []):
            result = subprocess.run(argv, capture_output=False)
            if result.returncode != 0:
                raise typer.Exit(code=result.returncode)
    if grok_mirror_needed:
        mirrored = mirror_grok_skills_from_claude()
        if mirrored:
            typer.echo(f"Mirrored {mirrored} skill(s) into ~/.grok/skills")


@catalog_app.command("index")
def catalog_index(
    check: bool = typer.Option(False, "--check", help="Exit 1 when committed index drifts from authoring"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Inspect or verify the generated skills catalog index bundle."""
    from wagents.skill_index import CATALOG_INDEX_PATH, catalog_index_stale_reason

    reason = catalog_index_stale_reason()
    if check:
        if reason:
            if format_ == "json" or format_ == "jsonl":
                typer.echo(json.dumps({"ok": False, "error": reason, "path": str(CATALOG_INDEX_PATH)}))
            else:
                typer.echo(reason, err=True)
            raise SystemExit(1)
        if format_ == "json" or format_ == "jsonl":
            typer.echo(json.dumps({"ok": True, "path": str(CATALOG_INDEX_PATH)}))
        else:
            typer.echo(f"{CATALOG_INDEX_PATH.relative_to(ROOT)} is up to date")
        return

    if reason:
        typer.echo(reason)
    else:
        typer.echo(f"{CATALOG_INDEX_PATH.relative_to(ROOT)} is up to date")


@catalog_app.command("audit")
def catalog_audit(
    status: str | None = typer.Option(None, "--status", help="Filter curated external rows by status"),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit 1 when warning or error audit issues are present",
    ),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Report curated external skill evidence gaps without mutating catalog sources."""
    from wagents.catalog_audit import build_catalog_audit, render_catalog_audit_text

    normalized_format = _normalize_output_format(format_)
    report = build_catalog_audit(status=status)
    issue_counts = cast("dict[str, int]", report.get("issue_counts") or {})
    strict_failed = bool(strict and (issue_counts.get("error") or issue_counts.get("warning")))
    payload = {**report, "strict": strict, "strict_failed": strict_failed}
    _emit_structured_output(
        normalized_format,
        text_lines=render_catalog_audit_text(payload, strict=strict),
        json_data=payload,
        jsonl_records=[{"type": "catalog-audit", **payload}],
    )
    if strict_failed:
        raise SystemExit(1)


@catalog_app.command("sync-authoring")
def catalog_sync_authoring(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show target authoring MDX paths without writing files"),
):
    """Sync repo-owned skills/*/SKILL.md into docs/src/authoring/skills/*.mdx (source_kind: custom).

    This populates the authoring SSOT used by docs generate for catalog index + pages.
    External (curated) entries are authored separately (or via migrate script) under same dir.
    """
    from wagents.authoring_sync import sync_custom_authoring_from_skills

    targets = sync_custom_authoring_from_skills(dry_run=dry_run)
    if dry_run:
        typer.echo(f"DRY-RUN: would sync {len(targets)} custom skills to authoring MDX")
        for t in targets[:20]:
            typer.echo(f"  {t}")
        if len(targets) > 20:
            typer.echo(f"  ... and {len(targets) - 20} more")
    else:
        typer.echo(f"Synced {len(targets)} custom authoring MDX entries")
        typer.echo("Next: uv run wagents docs generate --no-installed to refresh pages + indexes.")


def _emit_openspec_command_result(result, format_: str, *, success_message: str) -> None:
    """Emit an OpenSpec subprocess result and preserve its exit status."""
    try:
        parsed_stdout = result.json_stdout()
    except json.JSONDecodeError:
        parsed_stdout = None

    parsed_failure_count = 0
    if isinstance(parsed_stdout, dict):
        summary = parsed_stdout.get("summary")
        if isinstance(summary, dict):
            totals = summary.get("totals")
            if isinstance(totals, dict):
                failed = totals.get("failed")
                if isinstance(failed, int):
                    parsed_failure_count = failed
        items = parsed_stdout.get("items")
        if isinstance(items, list):
            parsed_failure_count = max(
                parsed_failure_count,
                sum(1 for item in items if isinstance(item, dict) and item.get("valid") is False),
            )
    exit_code = result.returncode or (1 if parsed_failure_count else 0)

    payload: dict[str, object] = {
        "argv": result.argv,
        "returncode": exit_code,
        "subprocessReturncode": result.returncode,
        "parsedFailureCount": parsed_failure_count,
        "stdout": parsed_stdout if parsed_stdout is not None else result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
    text_lines = [success_message, f"command: {shlex.join(result.argv)}", f"exit: {exit_code}"]
    if exit_code != result.returncode:
        text_lines.append(f"subprocess exit: {result.returncode}")
    if result.stdout.strip():
        text_lines.extend(["stdout:", result.stdout.strip()])
    if result.stderr.strip():
        text_lines.extend(["stderr:", result.stderr.strip()])
    _emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data=payload,
        jsonl_records=[{"type": "openspec-result", **payload}],
    )
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


def _emit_openspec_dry_run(argv: list[str], format_: str) -> None:
    """Print an OpenSpec command without executing it."""
    command = shlex.join(argv)
    _emit_structured_output(
        format_,
        text_lines=[command],
        json_data={"argv": argv, "command": command},
        jsonl_records=[{"type": "openspec-command", "argv": argv, "command": command}],
    )


@openspec_app.command("doctor")
def openspec_doctor(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
    check_cli: bool = typer.Option(False, "--check-cli", help="Run `openspec --version` through npx"),
    validate: bool = typer.Option(False, "--validate", help="Run `openspec validate --all --json`"),
    package: str = typer.Option(OPENSPEC_PACKAGE, "--package", help="OpenSpec npm package spec"),
):
    """Diagnose OpenSpec tooling, project state, and downstream tool mapping."""
    report = build_doctor_report(root=ROOT, package=package, check_cli=check_cli, validate=validate)
    node = cast("dict[str, object]", report["node"])
    npx = cast("dict[str, object]", report["npx"])
    project = cast("dict[str, object]", report["project"])
    text_lines = [
        f"OpenSpec package: {report['package']}",
        f"Node: {node.get('version') or 'missing'} supported={node.get('supported')}",
        f"npx: {npx.get('version') or 'missing'}",
        f"config: {project['configExists']} {project['config']}",
        f"specs: {project['specsExists']}",
        f"changes: {project['changesExists']}",
        f"schemas: {project['schemasExists']}",
        "tool mapping:",
    ]
    text_lines.extend(f"  {agent} -> {tool}" for agent, tool in sorted(OPENSPEC_TOOL_BY_AGENT.items()))
    generated = cast("list[str]", report.get("generatedArtifacts") or [])
    if generated:
        text_lines.append("generated artifacts present:")
        text_lines.extend(f"  {path}" for path in generated)
    checks = cast("list[dict[str, object]]", report.get("checks") or [])
    for check in checks:
        text_lines.append(f"check {check.get('name')}: exit={check.get('returncode')}")
    _emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data=report,
        jsonl_records=[{"type": "openspec-doctor", **report}],
    )


@openspec_app.command("init")
def openspec_init(
    path: Annotated[Path | None, typer.Option("--path", help="Target directory, defaults to repo root")] = None,
    agent: Annotated[list[str] | None, typer.Option("-a", "--agent", help="Repo agent ID to configure")] = None,
    tool: Annotated[list[str] | None, typer.Option("--tool", help="Raw OpenSpec tool ID to configure")] = None,
    all_tools: bool = typer.Option(False, "--all-tools", help="Pass `--tools all` to OpenSpec"),
    profile: str = typer.Option("core", "--profile", help="OpenSpec profile: core or custom"),
    force: bool = typer.Option(False, "--force", help="Pass `--force` to OpenSpec"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Print or execute the command"),
    package: str = typer.Option(OPENSPEC_PACKAGE, "--package", help="OpenSpec npm package spec"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Initialize OpenSpec and selected downstream AI tool artifacts."""
    args = ["init"]
    if path is not None:
        args.append(str(path))
    if all_tools:
        tools_arg = "all"
    else:
        default_agents = tuple(OPENSPEC_TOOL_BY_AGENT) if agent is None and tool is None else agent
        try:
            selected = select_openspec_tools(agents=default_agents, tools=tool)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        tools_arg = ",".join(selected) if selected else "none"
    args.extend(["--tools", tools_arg, "--profile", profile])
    if force:
        args.append("--force")
    argv = build_openspec_argv(args, package=package)
    if dry_run:
        _emit_openspec_dry_run(argv, format_)
        return
    result = run_openspec(args, cwd=ROOT, package=package, capture=False)
    raise typer.Exit(code=result.returncode)


@openspec_app.command("update")
def openspec_update(
    path: Annotated[Path | None, typer.Option("--path", help="Target directory, defaults to repo root")] = None,
    force: bool = typer.Option(False, "--force", help="Pass `--force` to OpenSpec"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Print or execute the command"),
    package: str = typer.Option(OPENSPEC_PACKAGE, "--package", help="OpenSpec npm package spec"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Refresh generated OpenSpec AI tool artifacts after CLI/profile changes."""
    args = ["update"]
    if path is not None:
        args.append(str(path))
    if force:
        args.append("--force")
    argv = build_openspec_argv(args, package=package)
    if dry_run:
        _emit_openspec_dry_run(argv, format_)
        return
    result = run_openspec(args, cwd=ROOT, package=package, capture=False)
    raise typer.Exit(code=result.returncode)


@openspec_app.command("validate")
def openspec_validate(
    strict: bool = typer.Option(True, "--strict/--no-strict", help="Run strict OpenSpec validation"),
    concurrency: int | None = typer.Option(None, "--concurrency", min=1, help="Validation concurrency"),
    package: str = typer.Option(OPENSPEC_PACKAGE, "--package", help="OpenSpec npm package spec"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Validate all OpenSpec changes and specs with JSON output."""
    args = ["validate", "--all", "--json"]
    if strict:
        args.append("--strict")
    if concurrency is not None:
        args.extend(["--concurrency", str(concurrency)])
    result = run_openspec(args, cwd=ROOT, package=package)
    _emit_openspec_command_result(result, format_, success_message="OpenSpec validation")


@openspec_app.command("status")
def openspec_status(
    change: str = typer.Option(..., "--change", help="OpenSpec change name"),
    schema: str | None = typer.Option(None, "--schema", help="Schema override"),
    package: str = typer.Option(OPENSPEC_PACKAGE, "--package", help="OpenSpec npm package spec"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Return JSON artifact status for one OpenSpec change."""
    args = ["status", "--change", change, "--json"]
    if schema:
        args.extend(["--schema", schema])
    result = run_openspec(args, cwd=ROOT, package=package)
    _emit_openspec_command_result(result, format_, success_message=f"OpenSpec status for {change}")


@openspec_app.command("instructions")
def openspec_instructions(
    artifact: str = typer.Argument("apply", help="Artifact ID, or `apply` for implementation instructions"),
    change: str = typer.Option(..., "--change", help="OpenSpec change name"),
    schema: str | None = typer.Option(None, "--schema", help="Schema override"),
    package: str = typer.Option(OPENSPEC_PACKAGE, "--package", help="OpenSpec npm package spec"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Return JSON OpenSpec instructions for an artifact or apply step."""
    args = ["instructions", artifact, "--change", change, "--json"]
    if schema:
        args.extend(["--schema", schema])
    result = run_openspec(args, cwd=ROOT, package=package)
    _emit_openspec_command_result(result, format_, success_message=f"OpenSpec instructions for {artifact}")


@openspec_app.command("schemas")
def openspec_schemas(
    package: str = typer.Option(OPENSPEC_PACKAGE, "--package", help="OpenSpec npm package spec"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """List OpenSpec schemas in JSON-compatible form."""
    result = run_openspec(["schemas", "--json"], cwd=ROOT, package=package)
    _emit_openspec_command_result(result, format_, success_message="OpenSpec schemas")


@openspec_app.command("archive")
def openspec_archive(
    change: str = typer.Argument(..., help="OpenSpec change name to archive"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip OpenSpec confirmation prompts"),
    skip_specs: bool = typer.Option(False, "--skip-specs", help="Skip spec update operations"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Run OpenSpec validation before archive"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Print or execute the command"),
    package: str = typer.Option(OPENSPEC_PACKAGE, "--package", help="OpenSpec npm package spec"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Archive a completed OpenSpec change after validation."""
    args = ["archive", change]
    if yes:
        args.append("--yes")
    if skip_specs:
        args.append("--skip-specs")
    if not validate:
        args.append("--no-validate")
    argv = build_openspec_argv(args, package=package)
    if dry_run:
        _emit_openspec_dry_run(argv, format_)
        return
    result = run_openspec(args, cwd=ROOT, package=package, capture=False)
    raise typer.Exit(code=result.returncode)


def _format_opencode_session_report(report: dict[str, Any]) -> list[str]:
    """Render a compact OpenCode session diagnosis."""
    summary = cast("dict[str, Any]", report.get("summary") or {})
    lines = [
        f"db: {report.get('db_path')}",
        f"logs: {report.get('log_dir')}",
        f"server_error events: {summary.get('event_count', 0)}",
    ]
    request_ids = cast("list[str]", summary.get("request_ids") or [])
    if request_ids:
        lines.append("request IDs:")
        lines.extend(f"  {request_id}" for request_id in request_ids)
    sessions = cast("dict[str, int]", summary.get("sessions") or {})
    if sessions:
        lines.append("sessions:")
        lines.extend(f"  {session_id}: {count} event(s)" for session_id, count in sorted(sessions.items()))
    if summary.get("first_timestamp") or summary.get("last_timestamp"):
        lines.append(f"window: {summary.get('first_timestamp')} .. {summary.get('last_timestamp')}")

    session_reports = cast("dict[str, dict[str, Any]]", report.get("sessions") or {})
    for session_id, session_report in sorted(session_reports.items()):
        lines.append(f"session {session_id}:")
        if not session_report.get("exists"):
            lines.append("  not found in opencode.db")
            continue
        session = cast("dict[str, Any]", session_report.get("session") or {})
        lines.append(f"  title: {session.get('title')}")
        lines.append(f"  directory: {session.get('directory')}")
        lines.append(f"  archived: {session.get('time_archived')}")
        lines.append(f"  assistant messages: {session_report.get('assistant_message_count')}")
        lines.append(f"  incomplete assistant messages: {session_report.get('incomplete_assistant_message_count')}")
        lines.append(f"  encrypted reasoning parts: {session_report.get('encrypted_reasoning_part_count')}")
        lines.append(f"  error parts: {session_report.get('error_part_count')}")

    quarantine = cast("dict[str, Any]", report.get("quarantine") or {})
    if quarantine.get("requested"):
        mode = "applied" if quarantine.get("applied") else "dry-run"
        lines.append(f"quarantine: {mode}")
        archived_sessions = cast("list[str]", quarantine.get("archived_sessions") or [])
        if archived_sessions:
            lines.extend(f"  archive session: {session_id}" for session_id in archived_sessions)
        if quarantine.get("backup_path"):
            lines.append(f"  backup: {quarantine.get('backup_path')}")
    return lines


@opencode_app.command("diagnose-session")
def opencode_diagnose_session(
    request_id: Annotated[str | None, typer.Option("--request-id", help="OpenAI request ID from a retry error")] = None,
    session_id: Annotated[
        list[str] | None,
        typer.Option("--session-id", help="OpenCode session ID to inspect; may be repeated"),
    ] = None,
    db_path: Annotated[Path, typer.Option("--db-path", help="Path to opencode.db")] = DEFAULT_OPENCODE_DB_PATH,
    log_dir: Annotated[
        Path,
        typer.Option("--log-dir", help="Path to OpenCode log directory"),
    ] = DEFAULT_OPENCODE_LOG_DIR,
    quarantine: bool = typer.Option(False, "--quarantine", help="Plan or apply archive quarantine for target sessions"),
    apply: bool = typer.Option(False, "--apply", help="Apply quarantine after backing up opencode.db"),
    backup_dir: Annotated[Path | None, typer.Option("--backup-dir", help="Directory for DB backups")] = None,
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Diagnose OpenCode session-local server_error loops without mutating by default."""
    normalized_format = _normalize_output_format(format_)
    try:
        report = diagnose_session(
            request_id=request_id,
            session_ids=session_id,
            db_path=db_path,
            log_dir=log_dir,
            quarantine=quarantine,
            apply=apply,
            backup_dir=backup_dir,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    text_report = redact_report_for_text(report)
    _emit_structured_output(
        normalized_format,
        text_lines=_format_opencode_session_report(text_report),
        json_data=report,
        jsonl_records=[{"type": "opencode-session-diagnosis", **report}],
    )


@app.command()
def package(
    name: str = typer.Argument("", help="Skill name (omit for --all)"),
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output directory")] = None,
    dry_run: bool = typer.Option(False, "--dry-run", help="Check portability without creating ZIPs"),
    all_skills: bool = typer.Option(False, "--all", help="Package all skills"),
    format_: str = typer.Option("table", "--format", help="Output format: json or table"),
):
    """Package skills into portable ZIP files."""
    import subprocess

    repo_root = get_repo_root()
    script = repo_root / "skills" / "skill-creator" / "scripts" / "package.py"
    cmd = [sys.executable, str(script)]

    if all_skills:
        cmd.append("--all")
    elif name:
        skill_dir = repo_root / "skills" / name
        cmd.append(str(skill_dir))
    else:
        typer.echo("Error: provide a skill name or use --all", err=True)
        raise typer.Exit(code=1)

    if output:
        cmd.extend(["--output", str(output)])
    if dry_run:
        cmd.append("--dry-run")
    cmd.extend(["--format", format_])

    result = subprocess.run(cmd, cwd=repo_root, capture_output=False)
    raise typer.Exit(code=result.returncode)


@app.command()
def readme(
    check: bool = typer.Option(False, "--check", help="Check if README is up to date"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Generate or check README.md."""
    skills = []
    skills_dir = ROOT / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                try:
                    fm, _ = parse_frontmatter(skill_file.read_text())
                    name = fm.get("name", skill_dir.name)
                    skills.append((name, fm.get("description", "")))
                except Exception as e:
                    typer.echo(f"Warning: skipping {skill_file}: {e}", err=True)

    agents = []
    agents_dir = ROOT / "agents"
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob("*.md")):
            if agent_file.name == "README.md":
                continue
            try:
                fm, _ = parse_frontmatter(agent_file.read_text())
                agents.append((fm.get("name", agent_file.stem), fm.get("description", "")))
            except Exception as e:
                typer.echo(f"Warning: skipping {agent_file}: {e}", err=True)

    mcps = []
    mcp_dir = ROOT / "mcp"
    if mcp_dir.exists():
        for mcp_subdir in sorted(mcp_dir.iterdir()):
            if not mcp_subdir.is_dir():
                continue
            if _is_local_mcp_dir(mcp_subdir):
                continue
            pyproject = mcp_subdir / "pyproject.toml"
            if pyproject.exists():
                try:
                    data = tomllib.loads(pyproject.read_text())
                    name = data.get("project", {}).get("name", mcp_subdir.name)
                    desc = data.get("project", {}).get("description", "")
                    mcps.append((name, desc))
                except Exception:
                    mcps.append((mcp_subdir.name, ""))

    logo_repo_path = docs_asset_repo_path(VISUAL_ASSET_BY_ID["logo"].src)
    social_card_repo_path = docs_asset_repo_path(VISUAL_ASSET_BY_ID["social-card"].src)

    content_parts = [
        '<div align="center">',
        (
            '  <img src="https://raw.githubusercontent.com/wyattowalsh/agents/main/'
            f'{logo_repo_path}" alt="Agents Logo" width="100" height="100">'
        ),
        "  <h1>agents</h1>",
        "  <p><b>Portable AI agent skills, MCP config, and shared instructions</b></p>",
        "  <p>",
        (
            '    <a href="https://github.com/wyattowalsh/agents/actions/workflows/CI">'
            '<img src="https://github.com/wyattowalsh/agents/actions/workflows/CI/'
            'badge.svg" alt="CI"></a>'
        ),
        (
            '    <a href="https://github.com/wyattowalsh/agents/blob/main/LICENSE">'
            '<img src="https://img.shields.io/github/license/wyattowalsh/agents?'
            'style=flat-square&color=5D6D7E" alt="License"></a>'
        ),
        (
            '    <a href="https://github.com/wyattowalsh/agents/releases"><img '
            'src="https://img.shields.io/github/v/release/wyattowalsh/agents?'
            'style=flat-square&color=2E86C1" alt="Release"></a>'
        ),
        (
            f'    <a href="https://agents.w4w.dev/skills/catalog/"><img '
            f'src="https://img.shields.io/badge/skills-{len(skills)}-0f766e?'
            'style=flat-square" alt="Skills"></a>'
        ),
        (
            '    <a href="https://agents.w4w.dev"><img src="https://img.shields.io/'
            "badge/docs-agents.w4w.dev-00b4d8?style=flat-square&logo=read-the-docs"
            '&logoColor=white" alt="Docs"></a>'
        ),
        "  </p>",
        (
            '  <img src="https://raw.githubusercontent.com/wyattowalsh/agents/main/'
            f'{social_card_repo_path}" alt="Agents social preview" width="640">'
        ),
        "</div>",
        "",
        "---",
        "",
        "## 🚀 Quick Start",
        "",
        "New here? Start with [START-HERE.md](START-HERE.md) for a 30-minute onboarding path.",
        "",
        "Install all skills globally into your favorite agents:",
        "",
        "```bash",
        build_install_command(all_skills=True),
        "```",
        "",
        "For non-trivial repository changes, check the OpenSpec workflow state:",
        "",
        "```bash",
        "uv run wagents openspec doctor",
        "```",
        "",
        "## 📦 Distribution",
        "",
        (
            "This repo is packaged as one cross-agent bundle with native plugin adapters and a skills CLI "
            "fallback. Today it primarily ships skills, MCP configuration, and shared instructions; "
            "the repo-level `agents/` directory is reserved for future bundled agent definitions."
            if not agents
            else (
                "This repo is packaged as one cross-agent bundle with native plugin adapters and a skills CLI fallback:"
            )
        ),
        "",
        "| Target | Path | Update behavior |",
        "| ------ | ---- | --------------- |",
        (
            "| Claude Code | `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` | "
            "Git-hosted plugin updates resolve from the latest commit because "
            "the plugin version is intentionally unpinned |"
        ),
        (
            "| Codex | `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json` | "
            "Codex can load the Git-backed plugin bundle and bundled skills from the repository root |"
        ),
        (
            "| OpenCode | `opencode.json` + `.opencode/` | Repo-managed npm runtime plugin specs use "
            "`@latest`; OCX-managed components stay copied under `.opencode/` with `.ocx/` receipts; "
            "restart OpenCode or refresh `~/.cache/opencode/packages/` when Bun's plugin cache is stale |"
        ),
        (
            "| Other agents | `npx skills add github:wyattowalsh/agents ...` | "
            "`wagents update` refreshes recorded sources, and `wagents skills sync` "
            "additively reconciles repo + curated external skills across harnesses |"
        ),
        (
            "| OpenSpec | `openspec/` + `uv run wagents openspec ...` | "
            "Spec/change workflow with JSON wrappers and local downstream AI tool artifact generation |"
        ),
        "",
        "## 🤝 Contributing",
        "",
        (
            "Start with [CONTRIBUTING.md](CONTRIBUTING.md) before changing skills, agents, MCP config, "
            "docs generators, external skill metadata, distribution files, or validation behavior."
        ),
        "",
        (
            "Use source-of-truth files first, regenerate derived docs and indexes with `wagents`, "
            "and run `uv run wagents openspec validate` for non-trivial public formats, downstream tooling, "
            "docs generation, validation behavior, sync behavior, or multi-surface distribution work."
        ),
        "",
        ("Security-sensitive reports and secret-handling rules are documented in [SECURITY.md](SECURITY.md)."),
        "",
        "## ✨ Why use this repository?",
        "",
        "| 📦 **Portable** | 🧩 **Composable** | 🌐 **Open Source** |",
        "| :--- | :--- | :--- |",
        (
            "| Use skills across Claude Code, Cursor, Copilot, and more. | Combine "
            "simple skills into complex, multi-agent workflows. | Extensible, "
            "readable, and community-driven. |"
        ),
        "",
    ]

    if skills:
        content_parts.extend([
            "## 🧰 Skills",
            "",
            "Reusable actions and knowledge bases for AI agents.",
            "",
            "| Name | Description |",
            "| ---- | ----------- |",
        ])
        for name, desc in skills:
            content_parts.append(f"| {name} | {desc} |")
        content_parts.append("")

    if agents:
        content_parts.extend([
            "## 🤖 Agents",
            "",
            "System prompts and context definitions for AI agents.",
            "",
            "| Name | Description |",
            "| ---- | ----------- |",
        ])
        for name, desc in agents:
            content_parts.append(f"| {name} | {desc} |")
        content_parts.append("")

    if mcps:
        content_parts.extend([
            "## 🔌 MCP Servers",
            "",
            (
                "First-party MCP servers authored in this repository (see `AGENTS.md` §2). "
                "Curated external servers are configured in `config/mcp-registry.json` "
                "and exposed via MCPHub."
            ),
            "",
            "| Name | Description |",
            "| ---- | ----------- |",
        ])
        for name, desc in mcps:
            content_parts.append(f"| {name} | {desc} |")
        content_parts.append("")

    # Dev commands
    content_parts.extend([
        "## 🛠️ Development",
        "",
        "| Command | Description |",
        "| ------- | ----------- |",
        "| `wagents new skill <name>` | Create a new skill |",
        "| `wagents new agent <name>` | Create a new agent |",
        "| `wagents new mcp <name>` | Create a new MCP server |",
        "| `wagents doctor` | Check local environment and toolchain health |",
        "| `wagents validate` | Validate all skills and agents |",
        "| `wagents openspec doctor` | Diagnose OpenSpec tooling, project state, and downstream tool mapping |",
        "| `wagents openspec validate` | Validate OpenSpec specs and changes with JSON-backed output |",
        (
            "| `wagents skills sync --dry-run` | Preview additive cross-harness "
            "skill sync from the normalized inventory |"
        ),
        "| `wagents skills search <query>` | Search local repo, installed, and plugin skills on demand |",
        "| `wagents skills context <query>` | Build a compact context packet for matching skills |",
        "| `make typecheck` | Run ty across `wagents/` and `scripts/` |",
        "| `wagents readme` | Regenerate this README |",
        "| `wagents package <name>` | Package a skill into portable ZIP |",
        "| `wagents package --all` | Package all skills |",
        "| `wagents install` | Install all skills to all agents |",
        "| `wagents install -a <agent>` | Install all skills to specific agent |",
        "| `wagents install <name>` | Install specific skill to all agents |",
        "| `wagents install <name> -a <agent>` | Install specific skill to specific agents |",
        "| `wagents update` | Refresh installed skills from their recorded sources |",
        "| `wagents docs init` | One-time setup: install docs dependencies |",
        "| `wagents docs generate` | Generate MDX content pages from assets |",
        (
            "| `wagents docs generate --include-installed` | Include installed "
            "skills discovered from the normalized harness inventory in generated docs |"
        ),
        "| `wagents docs dev` | Generate + launch dev server |",
        "| `wagents docs build` | Generate + production build |",
        "| `wagents docs preview` | Generate + build + preview server |",
        "| `wagents docs clean` | Remove generated content pages |",
        "",
        "Third-party skill collections can be installed directly with "
        "`npx skills add <source> --skill <name> -y -g --agent <agent>`. "
        "Repeat `--skill` and `--agent` to target a curated subset.",
        "",
    ])

    # Supported agents
    content_parts.extend([
        "## 🤝 Supported Agents",
        "",
        "- [Antigravity](https://antigravity.google/)",
        "- [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)",
        "- [Codex](https://github.com/openai/codex)",
        "- [Crush](https://github.com/crush-ai/crush)",
        "- [Cursor](https://cursor.sh/)",
        "- [Gemini CLI](https://github.com/google/gemini-cli)",
        "- [GitHub Copilot](https://github.com/features/copilot)",
        "- [Grok Build](https://x.ai/)",
        "- [OpenCode](https://github.com/anomalyco/opencode) — native AGENTS.md support with repo-level config",
        "- [Cherry Studio](https://www.cherry-ai.com/) — MCP-only via MCPHub registry",
        "And other [agentskills.io](https://agentskills.io)-compatible agents.",
        "",
    ])

    content_parts.extend([
        "## 📚 Documentation",
        "",
        (
            "Explore the full catalog, installation guides, and generated reference pages "
            "at [agents.w4w.dev](https://agents.w4w.dev)."
        ),
        "",
    ])

    # License
    content_parts.extend(["## 📜 License", "", "[MIT](LICENSE)", ""])

    generated_content = "\n".join(content_parts)

    readme_file = ROOT / "README.md"

    up_to_date = readme_file.exists() and readme_file.read_text() == generated_content
    payload: dict[str, object] = {
        "check": check,
        "path": str(readme_file),
        "up_to_date": up_to_date,
        "skills_count": len(skills),
        "agents_count": len(agents),
        "mcps_count": len(mcps),
        "written": False,
    }
    if check:
        if not readme_file.exists():
            if _normalize_output_format(format_) == "text":
                typer.echo("README.md is missing. Run `wagents readme` to create it.")
            else:
                payload["error"] = "README.md is missing"
                _emit_structured_output(format_, json_data=payload, jsonl_records=[{"type": "readme", **payload}])
            raise typer.Exit(code=1)
        if not up_to_date:
            if _normalize_output_format(format_) == "text":
                typer.echo("README.md is stale. Run `wagents readme` to update.")
            else:
                payload["error"] = "README.md is stale"
                _emit_structured_output(format_, json_data=payload, jsonl_records=[{"type": "readme", **payload}])
            raise typer.Exit(code=1)
        if _normalize_output_format(format_) == "text":
            typer.echo("README.md is up to date")
        else:
            _emit_structured_output(format_, json_data=payload, jsonl_records=[{"type": "readme", **payload}])
    else:
        readme_file.write_text(generated_content)
        payload["written"] = True
        if _normalize_output_format(format_) == "text":
            typer.echo("Updated README.md")
        else:
            _emit_structured_output(format_, json_data=payload, jsonl_records=[{"type": "readme", **payload}])


# ---------------------------------------------------------------------------
# wagents hooks list / validate
# ---------------------------------------------------------------------------


@hooks_app.command("list")
def hooks_list(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """List all hooks across skills, agents, and settings."""
    all_hooks = _collect_hooks()

    if not all_hooks:
        _emit_structured_output(
            format_,
            text_lines=["No hooks found."],
            json_data={"count": 0, "hooks": []},
            jsonl_records=[{"type": "summary", "count": 0}],
        )
        return

    rows: list[dict[str, Any]] = []
    for hook in all_hooks:
        rows.append({
            "source": hook.source,
            "event": hook.event,
            "matcher": hook.matcher,
            "handler_type": hook.handler_type,
            "command": hook.command,
            "prompt": hook.prompt,
            "harness_support": hook.harness_support or [],
            "rendered_event": hook.rendered_event,
            "blocking_mode": hook.blocking_mode,
        })

    text_lines = [
        f"{'Source':<35} {'Event':<20} {'Matcher':<15} {'Harnesses':<28} {'Type':<10} {'Command/Prompt'}",
        "-" * 130,
    ]
    for row in rows:
        value = row["command"] if row["handler_type"] == "command" else row["prompt"]
        if len(value) > 50:
            value = value[:47] + "..."
        matcher = row["matcher"] or "(all)"
        harnesses = ",".join(row.get("harness_support") or []) or "(native)"
        text_lines.append(
            f"{row['source']:<35} {row['event']:<20} {matcher:<15} {harnesses:<28} {row['handler_type']:<10} {value}"
        )

    _emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data={"count": len(rows), "hooks": rows},
        jsonl_records=[{"type": "hook", **row} for row in rows] + [{"type": "summary", "count": len(rows)}],
    )


@hooks_app.command("validate")
def hooks_validate(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Validate all hooks across skills, agents, and settings."""
    script = _skill_creator_scripts() / "asset_toolkit" / "validate_hooks.py"
    raise typer.Exit(code=_run_python_script(script, ["--format", format_, "--repo-root", str(ROOT)]))


# ---------------------------------------------------------------------------
# wagents eval list / validate / coverage
# ---------------------------------------------------------------------------


def _collect_evals() -> list[tuple[Path, dict]]:
    """Scan skills/*/evals/*.json and return (path, parsed_data) pairs."""
    results: list[tuple[Path, dict]] = []
    evals_root = ROOT / "skills"
    if not evals_root.exists():
        return results
    for skill_dir in sorted(evals_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        evals_dir = skill_dir / "evals"
        if not evals_dir.is_dir():
            continue
        for eval_file in sorted(evals_dir.glob("*.json")):
            try:
                data = json.loads(eval_file.read_text())
                results.append((eval_file, data))
            except json.JSONDecodeError:
                results.append((eval_file, {}))
    return results


def _is_eval_manifest(data: dict) -> bool:
    """Return True when an eval JSON file uses the canonical manifest shape."""
    return "evals" in data


def _expand_eval_cases(path: Path, data: dict) -> list[dict[str, object]]:
    """Expand an eval file into normalized per-case records."""
    skill_name = path.parent.parent.name
    if _is_eval_manifest(data):
        records: list[dict[str, object]] = []
        manifest_skill = data.get("skill_name", skill_name)
        for index, item in enumerate(data.get("evals", []), start=1):
            if not isinstance(item, dict):
                records.append({"skill": manifest_skill, "query": "", "source": path.name, "case_id": index})
                continue
            records.append({
                "skill": manifest_skill,
                "query": item.get("prompt", ""),
                "source": path.name,
                "case_id": item.get("id", index),
            })
        return records
    return [{"skill": skill_name, "query": data.get("query", ""), "source": path.name, "case_id": path.stem}]


@eval_app.command("list")
def eval_list(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """List all eval files grouped by skill."""
    evals = _collect_evals()
    if not evals:
        _emit_structured_output(
            format_,
            text_lines=["No evals found."],
            json_data={"count": 0, "eval_count": 0, "skills": []},
            jsonl_records=[{"type": "summary", "count": 0, "eval_count": 0}],
        )
        return

    # Group by skill directory name.
    by_skill: dict[str, list[dict[str, object]]] = {}
    for path, data in evals:
        for record in _expand_eval_cases(path, data):
            skill_name = str(record["skill"])
            by_skill.setdefault(skill_name, []).append(record)

    rows: list[dict[str, str | int]] = []
    for skill_name in sorted(by_skill):
        items = by_skill[skill_name]
        count = len(items)
        sample = next((str(item.get("query", "")) for item in items if item.get("query", "")), "")
        rows.append({"skill": skill_name, "eval_count": count, "sample_query": sample})

    total_cases = sum(len(items) for items in by_skill.values())

    text_lines = [f"{'Skill':<25} {'Evals':>5}  Sample Query", "-" * 70]
    text_lines.extend([f"{row['skill']:<25} {row['eval_count']:>5}  {row['sample_query']}" for row in rows])
    _emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data={"count": len(rows), "eval_count": total_cases, "skills": rows},
        jsonl_records=[{"type": "skill", **row} for row in rows],
    )


@eval_app.command("validate")
def eval_validate(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Validate all eval JSON files."""
    script = _skill_creator_scripts() / "asset_toolkit" / "validate_evals.py"
    raise typer.Exit(code=_run_python_script(script, ["--format", format_, "--repo-root", str(ROOT)]))


@eval_app.command("coverage")
def eval_coverage(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Show eval coverage for all skills."""
    skills_dir = ROOT / "skills"
    if not skills_dir.exists():
        _emit_structured_output(
            format_,
            text_lines=["No skills directory found."],
            json_data={"count": 0, "skills": []},
            jsonl_records=[{"type": "summary", "count": 0}],
        )
        return

    # Collect all skills
    skill_names: list[str] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            skill_names.append(skill_dir.name)

    if not skill_names:
        _emit_structured_output(
            format_,
            text_lines=["No skills found."],
            json_data={"count": 0, "skills": []},
            jsonl_records=[{"type": "summary", "count": 0}],
        )
        return

    # Count evals per skill
    evals = _collect_evals()
    counts: dict[str, int] = {}
    for path, data in evals:
        for record in _expand_eval_cases(path, data):
            skill_name = str(record["skill"])
            counts[skill_name] = counts.get(skill_name, 0) + 1

    rows: list[dict[str, str | int | bool]] = []
    for name in skill_names:
        count = counts.get(name, 0)
        rows.append({"skill": name, "has_evals": count > 0, "eval_count": count})

    text_lines = [f"{'Skill':<25} {'Has Evals':<12} {'Count':>5}", "-" * 45]
    text_lines.extend([
        f"{row['skill']:<25} {('Yes' if row['has_evals'] else 'No'):<12} {row['eval_count']:>5}" for row in rows
    ])
    _emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data={"count": len(rows), "skills": rows},
        jsonl_records=[{"type": "skill", **row} for row in rows],
    )


@eval_app.command("adequacy")
def eval_adequacy(
    skill: str | None = typer.Option(None, "--skill", help="Limit to a single skill name"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
    strict: bool = typer.Option(False, "--strict", help="Exit 1 if any R3/R4 skill lacks E4 signals"),
) -> None:
    """Report structural E3/E4 adequacy of skill evals (risk-adjusted)."""
    if skill:
        # Single skill
        target = get_repo_root() / "skills" / skill
        if not (target / "SKILL.md").is_file():
            _emit_structured_output(
                format_,
                text_lines=[f"Skill not found: {skill}"],
                json_data={"error": "skill_not_found", "skill": skill},
                jsonl_records=[{"type": "error", "skill": skill}],
            )
            raise typer.Exit(code=1)
        rep = assess_eval_adequacy(target)
        if format_ in ("text",):
            tier = rep["risk_tier"]
            adeq = rep["adequacy"]
            e4s = ",".join(rep["e4_signals"]) or "-"
            lines = [
                f"Skill: {rep['skill']}",
                f"Risk: {tier}",
                f"Adequacy: {adeq} (E3={rep['has_e3']} E4={rep['has_e4']})",
                f"E4 signals: {e4s}",
                f"Eval count: {rep['eval_count']}",
            ]
            if rep["needs_e4"]:
                lines.append("WARNING: R3/R4 skill lacks E4 signals")
            _emit_structured_output(
                format_,
                text_lines=lines,
                json_data=rep,
                jsonl_records=[{"type": "adequacy", **rep}],
            )
        else:
            _emit_structured_output(
                format_,
                text_lines=[],
                json_data=rep,
                jsonl_records=[{"type": "adequacy", **rep}],
            )
        if strict and rep["needs_e4"]:
            raise typer.Exit(code=1)
        return

    # Full report
    report = build_adequacy_report()
    high = filter_high_risk(report)
    failing = [s for s in high if s["needs_e4"]]

    if format_ == "json" or format_ == "jsonl":
        payload = {
            "count": report["count"],
            "high_risk": high,
            "failing_strict": [s["skill"] for s in failing],
            "summary": report["summary"],
        }
        if format_ == "json":
            _emit_structured_output(format_, text_lines=[], json_data=payload, jsonl_records=[])
        else:
            for rec in high:
                _emit_structured_output("jsonl", text_lines=[], json_data=None, jsonl_records=[{"type": "skill", **rec}])
            _emit_structured_output(
                "jsonl",
                text_lines=[],
                json_data=None,
                jsonl_records=[{"type": "summary", "failing": [s["skill"] for s in failing], **report["summary"]}],
            )
    else:
        # text
        lines: list[str] = ["Skill Adequacy Report (E3/E4 structural)", "-" * 60]
        lines.append(f"{'Skill':<30} {'Risk':<5} {'Adeq':<5} {'E3':<5} {'E4':<5}  E4 signals")
        lines.append("-" * 80)
        for s in sorted(high, key=lambda x: (x["risk_tier"], x["skill"])):
            sig = ",".join(s["e4_signals"][:3]) or "-"
            lines.append(
                f"{s['skill']:<30} {s['risk_tier']:<5} {s['adequacy']:<5} {'Y' if s['has_e3'] else 'N':<5} {'Y' if s['has_e4'] else 'N':<5}  {sig}"
            )
        if failing:
            lines.append("")
            lines.append("STRICT FAIL: R3/R4 skills missing E4:")
            for f in failing:
                lines.append(f"  - {f['skill']}")
        _emit_structured_output(
            format_,
            text_lines=lines,
            json_data={"count": len(high), "high_risk": high, "failing": [f["skill"] for f in failing]},
            jsonl_records=[{"type": "skill", **s} for s in high],
        )

    if strict and failing:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# apm (materialize + doctor)
# ---------------------------------------------------------------------------


@apm_app.command("materialize")
def apm_materialize(
    check: bool = typer.Option(False, "--check", help="Dry-run: compute changes without writing"),
) -> None:
    """Materialize agents/, instructions/, hooks into .apm/ and keep apm.yml mcp: [] (MCPHub-owned)."""
    from wagents.apm import materialize as _materialize
    from wagents.context import get_repo_root

    repo = get_repo_root()
    result = _materialize(repo, check=check)
    if not result.get("ok", True):
        raise typer.Exit(code=1)
    if check:
        changed = result.get("touched", [])
        if changed:
            typer.echo("APM materialize is stale. Run: uv run wagents apm materialize", err=True)
            typer.echo("Would update:")
            for p in changed:
                typer.echo(f"  {p}")
            raise typer.Exit(code=1)
        typer.echo("APM materialize is up to date.")
        raise typer.Exit(code=0)
    touched = result.get("touched", [])
    typer.echo(f"Materialized {len(touched)} path(s):")
    for p in touched:
        typer.echo(f"  {p}")
    raise typer.Exit(code=0)


@apm_app.command("doctor")
def apm_doctor(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
) -> None:
    """Verify opencode.json contract, apm.yml presence, and that .apm/ was generated."""
    from wagents.apm import doctor as _apm_doctor
    from wagents.context import get_repo_root
    from wagents.output import emit_structured_output, normalize_output_format

    repo = get_repo_root()
    report = _apm_doctor(repo)
    fmt = normalize_output_format(format_)
    if fmt == "text":
        status = "ok" if report.get("ok") else "FAIL"
        typer.echo(f"apm doctor: {status}")
        for c in report.get("checks", []):
            cstatus = "ok" if c.get("ok") else "FAIL"
            msg = c.get("message", "")
            suffix = f" ({msg})" if msg else ""
            typer.echo(f"  {c['name']}: {cstatus}{suffix}")
    else:
        emit_structured_output(fmt, json_data=report)
    raise typer.Exit(code=0 if report.get("ok") else 1)


def run() -> None:
    """Console entry point with opt-in telemetry recording."""
    exit_code = 0
    try:
        app(standalone_mode=False)
    except typer.Exit as exc:
        exit_code = exc.exit_code
        raise SystemExit(exc.exit_code) from exc
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 0
        raise
    finally:
        end_command_telemetry(exit_code)


if __name__ == "__main__":
    run()
