#!/usr/bin/env python3
"""Run bounded semantic canaries for enabled candidate Codex plugins."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import secrets
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from wagents.candidate_evidence import (
    FILESYSTEM_DIGEST_ALGORITHM,
    RUNTIME_DIGEST_IGNORED_DIRS,
    filesystem_digest,
    receipt_metadata,
)
from wagents.candidate_plugin_provenance import (
    PLUGIN_CONTENT_DIGEST_ALGORITHM,
    PLUGIN_CONTENT_IGNORED_DIRS,
    codex_plugin_live_state,
    load_plugin_provenance_lock,
    plugin_cache_path,
    plugin_content_sha256,
    plugin_installed_package_origin,
    plugin_lock_entry_sha256,
    resolve_locked_marketplace_source,
    verify_marketplace_checkout,
    verify_plugin_content,
)
from wagents.candidate_receipts import ReceiptStore
from wagents.candidate_sandbox import SANDBOX_REQUIRED_ENV, prepare_sandboxed_subprocess, sandbox_environment
from wagents.process_lifecycle import (
    run_after_process_lifecycle_gate,
    terminate_process_group,
)

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
RECEIPTS = MANIFEST_DIR / "runtime-activation-receipts.json"
PROVENANCE_LOCK = MANIFEST_DIR / "plugin-provenance-lock.json"
PLUGIN_REGISTRY = ROOT / "config" / "plugin-extension-registry.json"
RUNTIME_STATE = Path("~/.local/share/wagents/candidate-runtime").expanduser()
ACTIVATION_SCRIPT = ROOT / "scripts" / "record_candidate_runtime_activation.py"
CODEX_CACHE = Path.home() / ".codex" / "plugins" / "cache"
HOST_CODEX_HOME = Path.home() / ".codex"
HOST_CODEX_AUTH = HOST_CODEX_HOME / "auth.json"
MARKETPLACE_ROOTS = {
    "candidate-corpus-local": Path.home() / ".local" / "share" / "wagents" / "candidate-corpus-plugin-marketplace",
    "awesome-codex-plugins": HOST_CODEX_HOME / ".tmp" / "marketplaces" / "awesome-codex-plugins",
}
TLS_TRUST_READ_ROOTS = tuple(
    path
    for path in (
        Path("/Library/Keychains"),
        Path("/etc/ssl"),
        Path("/private/etc/ssl"),
        Path("/System/Library/Keychains"),
    )
    if path.exists()
)
SAFE_ENV_KEYS = frozenset({"LANG", "LC_ALL", "LC_CTYPE", "LOGNAME", "SHELL", "USER"})
SAFE_ENV_PREFIXES = ("LC_",)
FIXED_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
PYTHON_EXECUTABLE = Path(sys.executable).resolve(strict=True)
AUDITED_EXECUTABLE_CANDIDATES = {
    "bash": (Path("/bin/bash"), Path("/opt/homebrew/bin/bash"), Path("/usr/local/bin/bash")),
    "codex": (
        Path("/opt/homebrew/bin/codex"),
        Path("/usr/local/bin/codex"),
        Path.home() / ".local" / "bin" / "codex",
    ),
    "git": (Path("/opt/homebrew/bin/git"), Path("/usr/local/bin/git"), Path("/usr/bin/git")),
    "node": (Path("/opt/homebrew/bin/node"), Path("/usr/local/bin/node"), Path("/usr/bin/node")),
    "python": (PYTHON_EXECUTABLE,),
}
TRUSTED_HARNESS_OPERATIONS = frozenset({"trusted-harness-fixed-version-probe"})
PLUGIN_EXECUTABLE_ALLOWLIST = {
    "commit-narrator@candidate-corpus-local": frozenset({"scripts/narrate.py"}),
    "env-lint@candidate-corpus-local": frozenset({"scripts/envlint.py"}),
    "secret-guard@candidate-corpus-local": frozenset({"scripts/guard.py"}),
}
PLUGIN_MANIFEST_EXECUTION_KEYS = frozenset({
    "commands",
    "entry",
    "hooks",
    "mcpServers",
    "mcp_servers",
    "server",
    "startup",
})
PACKAGE_LIFECYCLE_KEYS = frozenset({"install", "postinstall", "preinstall", "prepare", "start"})
DIGEST_IGNORED_DIRS = set(RUNTIME_DIGEST_IGNORED_DIRS)
DIGEST_ALGORITHM = FILESYSTEM_DIGEST_ALGORITHM
ROADMAP_EDIT_MARKER = "WAGENTS_ROADMAP_EDIT "

SCRIPT_PLUGINS = {
    "commit-narrator@candidate-corpus-local": "commit-narrator",
    "env-lint@candidate-corpus-local": "env-lint",
    "secret-guard@candidate-corpus-local": "secret-guard",
    "unslop@awesome-codex-plugins": "unslop",
}
MODEL_PLUGINS = {
    "universal-design-principles@awesome-codex-plugins": "universal-design-principles",
    "brooks-lint@awesome-codex-plugins": "brooks-lint",
    "roadmapsmith@awesome-codex-plugins": "roadmapsmith",
    "codebase-recon@awesome-codex-plugins": "codebase-recon",
}
EXPECTED_ENABLED_PLUGINS = frozenset(SCRIPT_PLUGINS | MODEL_PLUGINS)
EXPECTED_DISABLED_CODEX_PLUGINS = frozenset({
    "axiom@axiom-marketplace",
    "designer-skill@awesome-codex-plugins",
    "hol-guard-plugin@awesome-codex-plugins",
    "hyperframes@hyperframes-upstream",
    "papersflow-codex-plugin@awesome-codex-plugins",
    "prompt-to-asset@awesome-codex-plugins",
    "remotion@awesome-codex-plugins",
    "zotero-research-tools@awesome-codex-plugins",
})
EXPECTED_OPENCODE_PLUGINS = frozenset({"candidate-opencode-plugin-openspec"})
EXPECTED_PLUGIN_ARTIFACT_COUNT = 17
UNPROVEN_BEHAVIOR_PLUGINS: frozenset[str] = frozenset()
UNIVERSAL_DESIGN_PLUGIN_ID = "universal-design-principles@awesome-codex-plugins"
UNIVERSAL_DESIGN_SKILL_SELECTORS = (
    "$universal-design-principles:errors",
    "$universal-design-principles:accessibility",
    "$universal-design-principles:hierarchy",
    "$universal-design-principles:hicks-law",
    "$universal-design-principles:affordance",
)
UNIVERSAL_DESIGN_FINDING_SOURCES = {
    "accessibility": "$universal-design-principles:accessibility",
    "perception": "$universal-design-principles:hierarchy",
    "cognition": "$universal-design-principles:hicks-law",
    "interaction": "$universal-design-principles:affordance",
}
UNIVERSAL_DESIGN_FIXTURE_SIGNALS = {
    "accessibility": "empty-aria-label",
    "perception": "color-only-error",
    "cognition": "twelve-choice-navigation",
    "interaction": "non-semantic-click-target",
}
UNIVERSAL_DESIGN_GROUNDING_TERMS = {
    "accessibility": ("aria-label", "accessible name", "unnamed"),
    "perception": ("color", "colour", "red", "failed"),
    "cognition": ("twelve", "12", "choice", "navigation"),
    "interaction": ("onclick", "div", "non-semantic", "keyboard"),
}


@dataclass(frozen=True)
class ProcessResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    pid: int
    launch_id: str = ""
    started_at_ns: int = 0


@dataclass(frozen=True)
class ProbeResult:
    fixture_id: str
    assertions: tuple[str, ...]
    initial_pid: int
    fresh_pid: int
    output_sha256: str
    probe_kind: str
    discovery_process_id: int
    discovery_output_sha256: str
    initial_launch_id: str = ""
    initial_started_at_ns: int = 0
    fresh_launch_id: str = ""
    fresh_started_at_ns: int = 0
    discovery_launch_id: str = ""
    discovery_started_at_ns: int = 0


def activation_module():
    spec = importlib.util.spec_from_file_location("_candidate_plugin_activation", ACTIVATION_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ACTIVATION_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def audited_executable(name: str) -> Path:
    candidates = AUDITED_EXECUTABLE_CANDIDATES.get(name)
    if candidates is None:
        raise RuntimeError(f"unknown audited executable: {name}")
    for candidate in candidates:
        require(candidate.is_absolute(), f"audited executable candidate is not absolute: {candidate}")
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError(f"audited executable is unavailable: {name}: {[str(path) for path in candidates]}")


def executable_runtime_roots(*names: str) -> tuple[Path, ...]:
    roots: set[Path] = {Path(sys.prefix), Path(sys.base_prefix), PYTHON_EXECUTABLE}
    for name in names:
        executable = audited_executable(name)
        resolved = executable.resolve(strict=True)
        roots.update((executable, resolved))
        if name in {"codex", "git", "node"}:
            roots.add(resolved.parents[1])
        if name == "git":
            system_config = Path("/opt/homebrew/etc/gitconfig")
            if system_config.is_file():
                roots.add(system_config)
        if resolved.is_relative_to(Path("/opt/homebrew")):
            roots.update(
                path
                for path in (
                    Path("/opt/homebrew/Cellar"),
                    Path("/opt/homebrew/etc/openssl@3"),
                    Path("/opt/homebrew/lib"),
                    Path("/opt/homebrew/opt"),
                )
                if path.is_dir()
            )
    return tuple(sorted(roots, key=str))


def sanitized_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key in SAFE_ENV_KEYS or any(key.startswith(prefix) for prefix in SAFE_ENV_PREFIXES)
    }
    env["PATH"] = FIXED_PATH
    env.update({
        "BASH": str(audited_executable("bash")),
        "CI": "1",
        "DO_NOT_TRACK": "1",
        "NO_COLOR": "1",
        "NO_UPDATE_NOTIFIER": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    return env


def isolated_env(root: Path) -> dict[str, str]:
    env = sanitized_env()
    home = root / "home"
    codex_home = root / "codex"
    home.mkdir(mode=0o700, parents=True, exist_ok=True)
    codex_home.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = root / "tmp"
    temporary.mkdir(mode=0o700, parents=True, exist_ok=True)
    env.update({
        "CODEX_HOME": str(codex_home),
        "HOME": str(home),
        "TMPDIR": str(temporary),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "ZDOTDIR": str(home),
    })
    return env


def run(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    input_text: str | None = None,
    timeout: int = 300,
    trusted_harness_operation: str | None = None,
) -> ProcessResult:
    require(bool(argv), "plugin canary received an empty argv")
    executable = Path(argv[0])
    require(executable.is_absolute(), f"plugin canary requires an absolute executable: {argv[0]!r}")
    sandboxed = env.get(SANDBOX_REQUIRED_ENV) == "1"
    if not sandboxed:
        require(
            trusted_harness_operation in TRUSTED_HARNESS_OPERATIONS,
            "plugin canary launch requires a declared sandbox",
        )
        require(
            trusted_harness_operation == "trusted-harness-fixed-version-probe"
            and tuple(argv)
            in {
                (str(audited_executable("codex")), "--version"),
                (str(audited_executable("git")), "--version"),
                (str(PYTHON_EXECUTABLE), "--version"),
                (str(audited_executable("bash")), "--version"),
            },
            "trusted harness operation does not match its fixed version-probe argv",
        )
    launch_id = secrets.token_hex(16)
    started_at_ns = time.time_ns()
    argv, child_env = prepare_sandboxed_subprocess(argv, cwd=cwd, env=env)
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=child_env,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(input=input_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        stdout, stderr = terminate_process_group(process)
        stdout_bytes = stdout.encode() if isinstance(stdout, str) else bytes(stdout or b"")
        stderr_bytes = stderr.encode() if isinstance(stderr, str) else bytes(stderr or b"")
        raise RuntimeError(
            "plugin canary timed out: "
            f"executable={Path(argv[0]).name!r} timeout={timeout}s "
            f"stdout_bytes={len(stdout_bytes)} stdout_sha256={hashlib.sha256(stdout_bytes).hexdigest()} "
            f"stderr_bytes={len(stderr_bytes)} stderr_sha256={hashlib.sha256(stderr_bytes).hexdigest()}"
        ) from None
    return ProcessResult(
        tuple(argv),
        process.returncode,
        stdout,
        stderr,
        process.pid,
        launch_id,
        started_at_ns,
    )


TreeEntry = tuple[str, int, bytes]


def _tree_manifest(root: Path, *, ignored_dirs: frozenset[str] = frozenset()) -> dict[str, TreeEntry]:
    """Capture type, permission mode, bytes, and link targets without following links."""
    manifest: dict[str, TreeEntry] = {}

    def visit(path: Path, relative: str) -> None:
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if stat.S_ISLNK(metadata.st_mode):
            manifest[relative] = ("symlink", mode, os.readlink(path).encode())
            return
        if stat.S_ISREG(metadata.st_mode):
            manifest[relative] = ("file", mode, path.read_bytes())
            return
        if stat.S_ISDIR(metadata.st_mode):
            manifest[relative] = ("directory", mode, b"")
            for child in sorted(path.iterdir(), key=lambda item: item.name):
                child_metadata = child.lstat()
                if child.name in ignored_dirs and stat.S_ISDIR(child_metadata.st_mode):
                    continue
                child_relative = child.name if relative == "." else f"{relative}/{child.name}"
                visit(child, child_relative)
            return
        manifest[relative] = (
            "special",
            mode,
            f"{metadata.st_rdev}:{metadata.st_size}".encode(),
        )

    visit(root, ".")
    return manifest


def _update_digest(digest: Any, manifest: dict[str, TreeEntry], *, include_root: bool) -> None:
    for relative, (kind, mode, payload) in sorted(manifest.items()):
        if relative == "." and not include_root:
            continue
        for value in (relative.encode(), kind.encode(), f"{mode:o}".encode(), payload):
            digest.update(value)
            digest.update(b"\0")


def file_digest(paths: list[Path]) -> str:
    return filesystem_digest(paths, ignored_dirs=DIGEST_IGNORED_DIRS)


def content_digest(root: Path) -> str:
    return plugin_content_sha256(root)


def plugin_root(seed: dict[str, Any], *, cache_root: Path = CODEX_CACHE) -> Path:
    return plugin_cache_path(
        cache_root,
        str(seed["plugin_id"]),
        str(seed["version"]),
    )


def source_shas() -> dict[str, str]:
    records = json.loads((MANIFEST_DIR / "all-records.json").read_text(encoding="utf-8"))["records"]
    result: dict[str, str] = {}
    for row in records:
        url = str(row["normalized_url"]).lower()
        sha = str(row["inspected_commit_sha"])
        if url in result and result[url] != sha:
            raise ValueError(f"conflicting inspected SHAs for {url}")
        result[url] = sha
    return result


def all_plugin_specs() -> dict[str, tuple[str, dict[str, Any]]]:
    module = activation_module()
    result: dict[str, tuple[str, dict[str, Any]]] = {}
    for url, specs in module.runtime_specs().items():
        for seed in specs:
            if seed.get("kind") != "plugin":
                continue
            plugin_id = str(seed.get("plugin_id") or "")
            if not plugin_id:
                raise ValueError(f"candidate plugin omitted plugin_id: {url}")
            if plugin_id in result:
                raise ValueError(f"duplicate candidate plugin id: {plugin_id}")
            result[plugin_id] = (url, seed)
    expected = EXPECTED_ENABLED_PLUGINS | EXPECTED_DISABLED_CODEX_PLUGINS | EXPECTED_OPENCODE_PLUGINS
    if len(result) != EXPECTED_PLUGIN_ARTIFACT_COUNT or frozenset(result) != expected:
        raise ValueError(f"plugin set drifted: expected {sorted(expected)}, found {sorted(result)}")
    return result


def enabled_plugin_specs(
    specs: dict[str, tuple[str, dict[str, Any]]] | None = None,
) -> dict[str, tuple[str, dict[str, Any]]]:
    source = all_plugin_specs() if specs is None else specs
    result = {plugin_id: (url, seed) for plugin_id, (url, seed) in source.items() if seed.get("plugin_enabled") is True}
    if frozenset(result) != EXPECTED_ENABLED_PLUGINS:
        raise ValueError(
            f"enabled plugin set drifted: expected {sorted(EXPECTED_ENABLED_PLUGINS)}, found {sorted(result)}"
        )
    return result


def verified_provenance_lock(
    specs: dict[str, tuple[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    entries = load_plugin_provenance_lock(PROVENANCE_LOCK)
    if set(entries) != set(EXPECTED_ENABLED_PLUGINS):
        raise ValueError(
            "candidate plugin provenance lock must exactly cover enabled plugins: "
            f"expected {sorted(EXPECTED_ENABLED_PLUGINS)}, found {sorted(entries)}"
        )
    registry_payload = json.loads(PLUGIN_REGISTRY.read_text(encoding="utf-8"))
    registry_rows = registry_payload.get("plugins")
    if not isinstance(registry_rows, list):
        raise ValueError("plugin extension registry must contain plugin rows")
    registry = {
        str(row.get("id") or ""): row for row in registry_rows if isinstance(row, dict) and str(row.get("id") or "")
    }
    shas = source_shas()
    for plugin_id, entry in entries.items():
        url, seed = specs[plugin_id]
        expected_sha = str(seed.get("source_commit_sha") or shas[url])
        expected_marketplace = plugin_id.rsplit("@", 1)[1]
        if str(entry["normalized_url"]).lower() != url.lower():
            raise ValueError(f"plugin provenance URL drifted: {plugin_id}")
        if entry["resolved_version"] != str(seed.get("version") or ""):
            raise ValueError(f"plugin provenance version drifted: {plugin_id}")
        if entry["audited_source_commit_sha"] != expected_sha:
            raise ValueError(f"plugin provenance audited commit drifted: {plugin_id}")
        if entry["marketplace"] != expected_marketplace:
            raise ValueError(f"plugin provenance marketplace drifted: {plugin_id}")
        registry_row = registry.get(str(entry["registry_id"]))
        if registry_row is None:
            raise ValueError(f"plugin provenance registry id is unknown: {plugin_id}")
        source_paths = registry_row.get("source_paths")
        if (
            registry_row.get("harness") != "codex"
            or not isinstance(source_paths, list)
            or url.lower() not in {str(value).lower() for value in source_paths}
        ):
            raise ValueError(f"plugin provenance registry source drifted: {plugin_id}")
    return entries


def execution_requirements(plugin_id: str) -> dict[str, bool]:
    probe_name = (MODEL_PLUGINS if plugin_id in MODEL_PLUGINS else SCRIPT_PLUGINS)[plugin_id]
    return {
        "model_execution": True,
        "audited_execution": probe_name in SCRIPT_PROBES,
    }


def execution_authorized(
    plugin_id: str,
    *,
    allow_model_execution: bool,
    allow_audited_execution: bool,
) -> bool:
    requirements = execution_requirements(plugin_id)
    return allow_model_execution and (allow_audited_execution or not requirements["audited_execution"])


def _configured_plugin(path: Path, package_name: str) -> bool:
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    plugins = payload.get("plugin", []) if isinstance(payload, dict) else []
    if not isinstance(plugins, list):
        return False
    return any(
        isinstance(value, str) and (value == package_name or value.startswith(f"{package_name}@")) for value in plugins
    )


def blocked_plugin_result(
    plugin_id: str,
    url: str,
    seed: dict[str, Any],
    module: Any,
    inventory: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    manager = str(seed.get("package_manager") or "")
    result: dict[str, Any] = {
        "artifact_id": module.artifact_id(url, seed),
        "plugin_id": plugin_id,
        "package_manager": manager,
        "configured_enabled": seed.get("plugin_enabled") is True,
        "status": "blocked",
        "behavior_probe_performed": False,
        "network_probe_performed": False,
        "secret_value_recorded": False,
    }
    if manager == "codex-plugin":
        state = inventory.get(plugin_id, {})
        root = plugin_root(seed)
        result.update({
            "blocker": "plugin-disabled-by-audited-policy",
            "local_install_present": root.is_dir(),
            "inventory_installed": state.get("installed") is True,
            "inventory_enabled": state.get("enabled") is True,
            "inventory_version_matches": str(state.get("version") or "") == str(seed.get("version") or ""),
        })
        return result
    if manager == "opencode-plugin":
        package_name = str(seed.get("package_name") or "")
        cache_root = Path.home() / ".cache" / "opencode" / "packages"
        result.update({
            "blocker": "opencode-plugin-not-configured-and-overlaps-repo-native-openspec",
            "repo_configured": _configured_plugin(ROOT / "opencode.json", package_name),
            "home_configured": _configured_plugin(
                Path.home() / ".config" / "opencode" / "opencode.json",
                package_name,
            ),
            "local_install_present": any(cache_root.glob(f"{package_name}@*")),
        })
        return result
    result["blocker"] = "unsupported-plugin-package-manager"
    return result


def codex_inventory(env: dict[str, str], *, fixture_cwd: Path) -> dict[str, dict[str, Any]]:
    result = run(
        [str(audited_executable("codex")), "plugin", "list", "--json"],
        cwd=fixture_cwd,
        env=env,
        timeout=60,
    )
    require(result.returncode == 0, f"codex plugin inventory failed with exit code {result.returncode}")
    payload = json.loads(result.stdout)
    return {str(item["pluginId"]): item for item in payload.get("installed", [])}


def probe_commit_narrator(root: Path, fixture: Path, env: dict[str, str]) -> ProcessResult:
    script = root / "scripts" / "narrate.py"
    diff = (
        "diff --git a/docs/guide.md b/docs/guide.md\n"
        "--- a/docs/guide.md\n+++ b/docs/guide.md\n@@ -1 +1,2 @@\n # Guide\n+New detail\n"
    )
    result = run(
        [str(PYTHON_EXECUTABLE), str(script), "--diff", "-", "--format", "json"],
        cwd=fixture,
        env=env,
        input_text=diff,
    )
    payload = json.loads(result.stdout)
    require(result.returncode == 0 and payload["type"] == "docs", "commit-narrator missed docs classification")
    require(payload["files"] == ["docs/guide.md"], "commit-narrator file extraction drifted")
    empty = run(
        [str(PYTHON_EXECUTABLE), str(script), "--diff", "-", "--format", "json"],
        cwd=fixture,
        env=env,
        input_text="",
    )
    require(empty.returncode == 0 and json.loads(empty.stdout)["files"] == [], "commit-narrator rejected empty diff")
    malformed = run(
        [str(PYTHON_EXECUTABLE), str(script), "--diff", "-", "--format", "json"],
        cwd=fixture,
        env=env,
        input_text="not a unified diff\n",
    )
    require(json.loads(malformed.stdout)["files"] == [], "commit-narrator fabricated files for malformed input")
    sentinel = fixture / "must-not-exist"
    hostile = diff.replace("docs/guide.md", "docs/$(touch must-not-exist).md")
    denied = run(
        [str(PYTHON_EXECUTABLE), str(script), "--diff", "-", "--format", "json"],
        cwd=fixture,
        env=env,
        input_text=hostile,
    )
    require(denied.returncode == 0 and not sentinel.exists(), "commit-narrator executed diff text")
    return result


def probe_env_lint(root: Path, fixture: Path, env: dict[str, str]) -> ProcessResult:
    script = root / "scripts" / "envlint.py"
    example = fixture / ".env.example"
    actual = fixture / ".env"
    example.write_text("REQ_A=\nREQ_B=\nEMPTY_OK=\n", encoding="utf-8")
    actual.write_text("REQ_A=fixture-value-one\nREQ_B=fixture-value-two\nEMPTY_OK=filled\n", encoding="utf-8")
    argv = [
        str(PYTHON_EXECUTABLE),
        str(script),
        "--example",
        str(example),
        "--env",
        str(actual),
        "--format",
        "json",
    ]
    result = run(argv, cwd=fixture, env=env)
    payload = json.loads(result.stdout)
    require(result.returncode == 0 and payload["pairs"][0]["missing_in_env"] == [], "env-lint rejected a complete env")
    actual.write_text("REQ_A=fixture-value-one\nEMPTY_OK=\nEXTRA_ONLY=fixture-private-value\n", encoding="utf-8")
    failure = run(argv, cwd=fixture, env=env)
    failure_payload = json.loads(failure.stdout)
    require(
        failure.returncode == 1 and failure_payload["pairs"][0]["missing_in_env"] == ["REQ_B"],
        "env-lint missed a required key",
    )
    require(
        failure_payload["pairs"][0]["extra_in_env"] == ["EXTRA_ONLY"],
        "env-lint missed an extra key",
    )
    require(
        failure_payload["pairs"][0]["empty_values"] == ["EMPTY_OK"],
        "env-lint missed an empty key",
    )
    combined = result.stdout + failure.stdout + result.stderr + failure.stderr
    require("fixture-value" not in combined and "fixture-private-value" not in combined, "env-lint disclosed values")
    denied = run([str(PYTHON_EXECUTABLE), str(script), "--example", str(example)], cwd=fixture, env=env)
    require(denied.returncode != 0, "env-lint accepted an incomplete argument pair")
    return result


def probe_secret_guard(root: Path, fixture: Path, env: dict[str, str]) -> ProcessResult:
    script = root / "scripts" / "guard.py"
    clean = fixture / "clean.txt"
    clean.write_text("ordinary fixture text\n", encoding="utf-8")
    result = run(
        [str(PYTHON_EXECUTABLE), str(script), "--files", str(clean), "--format", "json"],
        cwd=fixture,
        env=env,
    )
    require(result.returncode == 0 and json.loads(result.stdout) == [], "secret-guard rejected clean text")
    synthetic = "ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    flagged = fixture / "flagged.txt"
    flagged.write_text(f"token={synthetic}\n", encoding="utf-8")
    failure = run(
        [str(PYTHON_EXECUTABLE), str(script), "--files", str(flagged), "--format", "json"],
        cwd=fixture,
        env=env,
    )
    findings = json.loads(failure.stdout)
    require(failure.returncode == 1 and findings[0]["pattern"] == "GitHub PAT", "secret-guard missed the synthetic PAT")
    require(
        synthetic not in failure.stdout and synthetic not in failure.stderr, "secret-guard disclosed the synthetic PAT"
    )
    allowlist = fixture / "allowlist.txt"
    allowlist.write_text("^ghp_A+$\n", encoding="utf-8")
    denied = run(
        [
            str(PYTHON_EXECUTABLE),
            str(script),
            "--files",
            str(flagged),
            "--format",
            "json",
            "--allowlist",
            str(allowlist),
        ],
        cwd=fixture,
        env=env,
    )
    require(denied.returncode == 0 and json.loads(denied.stdout) == [], "secret-guard allowlist denial failed")
    return result


def probe_unslop(root: Path, fixture: Path, env: dict[str, str]) -> ProcessResult:
    skill_root = root / "skills" / "unslop-file"
    input_text = (
        "Certainly! It's important to note that this robust tool leverages caching. Additionally, it works.\n\n"
        "```text\nCertainly! robust leverages\n```\n"
    )
    argv = [
        str(PYTHON_EXECUTABLE),
        "-m",
        "scripts",
        "--stdin",
        "--deterministic",
        "--mode",
        "balanced",
        "--no-structural",
        "--no-soul",
        "--quiet",
    ]
    result = run(argv, cwd=skill_root, env=env, input_text=input_text)
    require(result.returncode == 0 and "Certainly! robust leverages" in result.stdout, "unslop changed fenced content")
    require("Certainly! It's important to note" not in result.stdout, "unslop did not transform fixture prose")
    missing = run(
        [str(PYTHON_EXECUTABLE), "-m", "scripts", str(fixture / "missing.md"), "--deterministic"],
        cwd=skill_root,
        env=env,
    )
    require(
        "Error: file not found:" in missing.stdout + missing.stderr,
        "unslop did not emit a bounded missing-file diagnostic",
    )
    sensitive = fixture / ".env"
    sensitive.write_text("PLACEHOLDER=value\n", encoding="utf-8")
    before = sensitive.read_bytes()
    denied = run(
        [str(PYTHON_EXECUTABLE), "-m", "scripts", str(sensitive), "--deterministic", "--dry-run"],
        cwd=skill_root,
        env=env,
    )
    require(
        any(marker in (denied.stdout + denied.stderr).lower() for marker in ("sensitive", "skip", "refus"))
        and sensitive.read_bytes() == before,
        "unslop did not explicitly refuse a sensitive fixture",
    )
    return result


def _git(
    fixture: Path, env: dict[str, str], *args: str, author: str | None = None, date: str | None = None
) -> ProcessResult:
    command_env = dict(env)
    if author:
        command_env.update({
            "GIT_AUTHOR_NAME": author,
            "GIT_AUTHOR_EMAIL": f"{author.lower()}@example.invalid",
            "GIT_COMMITTER_NAME": author,
            "GIT_COMMITTER_EMAIL": f"{author.lower()}@example.invalid",
        })
    if date:
        command_env.update({"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})
    return run([str(audited_executable("git")), *args], cwd=fixture, env=command_env)


def probe_codebase_recon(root: Path, fixture: Path, env: dict[str, str]) -> ProcessResult:
    skill = root / "skills" / "codebase-recon" / "SKILL.md"
    skill_text = skill.read_text(encoding="utf-8")
    for documented in ("git shortlog -sn --no-merges", 'git log -i -E --grep="fix|bug|broken"'):
        require(documented in skill_text, f"codebase-recon command drifted: {documented}")

    initialized = _git(fixture, env, "init", "-q")
    require(
        initialized.returncode == 0,
        f"codebase-recon fixture git init failed: {(initialized.stderr or initialized.stdout)[-1200:]}",
    )
    (fixture / "hot.py").write_text("VALUE = 0\n", encoding="utf-8")
    require(_git(fixture, env, "add", "hot.py").returncode == 0, "codebase-recon fixture add failed")
    require(
        _git(fixture, env, "commit", "-q", "-m", "initial", author="Bob", date="2024-01-02T12:00:00Z").returncode == 0,
        "codebase-recon fixture initial commit failed",
    )
    for index, author in enumerate(("Carol", "Dave"), start=1):
        path = fixture / f"cold_{index}.py"
        path.write_text(f"VALUE = {index}\n", encoding="utf-8")
        require(_git(fixture, env, "add", path.name).returncode == 0, "codebase-recon fixture add failed")
        require(
            _git(
                fixture,
                env,
                "commit",
                "-q",
                "-m",
                f"add cold {index}",
                author=author,
                date=f"2024-0{index + 2}-02T12:00:00Z",
            ).returncode
            == 0,
            "codebase-recon fixture contributor commit failed",
        )
    for index in range(1, 5):
        (fixture / "hot.py").write_text(f"VALUE = {index}\n", encoding="utf-8")
        require(_git(fixture, env, "add", "hot.py").returncode == 0, "codebase-recon fixture add failed")
        require(
            _git(
                fixture,
                env,
                "commit",
                "-q",
                "-m",
                f"fix hot path {index}",
                author="Alice",
                date=f"2026-07-{index + 1:02d}T12:00:00Z",
            ).returncode
            == 0,
            "codebase-recon fixture hotspot commit failed",
        )

    before = file_digest([fixture])
    hotspots = _git(fixture, env, "log", "--format=format:", "--name-only")
    bug_magnets = _git(fixture, env, "log", "-i", "-E", "--grep=fix|bug|broken", "--name-only", "--format=")
    contributors = _git(fixture, env, "shortlog", "-sn", "--no-merges", "HEAD")
    active = _git(fixture, env, "shortlog", "-sn", "--no-merges", "--since=3 months ago", "HEAD")
    owner = _git(fixture, env, "shortlog", "-sn", "HEAD", "--", "hot.py")
    for result in (hotspots, bug_magnets, contributors, active, owner):
        require(result.returncode == 0, f"codebase-recon git command failed: {result.stderr}")
    hotspot_counts = {
        name: hotspots.stdout.splitlines().count(name) for name in set(hotspots.stdout.splitlines()) if name
    }
    require(
        max(hotspot_counts, key=lambda name: hotspot_counts[name]) == "hot.py",
        "codebase-recon missed the expected hotspot",
    )
    require(bug_magnets.stdout.splitlines().count("hot.py") == 4, "codebase-recon missed the expected bug magnet")
    require("Alice" in owner.stdout, "codebase-recon missed the hotspot owner")
    require(
        len(active.stdout.splitlines()) < 0.3 * len(contributors.stdout.splitlines()),
        "codebase-recon missed bus-factor risk",
    )
    require(file_digest([fixture]) == before, "codebase-recon analysis mutated the fixture")
    non_repo = fixture.parent / f"{fixture.name}-not-a-repo"
    non_repo.mkdir()
    denied = run([str(audited_executable("git")), "rev-list", "--count", "HEAD"], cwd=non_repo, env=env)
    require(denied.returncode != 0, "codebase-recon accepted a non-repository fixture")
    return hotspots


def _owned_fixture_snapshot(root: Path) -> dict[str, TreeEntry]:
    return _tree_manifest(root)


def _benign_budget_error(item: dict[str, Any]) -> bool:
    message = str(item.get("message") or "").casefold()
    return "skills context budget" in message and "skill descriptions were shortened" in message


def _workflow_events(result: ProcessResult) -> tuple[str, str]:
    require(result.returncode == 0, f"Roadmapsmith Codex turn failed: {result.stderr[-1200:]}")
    thread_id = ""
    messages: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        require(isinstance(event, dict), "Roadmapsmith Codex event must be an object")
        event_type = str(event.get("type") or "")
        require(event_type not in {"error", "turn.failed"}, f"Roadmapsmith Codex emitted {event_type}")
        if event_type == "thread.started":
            thread_id = str(event.get("thread_id") or "")
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "")
        if item_type == "error" and _benign_budget_error(item):
            continue
        require(item_type in {"agent_message", "reasoning"}, f"Roadmapsmith used a forbidden Codex item: {item_type}")
        if item_type == "agent_message":
            messages.extend(
                _string_values(item.get("text"))
                + _string_values(item.get("content"))
                + _string_values(item.get("message"))
            )
    require(bool(messages), "Roadmapsmith Codex turn emitted no agent messages")
    return thread_id, "\n".join(messages)


def _roadmap_turn(
    fixture: Path,
    env: dict[str, str],
    prompt: str,
    *,
    session_id: str = "",
) -> tuple[ProcessResult, str, str]:
    auth_fingerprint = prepare_model_auth(env)
    launch_env = model_sandbox_env(env, fixture)
    sandbox = "read-only"
    common = [
        "--json",
        "--skip-git-repo-check",
        "--ignore-rules",
        "--strict-config",
        "--enable",
        "plugins",
        "-c",
        'web_search="disabled"',
        "-c",
        'approval_policy="never"',
        "-c",
        f'sandbox_mode="{sandbox}"',
        "-c",
        'shell_environment_policy.inherit="none"',
        "--disable",
        "shell_tool",
        "--disable",
        "unified_exec",
        "--disable",
        "browser_use",
        "--disable",
        "computer_use",
        "--disable",
        "apps",
        "--disable",
        "image_generation",
        "--disable",
        "multi_agent",
        "--disable",
        "code_mode_host",
    ]
    if session_id:
        argv = [str(audited_executable("codex")), "exec", "resume", *common, session_id, prompt]
    else:
        argv = [str(audited_executable("codex")), "exec", *common, "-s", sandbox, "-C", str(fixture), prompt]
    result = run(argv, cwd=fixture, env=launch_env, timeout=600)
    require(_auth_fingerprint() == auth_fingerprint, "host Codex auth changed during Roadmapsmith model launch")
    combined = result.stdout + result.stderr
    require(
        not any(secret in combined for secret in auth_secret_strings()),
        "Roadmapsmith Codex output contained authentication material",
    )
    started_id, messages = _workflow_events(result)
    return result, started_id, messages


def _trusted_fixture_payload(fixture: Path) -> str:
    """Serialize an owned text fixture without following links or reading outside it."""

    files: dict[str, str] = {}
    for path in sorted(fixture.rglob("*"), key=lambda value: str(value.relative_to(fixture))):
        relative = str(path.relative_to(fixture))
        metadata = path.lstat()
        require(not stat.S_ISLNK(metadata.st_mode), f"trusted fixture contains a symlink: {relative}")
        if stat.S_ISDIR(metadata.st_mode):
            continue
        require(stat.S_ISREG(metadata.st_mode), f"trusted fixture contains a special file: {relative}")
        files[relative] = path.read_text(encoding="utf-8")
    return json.dumps({"files": files}, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _validated_roadmap_edit(proposal: str, *, old: str, new: str) -> dict[str, str]:
    markers = [
        line.removeprefix(ROADMAP_EDIT_MARKER) for line in proposal.splitlines() if line.startswith(ROADMAP_EDIT_MARKER)
    ]
    require(len(markers) == 1, "Roadmapsmith proposal must contain exactly one structured edit marker")
    try:
        edit = json.loads(markers[0])
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Roadmapsmith structured edit marker is invalid JSON: {error}") from None
    require(isinstance(edit, dict), "Roadmapsmith structured edit marker must be an object")
    require(set(edit) == {"new", "old", "path"}, "Roadmapsmith structured edit marker has unexpected fields")
    expected = {"path": "ROADMAP.md", "old": old, "new": new}
    require(edit == expected, f"Roadmapsmith proposed an unexpected edit: {edit!r}")
    return {key: str(value) for key, value in edit.items()}


def _trusted_replace_regular_file(path: Path, *, expected: str, replacement: str) -> None:
    """Apply one harness-approved edit without allowing symlink substitution."""

    before = path.lstat()
    require(
        stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode),
        f"trusted write target is not regular: {path}",
    )
    require(path.read_text(encoding="utf-8") == expected, "trusted write target changed after proposal validation")
    flags = os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        require(
            stat.S_ISREG(opened.st_mode) and opened.st_dev == before.st_dev and opened.st_ino == before.st_ino,
            "trusted write target identity changed before apply",
        )
        encoded = replacement.encode("utf-8")
        os.ftruncate(descriptor, 0)
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            require(written > 0, "trusted roadmap write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def probe_roadmapsmith(root: Path, fixture: Path, env: dict[str, str]) -> ProcessResult:
    del root
    ready_line = "- [ ] Mark ready() implementation complete (src/ready.js)"
    roadmap = f"# Probe Roadmap\n\n## Phase 0\n\n{ready_line}\n- [ ] Add a missing widget with no implementation\n"
    (fixture / "src").mkdir()
    (fixture / "README.md").write_text("# Roadmapsmith owned fixture\n", encoding="utf-8")
    (fixture / "package.json").write_text(
        json.dumps({"name": "roadmapsmith-owned-fixture", "version": "1.0.0"}) + "\n",
        encoding="utf-8",
    )
    (fixture / "src" / "ready.js").write_text("export function ready() { return true; }\n", encoding="utf-8")
    roadmap_path = fixture / "ROADMAP.md"
    roadmap_path.write_text(roadmap, encoding="utf-8")
    before = _owned_fixture_snapshot(fixture)
    first, session_id, question = _roadmap_turn(
        fixture,
        env,
        "Invoke $roadmapsmith:roadmap-update for this owned isolated fixture. Follow the skill exactly. "
        "Begin by asking the required scan-mode question, then stop. All tools are disabled; do not attempt a tool "
        "call.",
    )
    require(bool(session_id), "Roadmapsmith did not create a resumable Codex session")
    require("scan" in question.casefold() or "modo" in question.casefold(), "Roadmapsmith did not ask scan mode")
    require(_owned_fixture_snapshot(fixture) == before, "Roadmapsmith mutated the fixture before scan-mode choice")

    expected_line = ready_line.replace("[ ]", "[x]", 1)
    expected_roadmap = roadmap.replace(ready_line, expected_line)
    snapshot = _trusted_fixture_payload(fixture)
    proposal, _, proposal_text = _roadmap_turn(
        fixture,
        env,
        "A. full-scan. All tools are disabled. Treat this trusted harness snapshot as the complete immutable fixture: "
        f"{snapshot}. The trusted git summary is: ready() was implemented in the latest commit; the missing widget "
        "has no implementation. Present the complete proposed diff, then stop and ask for approval. Do not attempt "
        "any tool call or modify any file. Include exactly one machine-readable line with this prefix and JSON shape: "
        f'{ROADMAP_EDIT_MARKER}{{"path":"ROADMAP.md","old":{json.dumps(ready_line)},'
        f'"new":{json.dumps(expected_line)}}}',
        session_id=session_id,
    )
    require(_owned_fixture_snapshot(fixture) == before, "Roadmapsmith mutated the fixture before approval")
    require(
        "[x]" in proposal_text and "diff" in proposal_text.casefold(),
        f"Roadmapsmith omitted the proposed diff: {proposal_text[-2000:]}",
    )
    require(
        any(marker in proposal_text.casefold() for marker in ("aplico", "apply", "approval", "ok")),
        "Roadmapsmith did not request approval",
    )
    _validated_roadmap_edit(proposal_text, old=ready_line, new=expected_line)
    require(_owned_fixture_snapshot(fixture) == before, "Roadmapsmith fixture changed during proposal validation")
    _trusted_replace_regular_file(roadmap_path, expected=roadmap, replacement=expected_roadmap)

    approved, _, report = _roadmap_turn(
        fixture,
        env,
        "ok. The trusted harness, not the model, applied the exact approved checkbox flip. All tools remain disabled. "
        f"The updated trusted snapshot is {_trusted_fixture_payload(fixture)}. Produce the required roadmap-update "
        "report and do not attempt any tool call or file change.",
        session_id=session_id,
    )
    after = _owned_fixture_snapshot(fixture)
    require(after.keys() == before.keys(), "Roadmapsmith added or removed fixture files")
    for path, content in before.items():
        if path != "ROADMAP.md":
            require(after[path] == content, f"Roadmapsmith changed an unapproved file: {path}")
    actual_roadmap = roadmap_path.read_text(encoding="utf-8")
    require(
        actual_roadmap == expected_roadmap,
        "Roadmapsmith applied an unexpected diff: "
        f"expected={expected_roadmap!r} actual={actual_roadmap!r} report={report[-2000:]!r}",
    )
    require(
        "roadmap-update report" in report.casefold() and "mode:" in report.casefold(),
        "Roadmapsmith report drifted",
    )

    denied_root = fixture.parent / f"{fixture.name}-missing-roadmap"
    denied_root.mkdir()
    (denied_root / "README.md").write_text("# Missing roadmap fixture\n", encoding="utf-8")
    denied_before = _owned_fixture_snapshot(denied_root)
    denied_first, denied_session, denied_question = _roadmap_turn(
        denied_root,
        env,
        "Invoke $roadmapsmith:roadmap-update for this owned isolated fixture. Ask the required scan-mode question "
        "and stop. All tools are disabled; do not attempt a tool call.",
    )
    require(bool(denied_session), "Roadmapsmith denial fixture did not create a resumable session")
    require(
        "scan" in denied_question.casefold() or "modo" in denied_question.casefold(),
        "Roadmapsmith denial missed scan mode",
    )
    denied, _, denial_text = _roadmap_turn(
        denied_root,
        env,
        "A. full-scan. This is the requested scan-mode answer. All tools are disabled. Treat this trusted harness "
        f"snapshot as the complete immutable fixture: {_trusted_fixture_payload(denied_root)}. ROADMAP.md is absent. "
        "Follow the skill's missing-roadmap denial and stop without attempting any tool call or file change.",
        session_id=denied_session,
    )
    normalized_denial = denial_text.casefold()
    require(
        "roadmap-init" in normalized_denial
        or "no encuentro roadmap" in normalized_denial
        or (
            "roadmap.md" in normalized_denial
            and any(
                marker in normalized_denial
                for marker in ("missing", "not found", "does not exist", "absent", "cannot", "can't")
            )
        ),
        f"Roadmapsmith did not deny a missing-roadmap fixture: {denial_text[-2000:]}",
    )
    require(_owned_fixture_snapshot(denied_root) == denied_before, "Roadmapsmith mutated the denial fixture")
    return ProcessResult(
        approved.argv,
        0,
        "\0".join((first.stdout, proposal.stdout, approved.stdout, denied_first.stdout, denied.stdout)),
        "\0".join((first.stderr, proposal.stderr, approved.stderr, denied_first.stderr, denied.stderr)),
        approved.pid,
        approved.launch_id,
        approved.started_at_ns,
    )


SCRIPT_PROBES: dict[str, Callable[[Path, Path, dict[str, str]], ProcessResult]] = {
    "commit-narrator": probe_commit_narrator,
    "env-lint": probe_env_lint,
    "secret-guard": probe_secret_guard,
    "unslop": probe_unslop,
    "codebase-recon": probe_codebase_recon,
    "roadmapsmith": probe_roadmapsmith,
}


DISCOVERY_SPECS = {
    "commit-narrator@candidate-corpus-local": (
        "$commit-narrator:commit-narrator",
        "Return the exact Role sentence from the loaded skill.",
        "Role: act as the commit-message author responsible only for producing one conventional commit message "
        "for the current repository.",
    ),
    "env-lint@candidate-corpus-local": (
        "$env-lint:env-lint",
        "Return the exact Role sentence from the loaded skill.",
        "Role: act as an env-var auditor. Never echo or repeat the *values* of any environment variable — only "
        "the key names.",
    ),
    "secret-guard@candidate-corpus-local": (
        "$secret-guard:secret-guard",
        "Return the exact Role sentence from the loaded skill.",
        "Role: act as a pre-merge security gate. Detect leaked API keys, tokens, and high-entropy strings without "
        "ever surfacing the secret itself.",
    ),
    "unslop@awesome-codex-plugins": (
        "$unslop:unslop-file",
        "Return the exact first sentence under the Purpose heading from the loaded skill.",
        "Rewrite natural-language memory files (CLAUDE.md, AGENTS.md, todos, preferences, docs) so they sound "
        "human-written: no sycophancy, no stock vocab, no five-paragraph essay shape, no tricolon padding.",
    ),
    "universal-design-principles@awesome-codex-plugins": (
        "$universal-design-principles:errors",
        "Return the exact first sentence after the Errors heading from the loaded skill.",
        'Most "accidents" attributed to human error are actually design errors.',
    ),
    "brooks-lint@awesome-codex-plugins": (
        "$brooks-lint:brooks-review",
        "Return the exact H1 line, including its leading Markdown marker, from the loaded skill.",
        "# Brooks-Lint — PR Review",
    ),
    "roadmapsmith@awesome-codex-plugins": (
        "$roadmapsmith:roadmap-update",
        "Return the exact invariant sentence that forbids modifying ROADMAP.md before approval.",
        "NUNCA modificar ROADMAP.md sin mostrar el diff completo y esperar OK del user.",
    ),
    "codebase-recon@awesome-codex-plugins": (
        "$codebase-recon:codebase-recon",
        "Return the exact first sentence after the Codebase Recon heading from the loaded skill.",
        "Analyze git history to understand a codebase before reading any code.",
    ),
}


def _string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for child in value.values() for item in _string_values(child)]
    if isinstance(value, list):
        return [item for child in value for item in _string_values(child)]
    return []


def _json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"{label} is unreadable or invalid: {path}: {error}") from None
    require(isinstance(payload, dict), f"{label} must be an object: {path}")
    return payload


def validate_plugin_surfaces(plugin_id: str, root: Path) -> None:
    """Reject implicit executable surfaces before Codex parses or loads a plugin."""

    root = root.resolve(strict=True)
    expected_name, _marketplace = plugin_id.rsplit("@", 1)
    manifest_path = root / ".codex-plugin" / "plugin.json"
    require(manifest_path.is_file(), f"plugin manifest missing: {plugin_id}")
    root_manifest = _json_object(manifest_path, label="plugin manifest")
    require(root_manifest.get("name") == expected_name, f"plugin manifest name drifted: {plugin_id}")

    allowed_executables = PLUGIN_EXECUTABLE_ALLOWLIST.get(plugin_id, frozenset())
    discovered_executables: set[str] = set()
    for path in sorted(root.rglob("*"), key=lambda value: str(value.relative_to(root))):
        relative = str(path.relative_to(root))
        metadata = path.lstat()
        require(not stat.S_ISLNK(metadata.st_mode), f"plugin surface contains a symlink: {plugin_id}: {relative}")
        require(
            stat.S_ISDIR(metadata.st_mode) or stat.S_ISREG(metadata.st_mode),
            f"plugin surface contains a special file: {plugin_id}: {relative}",
        )
        if not stat.S_ISREG(metadata.st_mode):
            continue
        if metadata.st_mode & 0o111:
            discovered_executables.add(relative)
        lowered_parts = {part.casefold() for part in path.relative_to(root).parts}
        require(
            not lowered_parts.intersection({"commands", "hooks"}),
            f"plugin exposes a command or hook directory: {plugin_id}: {relative}",
        )
        require(
            path.name.casefold() not in {".mcp.json", "mcp.json", "fastmcp.json"},
            f"plugin exposes an MCP startup surface: {plugin_id}: {relative}",
        )
        require(
            path.suffix.casefold() not in {".bash", ".command", ".sh"},
            f"plugin exposes an unaudited shell executable: {plugin_id}: {relative}",
        )

    require(
        discovered_executables == set(allowed_executables),
        f"plugin executable surface drifted: {plugin_id}: expected={sorted(allowed_executables)!r} "
        f"actual={sorted(discovered_executables)!r}",
    )

    for plugin_manifest in sorted(root.rglob("plugin.json"), key=str):
        if plugin_manifest.parent.name not in {".claude-plugin", ".codex-plugin", ".cursor-plugin"}:
            continue
        payload = _json_object(plugin_manifest, label="plugin manifest")
        forbidden = PLUGIN_MANIFEST_EXECUTION_KEYS.intersection(payload)
        require(
            not forbidden,
            f"plugin manifest exposes executable startup keys: {plugin_id}: "
            f"{plugin_manifest.relative_to(root)}: {sorted(forbidden)}",
        )

    for package_path in sorted(root.rglob("package.json"), key=str):
        payload = _json_object(package_path, label="package manifest")
        scripts = payload.get("scripts", {})
        require(isinstance(scripts, dict), f"package scripts must be an object: {package_path}")
        lifecycle = PACKAGE_LIFECYCLE_KEYS.intersection(scripts)
        require(
            not lifecycle,
            f"plugin package exposes install/start lifecycle scripts: {plugin_id}: "
            f"{package_path.relative_to(root)}: {sorted(lifecycle)}",
        )
        bin_value = payload.get("bin")
        bin_targets: list[str] = []
        if isinstance(bin_value, str):
            bin_targets.append(bin_value)
        elif isinstance(bin_value, dict):
            for target in bin_value.values():
                require(isinstance(target, str), f"plugin package bin target must be a string: {package_path}")
                bin_targets.append(target)
        for target in bin_targets:
            candidate = (package_path.parent / target).resolve(strict=False)
            require(
                not candidate.is_file(),
                f"plugin package exposes an active bin entry: {plugin_id}: {package_path.relative_to(root)}: {target}",
            )

    for skill_path in sorted(root.rglob("SKILL.md"), key=str):
        source = skill_path.read_text(encoding="utf-8")
        if not source.startswith("---\n"):
            continue
        frontmatter = yaml.safe_load(source.split("---", 2)[1])
        require(isinstance(frontmatter, dict), f"plugin skill frontmatter is invalid: {skill_path}")
        require("hooks" not in frontmatter, f"plugin skill exposes hooks: {plugin_id}: {skill_path.relative_to(root)}")
        allowed_tools = str(frontmatter.get("allowed-tools") or "").strip()
        if allowed_tools:
            require(
                plugin_id in SCRIPT_PLUGINS and allowed_tools == "Bash",
                f"plugin skill exposes unaudited allowed-tools: {plugin_id}: "
                f"{skill_path.relative_to(root)}: {allowed_tools!r}",
            )


def marketplace_plugin_source(
    plugin_id: str,
    marketplace_root: Path,
    provenance: dict[str, Any] | None = None,
) -> Path:
    if provenance is None:
        raise RuntimeError(f"marketplace provenance is required: {plugin_id}")
    require(provenance["plugin_id"] == plugin_id, f"marketplace provenance plugin id drifted: {plugin_id}")
    return resolve_locked_marketplace_source(marketplace_root, provenance)


def _auth_fingerprint() -> tuple[int, int, str]:
    metadata = HOST_CODEX_AUTH.lstat()
    require(stat.S_ISREG(metadata.st_mode), "Codex ChatGPT auth must be a regular file")
    return metadata.st_dev, metadata.st_ino, hashlib.sha256(HOST_CODEX_AUTH.read_bytes()).hexdigest()


def prepare_model_auth(env: dict[str, str]) -> tuple[int, int, str]:
    fingerprint = _auth_fingerprint()
    destination = Path(env["CODEX_HOME"]) / "auth.json"
    if destination.exists() or destination.is_symlink():
        require(destination.is_symlink(), "isolated Codex auth destination is not a symlink")
        require(
            destination.resolve(strict=True) == HOST_CODEX_AUTH.resolve(strict=True),
            "isolated Codex auth link drifted",
        )
    else:
        destination.symlink_to(HOST_CODEX_AUTH)
    require(_auth_fingerprint() == fingerprint, "host Codex auth changed while preparing model launch")
    return fingerprint


def model_sandbox_env(env: dict[str, str], fixture: Path) -> dict[str, str]:
    control_root = Path(env["CODEX_HOME"]).parent
    model_env = dict(env)
    model_env["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"
    return sandbox_environment(
        model_env,
        read_roots=(
            *executable_runtime_roots("codex", "node"),
            *TLS_TRUST_READ_ROOTS,
            control_root,
            fixture,
            HOST_CODEX_AUTH,
        ),
        write_roots=(control_root,),
        network_policy="external",
    )


def auth_secret_strings() -> tuple[str, ...]:
    require(HOST_CODEX_AUTH.is_file(), "Codex ChatGPT authentication is unavailable for isolated discovery")
    payload = json.loads(HOST_CODEX_AUTH.read_text(encoding="utf-8"))
    return tuple(sorted({value for value in _string_values(payload) if len(value) >= 8}, key=len, reverse=True))


def install_isolated_plugin(
    plugin_id: str,
    root: Path,
    provenance: dict[str, Any],
) -> tuple[dict[str, str], Path, int]:
    env = isolated_env(root)
    marketplace = plugin_id.rsplit("@", 1)[1]
    marketplace_root = MARKETPLACE_ROOTS[marketplace]
    require(marketplace_root.is_dir(), f"marketplace snapshot missing: {marketplace_root}")
    source_root = marketplace_plugin_source(plugin_id, marketplace_root, provenance)
    verify_marketplace_checkout(source_root, provenance)
    verify_plugin_content(source_root, provenance, label=f"marketplace source for {plugin_id}")
    validate_plugin_surfaces(plugin_id, source_root)
    operation_cwd = root / "plugin-operation-fixture"
    operation_cwd.mkdir(mode=0o700)
    env = sandbox_environment(
        env,
        read_roots=(
            *executable_runtime_roots("codex", "node"),
            marketplace_root,
            source_root,
            root,
        ),
        write_roots=(root,),
        network_policy="none",
    )
    codex = str(audited_executable("codex"))
    added_marketplace = run(
        [codex, "plugin", "marketplace", "add", str(marketplace_root), "--json"],
        cwd=operation_cwd,
        env=env,
        timeout=120,
    )
    require(
        added_marketplace.returncode == 0,
        f"isolated marketplace add failed for {plugin_id}: {added_marketplace.stderr[-1200:]}",
    )
    added_plugin = run([codex, "plugin", "add", plugin_id, "--json"], cwd=operation_cwd, env=env, timeout=120)
    require(
        added_plugin.returncode == 0,
        f"isolated plugin add failed for {plugin_id}: {added_plugin.stderr[-1200:]}",
    )
    installed_root = Path(str(json.loads(added_plugin.stdout)["installedPath"]))
    require(
        installed_root.resolve(strict=True).is_relative_to(Path(env["CODEX_HOME"]).resolve(strict=True)),
        f"isolated plugin root escaped CODEX_HOME: {plugin_id}",
    )
    verify_plugin_content(installed_root, provenance, label=f"isolated install for {plugin_id}")
    validate_plugin_surfaces(plugin_id, installed_root)
    inventory_result = run([codex, "plugin", "list", "--json"], cwd=operation_cwd, env=env, timeout=120)
    require(inventory_result.returncode == 0, f"isolated plugin inventory failed for {plugin_id}")
    installed = json.loads(inventory_result.stdout).get("installed", [])
    require(
        len(installed) == 1 and installed[0].get("pluginId") == plugin_id and installed[0].get("enabled") is True,
        f"isolated Codex home did not contain exactly the enabled target plugin: {plugin_id}",
    )
    require(installed_root.is_dir(), f"isolated plugin root missing: {installed_root}")
    return env, installed_root, inventory_result.pid


def _model_schema(plugin_id: str) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "plugin": {"type": "string"},
        "skill_evidence": {"type": "string"},
        "capability": {"type": "string"},
    }
    required = ["plugin", "skill_evidence", "capability"]
    if plugin_id == UNIVERSAL_DESIGN_PLUGIN_ID:
        properties["skill_nonces"] = {
            "type": "object",
            "additionalProperties": False,
            "required": list(UNIVERSAL_DESIGN_SKILL_SELECTORS),
            "properties": {
                selector: {"type": "string", "minLength": 1} for selector in UNIVERSAL_DESIGN_SKILL_SELECTORS
            },
        }
        required.append("skill_nonces")
        for field, source_selector in UNIVERSAL_DESIGN_FINDING_SOURCES.items():
            properties[field] = {
                "type": "array",
                "minItems": 1,
                "maxItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["issue", "remediation", "principle_or_source_skill", "fixture_signal"],
                    "properties": {
                        "issue": {"type": "string", "minLength": 1},
                        "remediation": {"type": "string", "minLength": 1},
                        "principle_or_source_skill": {"type": "string", "enum": [source_selector]},
                        "fixture_signal": {
                            "type": "string",
                            "enum": [UNIVERSAL_DESIGN_FIXTURE_SIGNALS[field]],
                        },
                    },
                },
            }
            required.append(field)
    else:
        properties["runtime_nonce"] = {"type": "string", "minLength": 1}
        required.append("runtime_nonce")
    if plugin_id == "brooks-lint@awesome-codex-plugins":
        properties.update({
            "discovered_skills": {"type": "array", "minItems": 6, "items": {"type": "string"}},
            "severity": {"type": "string", "enum": ["critical", "warning", "suggestion"]},
            "symptom": {"type": "string"},
            "source": {"type": "string"},
            "consequence": {"type": "string"},
            "remedy": {"type": "string"},
            "citation": {"type": "string"},
        })
        required.extend(["discovered_skills", "severity", "symptom", "source", "consequence", "remedy", "citation"])
    return {"type": "object", "additionalProperties": False, "required": required, "properties": properties}


def _model_prompt(plugin_id: str) -> str:
    selector, evidence_request, _expected = DISCOVERY_SPECS[plugin_id]
    if plugin_id == UNIVERSAL_DESIGN_PLUGIN_ID:
        selectors = ", ".join(UNIVERSAL_DESIGN_SKILL_SELECTORS)
        finding_contract = "; ".join(
            f"{field} -> principle_or_source_skill {UNIVERSAL_DESIGN_FINDING_SOURCES[field]!r} and "
            f"fixture_signal {UNIVERSAL_DESIGN_FIXTURE_SIGNALS[field]!r}"
            for field in UNIVERSAL_DESIGN_FINDING_SOURCES
        )
        return (
            f"Invoke each of these skills: {selectors}. All shell, browser, app, MCP, network, and write tools are "
            f"disabled. {evidence_request} Return JSON only. Set plugin to {plugin_id!r}. Return skill_nonces as "
            "an exact object mapping every listed selector to the distinct opaque text under that skill's Runtime "
            "Probe Nonce heading. Review this inline UI: "
            "<main><button aria-label=''></button><p style='color:red'>Failed</p>"
            "<nav><button>One</button><button>Two</button><button>Three</button><button>Four</button>"
            "<button>Five</button><button>Six</button><button>Seven</button><button>Eight</button>"
            "<button>Nine</button><button>Ten</button><button>Eleven</button><button>Twelve</button></nav>"
            "<div onclick='submit()'>Submit</div></main>. Return exactly one fixture-grounded object in each of "
            "accessibility, perception, cognition, and interaction. Every object must contain a nonblank issue, "
            "nonblank remediation, principle_or_source_skill, and fixture_signal. Use this exact category mapping: "
            f"{finding_contract}. Make the four issue/remediation pairs distinct. Put the exact requested sentence "
            "only in skill_evidence; put the review findings only in those structured arrays."
        )
    base = (
        f"Invoke {selector}. All shell, browser, app, MCP, network, and write tools are disabled. "
        f"{evidence_request} Return JSON only. Set plugin to {plugin_id!r}. "
        "Return the exact opaque text under the Runtime Probe Nonce heading in runtime_nonce. "
    )
    if plugin_id == "brooks-lint@awesome-codex-plugins":
        return base + (
            "Perform PR Review mode on this inline code without auto-fixing: "
            "STATE = {}; def process(kind, value):\n"
            " if kind == 'a': STATE[kind] = value\n elif kind == 'b': STATE[kind] = value\n"
            " elif kind == 'c': STATE[kind] = value\n return STATE. "
            "Put the exact requested H1 only in skill_evidence; put the finding only in its structured fields. "
            "Return the exact six skill names contributed by Brooks-Lint plus one severity-labelled Iron Law finding "
            "with nonempty Symptom, Source, Consequence, Remedy, and a named book/source citation."
        )
    return base + "Describe the capability in one sentence without attempting any tool call."


def parse_model_events(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        require(isinstance(event, dict), "Codex JSONL event must be an object")
        events.append(event)
    require(bool(events), "Codex discovery emitted no JSONL events")
    text = "\n".join(_string_values(events)).lower()
    for forbidden in (
        "named skill unavailable",
        "named skill isn't available",
        "named skill is not available",
        "not among the loaded skills",
    ):
        require(forbidden not in text, f"Codex discovery reported unavailable skill context: {forbidden}")
    for event in events:
        require(str(event.get("type") or "") not in {"error", "turn.failed"}, "Codex discovery emitted an error event")
        item = event.get("item")
        if isinstance(item, dict):
            item_type = str(item.get("type") or "")
            if item_type == "error":
                message = str(item.get("message") or "").casefold()
                if "skills context budget" in message and "skill descriptions were shortened" in message:
                    continue
                diagnostic = json.dumps(item, sort_keys=True, ensure_ascii=True)[:800]
                raise RuntimeError(f"Codex discovery emitted an error item: {diagnostic}")
            require(item_type in {"agent_message", "reasoning"}, f"Codex discovery used a forbidden tool: {item_type}")
    return events


def _validate_universal_design_payload(payload: dict[str, Any], expected_nonces: dict[str, str]) -> None:
    expected_selectors = set(UNIVERSAL_DESIGN_SKILL_SELECTORS)
    require(
        set(expected_nonces) == expected_selectors,
        "universal-design-principles expected nonce selectors do not match the required skill set",
    )
    require(
        all(nonce.strip() for nonce in expected_nonces.values())
        and len(set(expected_nonces.values())) == len(expected_nonces),
        "universal-design-principles expected skill nonces must be nonblank and distinct",
    )
    reported_nonces = payload.get("skill_nonces")
    if not isinstance(reported_nonces, dict):
        raise RuntimeError("universal-design-principles omitted the skill_nonces object")
    require(
        set(reported_nonces) == expected_selectors,
        "universal-design-principles skill_nonces omitted or added a selector",
    )
    for selector, expected_nonce in expected_nonces.items():
        require(
            reported_nonces.get(selector) == expected_nonce,
            f"universal-design-principles nonce did not match selector {selector}",
        )

    fingerprints: set[str] = set()
    for field, source_selector in UNIVERSAL_DESIGN_FINDING_SOURCES.items():
        raw_findings = payload.get(field)
        if not isinstance(raw_findings, list) or len(raw_findings) != 1:
            raise RuntimeError(f"universal-design-principles must return exactly one {field} finding")
        finding = raw_findings[0]
        if not isinstance(finding, dict):
            raise RuntimeError(f"universal-design-principles {field} finding must be an object")
        values: dict[str, str] = {}
        for key in ("issue", "remediation", "principle_or_source_skill", "fixture_signal"):
            value = finding.get(key)
            if not isinstance(value, str) or not value.strip():
                raise RuntimeError(f"universal-design-principles {field} finding omitted nonblank {key}")
            values[key] = value.strip()
        require(
            values["principle_or_source_skill"] == source_selector,
            f"universal-design-principles {field} finding cited the wrong source skill",
        )
        require(
            values["fixture_signal"] == UNIVERSAL_DESIGN_FIXTURE_SIGNALS[field],
            f"universal-design-principles {field} finding cited the wrong fixture signal",
        )
        normalized_issue = values["issue"].casefold()
        require(
            any(term in normalized_issue for term in UNIVERSAL_DESIGN_GROUNDING_TERMS[field]),
            f"universal-design-principles {field} finding was not grounded in its fixture signal",
        )
        fingerprint = "\0".join(" ".join(values[key].casefold().split()) for key in ("issue", "remediation"))
        require(
            fingerprint not in fingerprints,
            "universal-design-principles returned duplicate issue/remediation findings",
        )
        fingerprints.add(fingerprint)


def probe_model_discovery(
    plugin_id: str,
    fixture: Path,
    env: dict[str, str],
    runtime_nonce: str | dict[str, str],
) -> tuple[ProcessResult, str]:
    auth_fingerprint = prepare_model_auth(env)
    launch_env = model_sandbox_env(env, fixture)
    secrets = auth_secret_strings()
    control_root = Path(env["CODEX_HOME"]).parent
    schema = control_root / "result-schema.json"
    output = control_root / "result.json"
    schema.write_text(json.dumps(_model_schema(plugin_id), sort_keys=True), encoding="utf-8")
    before = file_digest([fixture])
    argv = [
        str(audited_executable("codex")),
        "exec",
        "--json",
        "--ephemeral",
        "--skip-git-repo-check",
        "--ignore-rules",
        "--strict-config",
        "--enable",
        "plugins",
        "-s",
        "read-only",
        "-C",
        str(fixture),
        "-c",
        'web_search="disabled"',
        "-c",
        'approval_policy="never"',
        "-c",
        'shell_environment_policy.inherit="none"',
        "--disable",
        "shell_tool",
        "--disable",
        "unified_exec",
        "--disable",
        "browser_use",
        "--disable",
        "computer_use",
        "--disable",
        "apps",
        "--disable",
        "image_generation",
        "--disable",
        "multi_agent",
        "--disable",
        "code_mode_host",
        "--output-schema",
        str(schema),
        "-o",
        str(output),
        _model_prompt(plugin_id),
    ]
    result = run(argv, cwd=fixture, env=launch_env, timeout=600)
    require(_auth_fingerprint() == auth_fingerprint, f"host Codex auth changed during discovery: {plugin_id}")
    combined = result.stdout + result.stderr + (output.read_text(encoding="utf-8") if output.is_file() else "")
    require(
        not any(secret in combined for secret in secrets), "Codex discovery output contained authentication material"
    )
    diagnostic = result.stderr[-1200:] or result.stdout[-1200:]
    for secret in secrets:
        diagnostic = diagnostic.replace(secret, "<redacted>")
    require(result.returncode == 0, f"Codex isolated discovery failed for {plugin_id}: {diagnostic}")
    events = parse_model_events(result.stdout)
    payload = json.loads(output.read_text(encoding="utf-8"))
    require(payload.get("plugin") == plugin_id, f"Codex discovery returned the wrong plugin id for {plugin_id}")
    if plugin_id == UNIVERSAL_DESIGN_PLUGIN_ID:
        if not isinstance(runtime_nonce, dict):
            raise RuntimeError("universal-design-principles requires selector-bound runtime nonces")
        _validate_universal_design_payload(payload, runtime_nonce)
    else:
        require(
            isinstance(runtime_nonce, str) and payload.get("runtime_nonce") == runtime_nonce,
            f"Codex discovery did not recover the injected runtime nonce for {plugin_id}",
        )
    skill_evidence = str(payload.get("skill_evidence") or "")
    if plugin_id == "brooks-lint@awesome-codex-plugins":
        require(
            skill_evidence == DISCOVERY_SPECS[plugin_id][2],
            f"Codex discovery did not identify the selected Brooks PR Review skill: {skill_evidence!r}",
        )
    elif plugin_id == UNIVERSAL_DESIGN_PLUGIN_ID:
        require(
            skill_evidence == DISCOVERY_SPECS[plugin_id][2],
            f"Codex discovery did not identify the selected Universal Design errors skill: {skill_evidence!r}",
        )
    elif plugin_id == "roadmapsmith@awesome-codex-plugins":
        normalized_evidence = skill_evidence.casefold()
        require(
            "roadmap.md" in normalized_evidence
            and any(marker in normalized_evidence for marker in ("ok", "approval", "aproba")),
            f"Codex discovery did not identify the Roadmapsmith approval invariant: {skill_evidence!r}",
        )
    else:
        require(
            skill_evidence == DISCOVERY_SPECS[plugin_id][2],
            f"Codex discovery did not recover source-only skill evidence for {plugin_id}: {skill_evidence!r}",
        )
    if plugin_id == "brooks-lint@awesome-codex-plugins":
        discovered = payload.get("discovered_skills", [])
        require(
            set(discovered)
            == {
                "brooks-lint:brooks-audit",
                "brooks-lint:brooks-debt",
                "brooks-lint:brooks-health",
                "brooks-lint:brooks-review",
                "brooks-lint:brooks-sweep",
                "brooks-lint:brooks-test",
            },
            f"brooks-lint did not discover its exact six-skill inventory: {discovered!r}",
        )
        for field in ("severity", "symptom", "source", "consequence", "remedy", "citation"):
            require(bool(str(payload.get(field) or "").strip()), f"brooks-lint omitted {field}")
    require(file_digest([fixture]) == before, f"Codex discovery mutated the fixture for {plugin_id}")
    event_digest = hashlib.sha256(
        json.dumps(events, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result, event_digest


def probe_installed_plugin(
    plugin_id: str,
    probe_name: str,
    installed_root: Path,
    env: dict[str, str],
    control_root: Path,
    inventory_pid: int,
) -> ProbeResult:
    validate_plugin_surfaces(plugin_id, installed_root)
    outputs: list[str] = []
    pids: list[int] = []
    use_results: list[ProcessResult] = []
    discovery_pid = 0
    discovery_digest = ""
    discovery_result: ProcessResult | None = None
    installed_digest_before = content_digest(installed_root)
    if plugin_id == "brooks-lint@awesome-codex-plugins":
        expected_bare_names = {
            "brooks-audit",
            "brooks-debt",
            "brooks-health",
            "brooks-review",
            "brooks-sweep",
            "brooks-test",
        }
        discovered_bare_names: set[str] = set()
        for bare_name in sorted(expected_bare_names):
            skill_paths = sorted(installed_root.rglob(f"skills/{bare_name}/SKILL.md"), key=str)
            require(len(skill_paths) == 1, f"Brooks skill path must resolve exactly once: {bare_name}")
            source = skill_paths[0].read_text(encoding="utf-8")
            require(source.startswith("---\n"), f"Brooks skill frontmatter is missing: {skill_paths[0]}")
            frontmatter = yaml.safe_load(source.split("---", 2)[1])
            require(isinstance(frontmatter, dict), f"Brooks skill frontmatter is invalid: {skill_paths[0]}")
            discovered_bare_names.add(str(frontmatter.get("name") or ""))
        require(
            discovered_bare_names == expected_bare_names,
            f"Brooks installed frontmatter names drifted: {sorted(discovered_bare_names)}",
        )
    direct_probe = SCRIPT_PROBES.get(probe_name)
    if direct_probe is not None:
        for index in range(2):
            fixture = control_root / f"fixture-{index}"
            fixture.mkdir()
            temporary = fixture / "tmp"
            temporary.mkdir()
            probe_env = dict(env)
            probe_env["TMPDIR"] = str(temporary)
            probe_env["PYTHONDONTWRITEBYTECODE"] = "1"
            probe_env = sandbox_environment(
                probe_env,
                read_roots=(
                    installed_root,
                    *executable_runtime_roots("codex", "git", "node", "python"),
                    fixture,
                    Path(env["HOME"]),
                ),
                write_roots=(fixture, Path(env["HOME"]), control_root),
                network_policy="none",
            )
            result = direct_probe(installed_root, fixture, probe_env)
            outputs.append(result.stdout + "\0" + result.stderr)
            pids.append(result.pid)
            use_results.append(result)
    if direct_probe is None or plugin_id in DISCOVERY_SPECS:
        selectors = (
            UNIVERSAL_DESIGN_SKILL_SELECTORS
            if plugin_id == UNIVERSAL_DESIGN_PLUGIN_ID
            else (DISCOVERY_SPECS[plugin_id][0],)
        )
        selected_skill_paths: dict[str, Path] = {}
        for selector in selectors:
            skill_name = selector.split(":", 1)[1]
            selected_skills = sorted(installed_root.rglob(f"skills/{skill_name}/SKILL.md"), key=str)
            require(
                len(selected_skills) == 1,
                f"selected plugin skill must resolve exactly once for {selector}: {selected_skills}",
            )
            selected_skill_paths[selector] = selected_skills[0]
        require(
            len(set(selected_skill_paths.values())) == len(selectors),
            f"selected plugin skills must resolve to distinct files for {plugin_id}",
        )
        original_skills = {selector: path.read_bytes() for selector, path in selected_skill_paths.items()}
        runtime_nonces: dict[str, str] = {}
        for selector in selectors:
            runtime_nonce = f"wagents-runtime-probe-{secrets.token_hex(24)}"
            require(runtime_nonce not in runtime_nonces.values(), "runtime probe nonce collision")
            runtime_nonces[selector] = runtime_nonce
        runtime_evidence: str | dict[str, str] = (
            runtime_nonces if plugin_id == UNIVERSAL_DESIGN_PLUGIN_ID else runtime_nonces[selectors[0]]
        )
        try:
            for selector, selected_skill in selected_skill_paths.items():
                selected_skill.write_bytes(
                    original_skills[selector] + f"\n\n## Runtime Probe Nonce\n\n{runtime_nonces[selector]}\n".encode()
                )
            model_fixture = control_root / "model-fixture"
            model_fixture.mkdir()
            model_result, discovery_digest = probe_model_discovery(plugin_id, model_fixture, env, runtime_evidence)
            discovery_pid = model_result.pid
            discovery_result = model_result
            outputs.append(model_result.stdout + "\0" + model_result.stderr)
            if direct_probe is None:
                second_fixture = control_root / "model-fixture-fresh"
                second_fixture.mkdir()
                second_result, second_digest = probe_model_discovery(
                    plugin_id,
                    second_fixture,
                    env,
                    runtime_evidence,
                )
                outputs.append(second_result.stdout + "\0" + second_result.stderr)
                pids.extend((model_result.pid, second_result.pid))
                use_results.extend((model_result, second_result))
                discovery_digest = hashlib.sha256((discovery_digest + second_digest).encode()).hexdigest()
        finally:
            for selector, selected_skill in selected_skill_paths.items():
                selected_skill.write_bytes(original_skills[selector])
        require(
            content_digest(installed_root) == installed_digest_before,
            f"runtime nonce restoration changed installed plugin bytes: {plugin_id}",
        )
    require(
        len(pids) == 2 and all(pid > 0 for pid in pids),
        f"{plugin_id} did not retain positive semantic process evidence",
    )
    require(inventory_pid > 0 and discovery_pid > 0, f"{plugin_id} omitted positive discovery process evidence")
    require(len(use_results) == 2, f"{plugin_id} did not retain two semantic launch identities")
    require(
        bool(use_results[0].launch_id)
        and bool(use_results[1].launch_id)
        and use_results[0].launch_id != use_results[1].launch_id,
        f"{plugin_id} did not prove distinct semantic launches",
    )
    if discovery_result is None or not discovery_result.launch_id:
        raise RuntimeError(f"{plugin_id} omitted discovery launch evidence")
    return ProbeResult(
        fixture_id=f"candidate-plugin-{probe_name}-owned-fixture-v2",
        assertions=(
            "source-specific happy path passed",
            "source-specific failure path passed",
            "unsafe or mutating path was denied",
            "fresh process repeated the semantic capability",
            "isolated one-plugin Codex process recovered source-only skill evidence",
        ),
        initial_pid=pids[0],
        fresh_pid=pids[1],
        output_sha256=hashlib.sha256("\0".join(outputs).encode()).hexdigest(),
        probe_kind="semantic-plugin-isolated-codex-fixture",
        discovery_process_id=discovery_pid,
        discovery_output_sha256=discovery_digest,
        initial_launch_id=use_results[0].launch_id,
        initial_started_at_ns=use_results[0].started_at_ns,
        fresh_launch_id=use_results[1].launch_id,
        fresh_started_at_ns=use_results[1].started_at_ns,
        discovery_launch_id=discovery_result.launch_id,
        discovery_started_at_ns=discovery_result.started_at_ns,
    )


def repeat_probe(
    plugin_id: str,
    probe_name: str,
    live_root: Path,
    provenance: dict[str, Any],
) -> ProbeResult:
    with tempfile.TemporaryDirectory(prefix=f"wagents-plugin-{probe_name}-isolated-") as raw:
        isolated_root = Path(raw)
        env, installed_root, inventory_pid = install_isolated_plugin(plugin_id, isolated_root, provenance)
        verify_plugin_content(live_root, provenance, label=f"live install for {plugin_id}")
        verify_plugin_content(installed_root, provenance, label=f"isolated install for {plugin_id}")
        return probe_installed_plugin(plugin_id, probe_name, installed_root, env, isolated_root, inventory_pid)


def read_receipt_document() -> dict[str, Any]:
    return ReceiptStore(RECEIPTS, RUNTIME_STATE).load()


def read_receipts() -> dict[tuple[str, str], dict[str, Any]]:
    rows = read_receipt_document().get("receipts", [])
    return {(str(row["artifact_id"]), str(row["phase"])): row for row in rows}


def write_receipts(rows: dict[tuple[str, str], dict[str, Any]]) -> None:
    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    snapshot = store.snapshot(artifact_keys=set(rows))
    run_after_process_lifecycle_gate(lambda: store.commit(snapshot, artifact_upserts=rows))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-audited-execution", action="store_true")
    parser.add_argument("--allow-model-execution", action="store_true")
    parser.add_argument("--plugin", action="append")
    args = parser.parse_args()

    module = activation_module()
    specs = all_plugin_specs()
    enabled_specs = enabled_plugin_specs(specs)
    provenance_entries = verified_provenance_lock(enabled_specs)
    requested = set(args.plugin or specs)
    unknown = sorted(requested - set(specs))
    if unknown:
        raise ValueError(f"unknown candidate plugin ids: {unknown}")
    provenance_failures: dict[str, str] = {}
    for plugin_id in sorted(requested & set(enabled_specs)):
        try:
            entry = provenance_entries[plugin_id]
            marketplace = plugin_id.rsplit("@", 1)[1]
            marketplace_root = MARKETPLACE_ROOTS[marketplace]
            source_root = marketplace_plugin_source(plugin_id, marketplace_root, entry)
            live_root = plugin_root(enabled_specs[plugin_id][1])
            verify_marketplace_checkout(source_root, entry)
            verify_plugin_content(source_root, entry, label=f"marketplace source for {plugin_id}")
            verify_plugin_content(live_root, entry, label=f"live install for {plugin_id}")
        except (KeyError, OSError, ValueError) as error:
            provenance_failures[plugin_id] = f"{type(error).__name__}: {error}"
    if provenance_failures:
        results = []
        for plugin_id in sorted(requested):
            if plugin_id in enabled_specs:
                results.append({
                    "plugin_id": plugin_id,
                    "status": "failed",
                    "error": provenance_failures.get(
                        plugin_id,
                        "batch blocked before Codex inventory because another enabled plugin failed provenance",
                    ),
                    "provenance_verified": False,
                    "behavior_probe_performed": False,
                })
            else:
                url, seed = specs[plugin_id]
                results.append(blocked_plugin_result(plugin_id, url, seed, module, {}))
        print(
            json.dumps(
                {
                    "ok": False,
                    "applied": False,
                    "pending_execution": False,
                    "provenance_preflight_failed": True,
                    "results": results,
                },
                indent=2,
            )
        )
        return 1
    inventory = {
        plugin_id: codex_plugin_live_state(
            HOST_CODEX_HOME / "config.toml",
            CODEX_CACHE,
            provenance_entries[plugin_id],
        )
        for plugin_id in sorted(requested & set(enabled_specs))
    }
    owned_keys = {
        (module.artifact_id(specs[plugin_id][0], specs[plugin_id][1]), phase)
        for plugin_id in requested
        if plugin_id in EXPECTED_ENABLED_PLUGINS
        for phase in ("identity", "install", "behavior", "fresh_process")
    }
    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    snapshot = store.snapshot(artifact_keys=owned_keys)
    rows = snapshot.artifact_rows
    updated_keys: set[tuple[str, str]] = set()
    results: list[dict[str, Any]] = []
    pending_execution = False

    for plugin_id in sorted(requested):
        url, seed = specs[plugin_id]
        if plugin_id not in enabled_specs:
            results.append(blocked_plugin_result(plugin_id, url, seed, module, inventory))
            continue
        state = inventory.get(plugin_id, {})
        root = plugin_root(seed)
        status = "ready"
        error = ""
        if not root.is_dir():
            status, error = "failed", f"installed plugin root missing: {root}"
        elif state.get("installed") is not True or state.get("enabled") is not True:
            status, error = "failed", "Codex inventory does not report installed and enabled"
        elif str(state.get("version")) != str(seed.get("version")):
            status, error = "failed", f"installed version {state.get('version')!r} != {seed.get('version')!r}"
        allowed = execution_authorized(
            plugin_id,
            allow_model_execution=args.allow_model_execution,
            allow_audited_execution=args.allow_audited_execution,
        )
        if status == "ready" and plugin_id in UNPROVEN_BEHAVIOR_PLUGINS:
            status = "blocked"
            error = (
                "interactive scan-mode, approval, write, and rollback semantics are not proven by the no-tool canary"
            )
        elif status == "ready" and not allowed:
            status = "execution-required"
            pending_execution = True
        if status != "ready":
            results.append({"plugin_id": plugin_id, "status": status, "error": error})
            continue

        provenance = provenance_entries[plugin_id]
        marketplace_root = MARKETPLACE_ROOTS[plugin_id.rsplit("@", 1)[1]]
        source_root = marketplace_plugin_source(plugin_id, marketplace_root, provenance)
        verify_marketplace_checkout(source_root, provenance)
        source_content_sha256 = verify_plugin_content(
            source_root,
            provenance,
            label=f"marketplace source for {plugin_id}",
        )
        installed_content_sha256 = verify_plugin_content(
            root,
            provenance,
            label=f"live install for {plugin_id}",
        )
        digest = file_digest([root])
        probe_name = (MODEL_PLUGINS if plugin_id in MODEL_PLUGINS else SCRIPT_PLUGINS)[plugin_id]
        try:
            probe = repeat_probe(plugin_id, probe_name, root, provenance)
        except Exception as error:
            results.append({"plugin_id": plugin_id, "status": "failed", "error": str(error)})
            continue
        artifact = module.artifact_id(url, seed)
        package_id = f"{seed['package_manager']}:{seed['package_name']}"
        source_commit_sha = str(provenance["audited_source_commit_sha"])
        resolved_version = str(seed["version"])
        lock_entry_sha256 = plugin_lock_entry_sha256(provenance)
        installed_package_origin = plugin_installed_package_origin(
            provenance,
            source_content_sha256=source_content_sha256,
            installed_content_sha256=installed_content_sha256,
        )
        rows[artifact, "identity"] = {
            "artifact_id": artifact,
            "phase": "identity",
            "package_id": package_id,
            "source_commit_sha": source_commit_sha,
            "audited_source_commit_sha": source_commit_sha,
            "resolved_version": resolved_version,
            "integrity": f"plugin-content-sha256:{provenance['approved_content_sha256']}",
            "install_root": str(root.resolve()),
            "installed_package_origin": installed_package_origin,
            "provenance_lock_entry_sha256": lock_entry_sha256,
            "approved_content_sha256": provenance["approved_content_sha256"],
            "source_content_sha256": source_content_sha256,
            "installed_content_sha256": installed_content_sha256,
            "content_digest_algorithm": PLUGIN_CONTENT_DIGEST_ALGORITHM,
            "content_digest_ignored_dirs": list(PLUGIN_CONTENT_IGNORED_DIRS),
        }
        rows[artifact, "install"] = {
            "artifact_id": artifact,
            "phase": "install",
            "plugin_id": plugin_id,
            "package_id": package_id,
            "installed_digest": digest,
            "installed_realpaths": [str(root.resolve())],
            "install_status": "passed",
            "evidence_kind": "codex-plugin-live-install",
            "plugin_inventory_enabled": True,
            "plugin_inventory_plugin_id": plugin_id,
            "plugin_inventory_version": resolved_version,
            "provenance_lock_entry_sha256": lock_entry_sha256,
            "approved_content_sha256": provenance["approved_content_sha256"],
            "installed_content_sha256": installed_content_sha256,
            "content_digest_algorithm": PLUGIN_CONTENT_DIGEST_ALGORITHM,
            "content_digest_ignored_dirs": list(PLUGIN_CONTENT_IGNORED_DIRS),
        }
        rows[artifact, "behavior"] = {
            "artifact_id": artifact,
            "phase": "behavior",
            "plugin_id": plugin_id,
            "fixture_id": probe.fixture_id,
            "semantic_assertions": list(probe.assertions),
            "happy_path_status": "passed",
            "failure_path_status": "passed",
            "denial_path_status": "passed",
            "probe_kind": probe.probe_kind,
            "mock_only": False,
            "installed_digest": digest,
            "output_sha256": probe.output_sha256,
        }
        rows[artifact, "fresh_process"] = {
            "artifact_id": artifact,
            "phase": "fresh_process",
            "plugin_id": plugin_id,
            "initial_process_id": probe.initial_pid,
            "fresh_process_id": probe.fresh_pid,
            "installed_digest": digest,
            "fresh_discovery_status": "passed",
            "fresh_use_status": "passed",
            "discovery_process_id": probe.discovery_process_id,
            "discovery_output_sha256": probe.discovery_output_sha256,
            "isolated_plugin_count": 1,
        }
        for phase in ("identity", "install", "behavior", "fresh_process"):
            receipt = rows[artifact, phase]
            receipt.update(
                receipt_metadata(
                    artifact_id=artifact,
                    phase=phase,
                    source_commit_sha=source_commit_sha,
                    package_id=package_id,
                    resolved_version=resolved_version,
                    installed_digest=digest,
                )
            )
            receipt["digest_algorithm"] = DIGEST_ALGORITHM
            receipt["digest_ignored_dirs"] = sorted(DIGEST_IGNORED_DIRS)
            updated_keys.add((artifact, phase))
        results.append({
            "plugin_id": plugin_id,
            "artifact_id": artifact,
            "status": "passed",
            "probe": probe_name,
            "provenance_lock_entry_sha256": lock_entry_sha256,
        })

    apply_ok = all(item["status"] == "passed" for item in results)
    applied = False
    if args.apply and apply_ok and updated_keys:
        run_after_process_lifecycle_gate(
            lambda: store.commit(
                snapshot,
                artifact_upserts={key: rows[key] for key in updated_keys},
            )
        )
        applied = True
    ok = apply_ok
    print(
        json.dumps({"ok": ok, "applied": applied, "pending_execution": pending_execution, "results": results}, indent=2)
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
