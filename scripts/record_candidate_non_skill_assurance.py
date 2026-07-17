#!/usr/bin/env python3
"""Record secret-free runtime assurance for the July 2026 candidate corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
OUTPUT = MANIFEST_DIR / "non-skill-install-assurance.json"
INTEGRATION_TARGETS = MANIFEST_DIR / "integration-targets.json"
ALL_RECORDS = MANIFEST_DIR / "all-records.json"
SOURCE_FILES = {
    "integration_decisions": MANIFEST_DIR / "integration-decisions.json",
    "mcp_registry": ROOT / "config" / "mcp-registry.json",
    "plugin_registry": ROOT / "config" / "plugin-extension-registry.json",
    "tooling_policy": ROOT / "config" / "tooling-policy.json",
}
EXPECTED_UNIQUE_TARGETS = 289
AUTH_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
NON_SKILL_TYPES = {"CLI/tool", "MCP server", "plugin", "library"}
ALLOWED_DISPOSITIONS = {
    "collection-extracted",
    "configured-disabled-mcp",
    "hard-quarantined",
    "installed-cli",
    "installed-library",
    "installed-mixed-runtime",
    "integrated-non-executable-surface",
    "not-applicable-skill-only",
    "registered-disabled-plugin",
    "registered-plugin",
}


def _artifact(
    kind: str,
    manager: str,
    package: str,
    version: str,
    *,
    executables: tuple[str, ...] = (),
    paths: tuple[str, ...] = (),
    probe: tuple[str, ...] = (),
    probe_contains: str = "",
    probe_exit_codes: tuple[int, ...] = (0,),
    probe_env: dict[str, str] | None = None,
    mcp_server: str = "",
    plugin_id: str = "",
    plugin_enabled: bool | None = None,
    auth_env_names: tuple[str, ...] = (),
    config_surfaces: tuple[str, ...] = (),
    notes: str = "",
) -> dict[str, Any]:
    return {
        "kind": kind,
        "package_manager": manager,
        "package_name": package,
        "version": version,
        "executables": list(executables),
        "paths": list(paths),
        "probe": list(probe),
        "probe_contains": probe_contains,
        "probe_exit_codes": list(probe_exit_codes),
        "probe_env": dict(probe_env or {}),
        "mcp_server": mcp_server,
        "plugin_id": plugin_id,
        "plugin_enabled": plugin_enabled,
        "auth_env_names": sorted(set(auth_env_names)),
        "config_surfaces": list(config_surfaces),
        "notes": notes,
    }


def _cli(
    manager: str,
    package: str,
    version: str,
    executables: tuple[str, ...],
    *,
    probe: tuple[str, ...] = (),
    probe_contains: str = "",
    probe_exit_codes: tuple[int, ...] = (0,),
    probe_env: dict[str, str] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    return _artifact(
        "cli",
        manager,
        package,
        version,
        executables=executables,
        probe=probe,
        probe_contains=probe_contains,
        probe_exit_codes=probe_exit_codes,
        probe_env=probe_env,
        notes=notes,
    )


def _mcp(
    manager: str,
    package: str,
    version: str,
    server: str,
    *,
    executables: tuple[str, ...] = (),
    auth_env_names: tuple[str, ...] = (),
    notes: str = "",
) -> dict[str, Any]:
    return _artifact(
        "mcp",
        manager,
        package,
        version,
        executables=executables,
        mcp_server=server,
        auth_env_names=auth_env_names,
        config_surfaces=(f"config/mcp-registry.json:{server}", "mcp/mcphub/mcp_settings.json"),
        notes=notes,
    )


def _plugin(
    plugin_id: str,
    version: str,
    enabled: bool,
    *,
    notes: str = "",
) -> dict[str, Any]:
    return _artifact(
        "plugin",
        "codex-plugin",
        plugin_id,
        version,
        plugin_id=plugin_id,
        plugin_enabled=enabled,
        config_surfaces=("config/plugin-extension-registry.json",),
        notes=notes,
    )


def _library(manager: str, package: str, version: str, path: str, *, notes: str = "") -> dict[str, Any]:
    return _artifact("library", manager, package, version, paths=(path,), notes=notes)


RUNTIME_SPECS: dict[str, list[dict[str, Any]]] = {
    "https://github.com/ratnaditya-j/csvglow": [
        _cli("uv-tool", "csvglow", "0.1.0", ("csvglow",), probe=("csvglow", "--version"), probe_contains="0.1.0"),
        _mcp(
            "uvx",
            "csvglow",
            "0.1.0",
            "csvglow",
            executables=("csvglow",),
            notes="The MCP entrypoint is csvglow --mcp; do not use that flag as a smoke probe.",
        ),
    ],
    "https://github.com/devenjarvis/lathe": [
        _cli(
            "go",
            "github.com/devenjarvis/lathe",
            "0.4.0",
            ("lathe",),
            probe=("lathe", "--version"),
            probe_contains="0.4.0",
        ),
    ],
    "https://github.com/jakubantalik/transitions.dev": [
        _cli(
            "npm",
            "transitions-refine",
            "0.3.34",
            ("refine",),
            probe=("refine", "help"),
            probe_contains="Refine",
            probe_exit_codes=(1,),
            notes="Never probe refine with --help or --version because those flags default to live mode.",
        ),
    ],
    "https://github.com/tanstack/cli": [
        _cli("npm", "@tanstack/cli", "0.69.5", ("tanstack",)),
    ],
    "https://github.com/plannotator/tot": [
        _cli("npm", "@plannotator/tot", "0.1.2", ("tot",)),
    ],
    "https://github.com/better-auth/better-icons": [
        _cli("npm", "better-icons", "1.0.4", ("better-icons",)),
        _mcp("npm", "better-icons", "1.0.4", "better-icons", executables=("better-icons",)),
    ],
    "https://github.com/charleswiltgen/axiom": [
        _mcp(
            "npm",
            "axiom-mcp",
            "27.0.0-beta.22",
            "axiom-mcp",
            executables=("axiom-mcp",),
            notes="No --help or --version probe is safe; every invocation starts MCP stdio.",
        ),
        _plugin(
            "axiom@axiom-marketplace",
            "27.0.0-beta.22",
            False,
            notes="Disabled because the plugin contributes broad lifecycle hooks and Apple/Xcode process actions.",
        ),
    ],
    "https://github.com/nvidia/skillspector": [
        _cli(
            "uv-tool-git",
            "NVIDIA/SkillSpector",
            "2.3.13",
            ("skillspector",),
            probe=("skillspector", "--version"),
            probe_contains="2.3.13",
        ),
    ],
    "https://github.com/auriti-labs/geo-optimizer-skill": [
        _cli(
            "uv-tool",
            "geo-optimizer-skill[all]",
            "4.15.0",
            ("geo", "geo-mcp", "geo-web"),
            probe=("geo", "--version"),
            probe_contains="4.15.0",
        ),
        _mcp(
            "uvx",
            "geo-optimizer-skill[mcp]",
            "4.15.0",
            "geo-mcp",
            executables=("geo-mcp",),
            auth_env_names=(
                "ANTHROPIC_API_KEY",
                "GEO_LLM_API_KEY",
                "GROQ_API_KEY",
                "OPENAI_API_KEY",
                "PERPLEXITY_API_KEY",
            ),
            notes="Base audits are keyless; geo-mcp --help starts the server and is not a smoke probe.",
        ),
    ],
    "https://github.com/elvisun/newsjack": [
        _cli(
            "npm",
            "newsjack",
            "0.1.15",
            ("newsjack",),
            probe=("newsjack", "version"),
            probe_contains="0.1.15",
            probe_env={"NEWSJACK_NO_AUTO_UPDATE": "1"},
        ),
    ],
    "https://github.com/varnan-tech/opendirectory": [
        _cli(
            "npm",
            "@opendirectory.dev/skills",
            "0.1.97",
            ("opendirectory",),
            probe=("opendirectory", "--version"),
            probe_contains="0.1.97",
            notes=(
                "The npm gitHead differs from current public main; registry integrity is retained as provenance "
                "evidence."
            ),
        ),
    ],
    "https://github.com/panniantong/agent-reach": [
        _cli(
            "uv-tool-git",
            "Panniantong/Agent-Reach",
            "1.5.0",
            ("agent-reach",),
            probe=("agent-reach", "--version"),
            probe_contains="1.5.0",
            notes="Setup, browser-cookie, scraping, and platform login commands remain explicit user actions.",
        ),
    ],
    "https://github.com/heygen-com/hyperframes": [
        _cli(
            "npm",
            "hyperframes",
            "0.7.59",
            ("hyperframes",),
            probe=("hyperframes", "--version"),
            probe_contains="0.7.59",
            probe_env={"DO_NOT_TRACK": "1", "HYPERFRAMES_NO_TELEMETRY": "1"},
        ),
        _plugin(
            "hyperframes@hyperframes-upstream",
            "0.7.59",
            False,
            notes=(
                "Disabled because its Bash hook intercepts git commit and runs project build, lint, and typecheck "
                "commands."
            ),
        ),
    ],
    "https://github.com/pythoughts-labs/designer-skill": [
        _mcp(
            "npm",
            "designer-skill-mcp",
            "0.14.0",
            "designer-skill-mcp",
            executables=("designer-skill-mcp",),
            notes="Version probing is safe; no-argument invocation starts MCP stdio.",
        ),
        _plugin("designer-skill@awesome-codex-plugins", "0.13.0", True),
    ],
    "https://github.com/mohamedabdallah-14/prompt-to-asset": [
        _cli(
            "npm",
            "prompt-to-asset",
            "0.5.1",
            ("p2a", "prompt-to-asset"),
            probe=("p2a", "--version"),
            probe_contains="0.5.1",
        ),
        _mcp(
            "npm",
            "prompt-to-asset",
            "0.5.1",
            "prompt-to-asset",
            executables=("p2a", "prompt-to-asset"),
            auth_env_names=(
                "BFL_API_KEY",
                "CLOUDFLARE_ACCOUNT_ID",
                "CLOUDFLARE_API_TOKEN",
                "FAL_API_KEY",
                "FAL_KEY",
                "FREEPIK_API_KEY",
                "GEMINI_API_KEY",
                "GOOGLE_API_KEY",
                "HF_TOKEN",
                "HUGGINGFACE_API_KEY",
                "IDEOGRAM_API_KEY",
                "LEONARDO_API_KEY",
                "NIM_API_KEY",
                "NVIDIA_API_KEY",
                "OPENAI_API_KEY",
                "PIXAZO_API_KEY",
                "PIXAZO_SUBSCRIPTION_KEY",
                "RECRAFT_API_KEY",
                "REPLICATE_API_KEY",
                "REPLICATE_API_TOKEN",
                "STABILITY_API_KEY",
                "TOGETHER_API_KEY",
            ),
            notes="MCP defaults to tracked dry-run mode; provider spend and output writes require explicit approval.",
        ),
        _plugin("prompt-to-asset@awesome-codex-plugins", "0.1.0", True),
    ],
    "https://github.com/mohamedabdallah-14/unslop": [
        _cli("uv-tool", "unslop", "0.6.2", ("unslop",), probe=("unslop", "--version"), probe_contains="0.6.2"),
        _plugin("unslop@awesome-codex-plugins", "0.6.2", True),
    ],
    "https://github.com/googleworkspace/cli": [
        _cli("npm", "@googleworkspace/cli", "0.22.5", ("gws",)),
    ],
    "https://github.com/mobile-next/mobile-mcp": [
        _mcp(
            "npm",
            "@mobilenext/mobile-mcp",
            "0.0.62",
            "mobile-mcp",
            executables=("mcp-server-mobile",),
            notes=(
                "Device and simulator automation remains disabled pending target, signing, privacy, and "
                "destructive-action review."
            ),
        ),
    ],
    "https://github.com/modelcontextprotocol/inspector": [
        _cli(
            "npm",
            "@modelcontextprotocol/inspector",
            "0.22.0",
            ("mcp-inspector",),
            notes="Installed as an inspection client, never configured as an MCP server.",
        ),
    ],
    "https://github.com/antvis/mcp-server-chart": [
        _mcp(
            "npm",
            "@antv/mcp-server-chart",
            "0.9.10",
            "antv-chart",
            executables=("mcp-server-chart",),
            auth_env_names=("ANTV_CHART_DISABLED_TOOLS", "SERVICE_ID", "VIS_REQUEST_SERVER"),
        ),
    ],
    "https://github.com/avivsinai/langfuse-mcp": [
        _mcp(
            "uv-tool",
            "langfuse-mcp",
            "0.10.0",
            "langfuse-mcp",
            executables=("langfuse-mcp",),
            auth_env_names=("LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"),
        ),
    ],
    "https://github.com/johnvouros/nullcost-plugin": [
        _mcp("npm", "nullcost-plugin", "0.1.6", "nullcost", executables=("nullcost-plugin",)),
    ],
    "https://github.com/lumiaqian/openspec-mcp": [
        _mcp("npm", "openspec-mcp", "0.4.2", "openspec-mcp"),
    ],
    "https://github.com/openags/paper-search-mcp": [
        _mcp(
            "uv-tool",
            "paper-search-mcp",
            "0.1.4",
            "paper-search-mcp",
            executables=("paper-search-mcp",),
            auth_env_names=(
                "PAPER_SEARCH_MCP_CORE_API_KEY",
                "SEMANTIC_SCHOLAR_API_KEY",
                "UNPAYWALL_EMAIL",
                "ZENODO_ACCESS_TOKEN",
            ),
        ),
    ],
    "https://github.com/nteract/semiotic": [
        _mcp("npm", "semiotic", "3.7.5", "semiotic", executables=("semiotic-ai", "semiotic-mcp")),
    ],
    "https://github.com/kyurish/mcp-dashboards": [
        _mcp("npm", "mcp-dashboards", "2.4.0", "mcp-dashboards", executables=("mcp-dashboards",)),
    ],
    "https://github.com/yctimlin/mcp_excalidraw": [
        _mcp(
            "npm",
            "mcp-excalidraw-server",
            "1.1.0",
            "mcp-excalidraw",
            executables=("mcp-excalidraw-server", "excalidraw-canvas"),
        ),
    ],
    "https://github.com/marzukia/charted": [
        _cli("uv-tool", "charted", "1.2.1", ("charted", "charted-mcp")),
        _mcp("uvx", "charted[mcp]", "1.2.1", "charted", executables=("charted-mcp",)),
    ],
    "https://github.com/iannuttall/dotagents": [
        _cli("bun", "@iannuttall/dotagents", "0.1.3", ("dotagents",)),
    ],
    "https://github.com/sflueckiger/specboard": [
        _cli("bun", "@sflueckiger/specboard", "1.1.2", ("specboard",)),
    ],
    "https://github.com/epicsagas/llm-transpile": [
        _cli("cargo", "llm-transpile", "0.4.1", ("transpile",)),
    ],
    "https://github.com/teng-lin/notebooklm-py": [
        _cli("uv-tool", "notebooklm-py", "0.7.3", ("notebooklm",)),
    ],
    "https://github.com/wenqingyu/ralphy-openspec": [
        _cli("npm", "ralphy-spec", "0.3.6", ("ralphy-spec",)),
    ],
    "https://github.com/jixoai/openspecui": [
        _cli(
            "npm",
            "openspecui",
            "5.0.0",
            ("openspecui",),
            notes=(
                "Native watcher and SQLite lifecycle scripts were allowlisted; optional node-llama-cpp postinstall "
                "remained blocked."
            ),
        ),
    ],
    "https://github.com/toruai/openspec-ui": [
        _cli("standalone", "openspec-ui", "pinned-checksum", ("openspec-ui",)),
    ],
    "https://github.com/wxhou/openspec-playwright": [
        _cli("npm", "openspec-playwright", "0.3.56", ("openspec-pw",)),
    ],
    "https://github.com/millionco/react-doctor": [
        _cli("npm", "react-doctor", "0.7.6", ("react-doctor",)),
    ],
    "https://github.com/aitytech/agentkits-marketing": [
        _library(
            "npm",
            "@aitytech/agentkits-marketing",
            "1.7.2",
            "~/.local/lib/node_modules/@aitytech/agentkits-marketing",
            notes="Package contributes agent/skill assets rather than a standalone executable.",
        ),
    ],
    "https://github.com/hardikpandya/stop-slop": [
        _cli("npm", "deslop-cli", "0.7.6", ("deslop",)),
    ],
    "https://github.com/rorkai/app-store-connect-cli-skills": [
        _cli(
            "standalone",
            "asc",
            "pinned-checksum",
            ("asc",),
            notes="Credentials, signing, and App Store Connect mutations remain user-owned and confirmation-gated.",
        ),
    ],
    "https://github.com/tt-a1i/archify": [
        _cli(
            "skill-bundled",
            "archify",
            "audited-source",
            ("archify",),
            notes=(
                "The global command is a symlink to the audited skill-bundled CLI, not the unrelated public npm "
                "package."
            ),
        ),
    ],
    "https://github.com/hashgraph-online/hol-guard-plugin": [
        _plugin("hol-guard-plugin@awesome-codex-plugins", "0.1.0", False),
    ],
    "https://github.com/papersflow-ai/papersflow-codex-plugin": [
        _plugin("papersflow-codex-plugin@awesome-codex-plugins", "1.0.0", False),
        _mcp(
            "hosted",
            "papersflow",
            "account-bound",
            "papersflow",
            notes="Hosted OAuth/account surface remains disabled.",
        ),
    ],
    "https://github.com/summer521521/zotero_research_plugin": [
        _plugin("zotero-research-tools@awesome-codex-plugins", "0.1.5", False),
    ],
    "https://github.com/tim-osterhus/codex-remotion-plugin": [
        _plugin("remotion@awesome-codex-plugins", "0.1.0", True),
    ],
    "https://github.com/hashgraph-online/awesome-codex-plugins/tree/main/plugins/mturac/env-lint": [
        _plugin("env-lint@candidate-corpus-local", "0.1.0", True),
    ],
    "https://github.com/hashgraph-online/awesome-codex-plugins/tree/main/plugins/mturac/secret-guard": [
        _plugin("secret-guard@candidate-corpus-local", "0.1.0", True),
    ],
    "https://github.com/hashgraph-online/awesome-codex-plugins/tree/main/plugins/mturac/commit-narrator": [
        _plugin("commit-narrator@candidate-corpus-local", "0.1.0", True),
    ],
    "https://github.com/yujiachen-y/codebase-recon-skill": [
        _plugin("codebase-recon@awesome-codex-plugins", "1.0.0", True),
    ],
    "https://github.com/hyhmrright/brooks-lint": [
        _plugin("brooks-lint@awesome-codex-plugins", "1.4.0", True),
    ],
    "https://github.com/hdeibler/universal-design-principles": [
        _plugin("universal-design-principles@awesome-codex-plugins", "1.0.0", True),
    ],
    "https://github.com/papischolz/roadmapsmith": [
        _plugin("roadmapsmith@awesome-codex-plugins", "0.12.0", True),
    ],
}


def now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def semantic_sha256(path: Path) -> str:
    payload = load_json(path)
    payload.pop("generated_at", None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def source_fingerprints() -> dict[str, str]:
    return {name: semantic_sha256(path) for name, path in SOURCE_FILES.items()}


def display_path(path: Path) -> str:
    try:
        return "~/" + str(path.resolve().relative_to(Path.home().resolve()))
    except ValueError:
        return str(path.resolve().relative_to(ROOT)) if path.resolve().is_relative_to(ROOT) else path.name


def plugin_inventory() -> dict[str, dict[str, Any]]:
    completed = subprocess.run(
        ["codex", "plugin", "list", "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(completed.stdout)
    return {
        str(item.get("pluginId")): item
        for item in payload.get("installed", [])
        if isinstance(item, dict) and item.get("pluginId")
    }


def run_probe(spec: dict[str, Any]) -> tuple[str, int | None]:
    probe = spec.get("probe", [])
    if not probe:
        return "path-or-config-verified", None
    env = os.environ.copy()
    env.update({str(key): str(value) for key, value in spec.get("probe_env", {}).items()})
    try:
        completed = subprocess.run(
            [str(value) for value in probe],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "failed", None
    combined = completed.stdout + completed.stderr
    expected_codes = {int(value) for value in spec.get("probe_exit_codes", [0])}
    expected_text = str(spec.get("probe_contains") or "")
    ok = completed.returncode in expected_codes and (not expected_text or expected_text in combined)
    return ("passed" if ok else "failed"), completed.returncode


def evaluate_artifact(
    spec: dict[str, Any],
    mcp_servers: dict[str, Any],
    plugins: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    item = {
        key: value
        for key, value in spec.items()
        if key not in {"probe", "probe_contains", "probe_exit_codes", "probe_env", "paths"}
    }
    resolved_paths: list[str] = []
    path_checks: list[bool] = []
    for executable in spec.get("executables", []):
        located = shutil.which(str(executable))
        path_checks.append(bool(located))
        if located:
            resolved_paths.append(display_path(Path(located)))
    for raw_path in spec.get("paths", []):
        path = Path(str(raw_path).replace("~/", str(Path.home()) + "/")).expanduser()
        path_checks.append(path.exists())
        if path.exists():
            resolved_paths.append(display_path(path))

    mcp_name = str(spec.get("mcp_server") or "")
    mcp_configured = None
    mcp_enabled = None
    if mcp_name:
        server = mcp_servers.get(mcp_name)
        mcp_configured = isinstance(server, dict)
        mcp_enabled = server.get("enabled") if isinstance(server, dict) else None

    plugin_id = str(spec.get("plugin_id") or "")
    plugin_installed = None
    plugin_enabled = None
    if plugin_id:
        plugin = plugins.get(plugin_id)
        plugin_installed = isinstance(plugin, dict) and plugin.get("installed") is True
        plugin_enabled = plugin.get("enabled") if isinstance(plugin, dict) else None

    smoke_status, smoke_exit_code = run_probe(spec)
    expected_plugin_enabled = spec.get("plugin_enabled")
    verified = all(path_checks) if path_checks else True
    if mcp_name:
        verified = verified and mcp_configured is True and mcp_enabled is False
    if plugin_id:
        verified = verified and plugin_installed is True and plugin_enabled is expected_plugin_enabled
    verified = verified and smoke_status != "failed"

    item.update({
        "resolved_paths": sorted(set(resolved_paths)),
        "path_exists": all(path_checks) if path_checks else None,
        "smoke_status": smoke_status,
        "smoke_exit_code": smoke_exit_code,
        "mcp_configured": mcp_configured,
        "mcp_enabled": mcp_enabled,
        "plugin_installed": plugin_installed,
        "plugin_enabled": plugin_enabled,
        "verified": verified,
    })
    return item


def disposition_for(artifacts: list[dict[str, Any]]) -> str:
    kinds = {str(item.get("kind")) for item in artifacts}
    if len(kinds) > 1:
        return "installed-mixed-runtime"
    if "mcp" in kinds:
        return "configured-disabled-mcp"
    if "plugin" in kinds:
        return (
            "registered-plugin"
            if any(item.get("plugin_enabled") is True for item in artifacts)
            else "registered-disabled-plugin"
        )
    if "library" in kinds:
        return "installed-library"
    return "installed-cli"


def build_assurance() -> dict[str, Any]:
    targets = load_json(INTEGRATION_TARGETS).get("items", [])
    records = load_json(ALL_RECORDS).get("records", [])
    mcp_servers = load_json(SOURCE_FILES["mcp_registry"]).get("servers", {})
    plugins = plugin_inventory()
    if not isinstance(targets, list) or not isinstance(records, list) or not isinstance(mcp_servers, dict):
        raise ValueError("candidate inputs have invalid collection shapes")

    record_types: dict[str, set[str]] = defaultdict(set)
    for record in records:
        if not isinstance(record, dict):
            continue
        key = str(record.get("normalized_url") or "").lower()
        record_types[key].update(str(value) for value in record.get("artifact_types_found", []) if value)

    rows: list[dict[str, Any]] = []
    for target in targets:
        if not isinstance(target, dict):
            raise ValueError("integration target rows must be objects")
        url = str(target.get("normalized_url") or "")
        key = url.lower()
        artifact_types = sorted(record_types.get(key, set()))
        hard_blocked = bool(target.get("hard_blocked"))
        artifacts = [evaluate_artifact(spec, mcp_servers, plugins) for spec in RUNTIME_SPECS.get(key, [])]
        if hard_blocked:
            disposition = "hard-quarantined"
            reason = "Hard quarantine prohibits installation and activation."
        elif artifacts:
            disposition = disposition_for(artifacts)
            reason = "Audited runtime artifacts are installed or registered with their recorded activation boundary."
        elif "awesome list" in artifact_types:
            disposition = "collection-extracted"
            reason = (
                "Collection guidance is represented by bounded repo-native catalog entries; no monolithic runtime "
                "exists."
            )
        elif set(artifact_types) & NON_SKILL_TYPES:
            disposition = "integrated-non-executable-surface"
            reason = (
                "The source's non-skill material has no separate audited durable runtime beyond its catalog, agent, "
                "library, or workflow integration."
            )
        else:
            disposition = "not-applicable-skill-only"
            reason = (
                "The source is installed through skill harness reconciliation and has no independent runtime artifact."
            )
        auth_names = sorted({name for artifact in artifacts for name in artifact.get("auth_env_names", [])})
        surfaces = sorted({surface for artifact in artifacts for surface in artifact.get("config_surfaces", [])})
        rows.append({
            "normalized_url": url,
            "raw_indexes": target.get("raw_indexes", []),
            "artifact_types_found": artifact_types,
            "decision": target.get("intake_decision"),
            "integration_classification": target.get("integration_classification"),
            "runtime_disposition": disposition,
            "artifacts": artifacts,
            "config_surfaces": surfaces,
            "activation_state": "quarantined"
            if hard_blocked
            else (
                "verified"
                if all(item.get("verified") for item in artifacts)
                else "not-applicable"
                if not artifacts
                else "incomplete"
            ),
            "auth_env_names": auth_names,
            "blocker": "security-quarantine" if hard_blocked else "",
            "reason": reason,
        })

    disposition_counts = Counter(row["runtime_disposition"] for row in rows)
    artifact_counts = Counter(artifact["kind"] for row in rows for artifact in row["artifacts"])
    failed_artifacts = [
        f"{row['normalized_url']}:{artifact['package_name']}"
        for row in rows
        for artifact in row["artifacts"]
        if not artifact.get("verified")
    ]
    complete = (
        len(rows) == EXPECTED_UNIQUE_TARGETS
        and len({row["normalized_url"].lower() for row in rows}) == EXPECTED_UNIQUE_TARGETS
        and not failed_artifacts
        and all(not row["artifacts"] for row in rows if row["runtime_disposition"] == "hard-quarantined")
    )
    return {
        "version": 1,
        "generated_at": now(),
        "assurance_kind": "candidate-non-skill-live-install",
        "complete": complete,
        "unique_target_count": len(rows),
        "source_fingerprints": source_fingerprints(),
        "items": rows,
        "totals": {
            "runtime_artifacts": sum(len(row["artifacts"]) for row in rows),
            "verified_runtime_artifacts": sum(
                1 for row in rows for artifact in row["artifacts"] if artifact.get("verified")
            ),
            "failed_runtime_artifacts": len(failed_artifacts),
            "disposition_counts": dict(sorted(disposition_counts.items())),
            "artifact_kind_counts": dict(sorted(artifact_counts.items())),
        },
        "failed_artifacts": failed_artifacts,
        "notes": (
            "This machine-local evidence records package paths, bounded smoke probes, disabled MCP registrations, "
            "plugin activation state, and terminal non-runtime dispositions without storing credential values."
        ),
    }


def validation_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    items = payload.get("items", [])
    if not isinstance(items, list) or len(items) != EXPECTED_UNIQUE_TARGETS:
        errors.append("non-skill assurance must contain 289 item rows")
        return errors
    expected_urls = {
        str(item.get("normalized_url") or "").lower()
        for item in load_json(INTEGRATION_TARGETS).get("items", [])
        if isinstance(item, dict)
    }
    actual_urls = [str(item.get("normalized_url") or "").lower() for item in items if isinstance(item, dict)]
    if len(actual_urls) != len(set(actual_urls)) or set(actual_urls) != expected_urls:
        errors.append("non-skill assurance URL coverage is incomplete or duplicated")
    if payload.get("source_fingerprints") != source_fingerprints():
        errors.append("non-skill assurance source fingerprints are stale")
    for item in items:
        if not isinstance(item, dict):
            errors.append("non-skill assurance rows must be objects")
            continue
        disposition = item.get("runtime_disposition")
        if disposition not in ALLOWED_DISPOSITIONS:
            errors.append(f"invalid runtime disposition for {item.get('normalized_url')}: {disposition}")
        artifacts = item.get("artifacts", [])
        if not isinstance(artifacts, list):
            errors.append(f"artifact list is invalid for {item.get('normalized_url')}")
            continue
        if disposition == "hard-quarantined" and artifacts:
            errors.append(f"hard-quarantined target has runtime artifacts: {item.get('normalized_url')}")
        for name in item.get("auth_env_names", []):
            if not isinstance(name, str) or not AUTH_NAME_RE.fullmatch(name):
                errors.append(f"invalid auth env name for {item.get('normalized_url')}: {name!r}")
        for artifact in artifacts:
            if not isinstance(artifact, dict) or artifact.get("verified") is not True:
                errors.append(f"unverified runtime artifact for {item.get('normalized_url')}")
                continue
            for path in artifact.get("resolved_paths", []):
                if str(path).startswith("/") or "/Users/" in str(path):
                    errors.append(f"absolute home path leaked for {item.get('normalized_url')}")
            if artifact.get("kind") == "mcp" and artifact.get("mcp_enabled") is not False:
                errors.append(f"candidate MCP is not disabled for {item.get('normalized_url')}")
    if payload.get("complete") is not True:
        errors.append("non-skill assurance is not complete")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        if not OUTPUT.is_file():
            print(json.dumps({"ok": False, "errors": [f"missing {OUTPUT.relative_to(ROOT)}"]}, indent=2))
            return 1
        errors = validation_errors(load_json(OUTPUT))
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
        return 1 if errors else 0

    payload = build_assurance()
    errors = validation_errors(payload)
    if args.apply:
        OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "complete": payload["complete"],
                "unique_target_count": payload["unique_target_count"],
                "totals": payload["totals"],
                "errors": errors,
            },
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
