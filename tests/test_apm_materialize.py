"""Unit tests for wagents.apm materialize using tmp_path fixtures.

No real apm CLI or install required.
"""

import json
import subprocess
import sys
from pathlib import Path

import yaml

from wagents.apm import (
    doctor,
    materialize,
    materialize_agents,
    materialize_hooks,
    materialize_instructions,
    materialize_scoped_rules,
)
from wagents.hooks import render as hook_render
from wagents.hooks.render import render_codex_hooks, render_copilot_hooks, render_cursor_hooks


def _write_agent(tmp: Path, name: str, description: str, tools: str = "") -> Path:
    agents = tmp / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    fm = f"""---
name: {name}
description: {description}
"""
    if tools:
        fm += f"tools: {tools}\n"
    fm += f"---\n\nYou are {name}.\n"
    p = agents / f"{name}.md"
    p.write_text(fm, encoding="utf-8")
    return p


def _write_global_instructions(tmp: Path) -> Path:
    ins = tmp / "instructions"
    ins.mkdir(parents=True, exist_ok=True)
    p = ins / "global.md"
    p.write_text("# Global\n\nBe helpful.\n", encoding="utf-8")
    return p


def _write_overlay(tmp: Path, fname: str, content: str = "") -> Path:
    ins = tmp / "instructions"
    ins.mkdir(parents=True, exist_ok=True)
    p = ins / fname
    body = content or "Platform notes.\n"
    p.write_text(body, encoding="utf-8")
    return p


def _write_hook_registry(tmp: Path) -> Path:
    cfg = tmp / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 1,
        "hooks": [
            {
                "id": "sess",
                "logical_event": "SessionStart",
                "command": "echo start",
                "timeout": 5,
                "harnesses": ["codex", "claude-code", "cursor", "github-copilot", "gemini-cli"],
            },
            {
                "id": "pre",
                "logical_event": "PreToolUse",
                "command": "python3 {repo_root}/hooks/check.py --harness {harness}",
                "matcher": "Write",
                "timeout": 5,
                "harnesses": ["cursor", "gemini-cli"],
            },
        ],
    }
    p = cfg / "hook-registry.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _write_mcp_registry(tmp: Path) -> Path:
    cfg = tmp / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 1,
        "servers": {
            "brave-search": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@brave/brave-search-mcp-server"],
                "enabled": True,
            },
            "docling-local": {
                "transport": "stdio",
                "command": "${REPO_ROOT}/scripts/mcphub/docling-stdio.sh",
                "args": [],
                "enabled": True,
            },
            "internal-only": {
                "transport": "stdio",
                "command": "node internal.js",
                "enabled": True,
                "tags": ["wagents_managed"],
            },
        },
    }
    p = cfg / "mcp-registry.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_materialize_agents_writes_agent_md(tmp_path: Path):
    _write_agent(tmp_path, "reviewer", "Reviews code.", "Read, Grep")
    touched = materialize_agents(tmp_path)
    assert any("reviewer.agent.md" in str(p) for p in touched)
    out = tmp_path / ".apm" / "agents" / "reviewer.agent.md"
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "name: reviewer" in text
    assert "description: Reviews code." in text
    assert "tools: Read, Grep" in text or "Read, Grep" in text
    assert "You are reviewer." in text


def test_materialize_agents_strips_readme_and_stale(tmp_path: Path):
    _write_agent(tmp_path, "a1", "d1")
    (tmp_path / "agents" / "README.md").write_text("ignore", encoding="utf-8")
    materialize_agents(tmp_path)
    out_dir = tmp_path / ".apm" / "agents"
    assert (out_dir / "a1.agent.md").exists()
    # create a stale and re-run
    stale = out_dir / "stale.agent.md"
    stale.write_text("old", encoding="utf-8")
    materialize_agents(tmp_path)
    assert not stale.exists()


def _write_claude_rule(tmp: Path, name: str, paths: list[str], body: str) -> Path:
    rules = tmp / ".claude" / "rules"
    rules.mkdir(parents=True, exist_ok=True)
    lines = ["---", "paths:"]
    lines.extend(f'  - "{p}"' for p in paths)
    lines.append("---")
    lines.append(body)
    p = rules / f"{name}.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_materialize_scoped_rules_projects_path_rules(tmp_path: Path):
    _write_claude_rule(tmp_path, "docs-verify", ["docs/**/*.mdx"], "Run docs build.\n")
    _write_claude_rule(tmp_path, "global", ["**/*"], "Always on.\n")
    touched = materialize_scoped_rules(tmp_path)
    apm_i = tmp_path / ".apm" / "instructions"
    assert (apm_i / "docs-verify.instructions.md").exists()
    assert "applyTo: docs/**/*.mdx" in (apm_i / "docs-verify.instructions.md").read_text()
    assert not (apm_i / "global.instructions.md").exists()
    assert any("docs-verify.instructions.md" in str(p) for p in touched)


def test_materialize_instructions_global_and_overlays(tmp_path: Path):
    _write_global_instructions(tmp_path)
    _write_overlay(tmp_path, "copilot-global.md", "Copilot only.\n")
    _write_overlay(tmp_path, "claude-code-global.md", "@./instructions/global.md\nClaude shim.\n")
    materialize_instructions(tmp_path)
    apm_i = tmp_path / ".apm" / "instructions"
    assert (apm_i / "global.instructions.md").exists()
    assert (apm_i / "copilot.instructions.md").exists()
    assert (apm_i / "claude-code.instructions.md").exists()
    gtext = (apm_i / "global.instructions.md").read_text()
    assert "applyTo: '**/*'" in gtext
    ctext = (apm_i / "claude-code.instructions.md").read_text()
    assert "@./" not in ctext  # stripped


def test_materialize_hooks_emits_shapes(tmp_path: Path):
    _write_hook_registry(tmp_path)
    touched = materialize_hooks(tmp_path)
    apm_h = tmp_path / ".apm" / "hooks"
    names = [p.name for p in touched]
    assert "codex.json" in names
    assert "claude-code.json" in names
    assert "cursor.json" in names
    assert "github-copilot.json" in names
    assert "gemini-cli.json" in names
    codex = json.loads((apm_h / "codex.json").read_text())
    assert "SessionStart" in codex["hooks"]
    claude = json.loads((apm_h / "claude-code.json").read_text())
    assert "hooks" in claude
    cur = json.loads((apm_h / "cursor.json").read_text())
    assert cur.get("version") == 1
    assert "${workspaceFolder}" not in json.dumps(cur)
    assert "$CURSOR_PROJECT_DIR/hooks/run-wagents-hook" in json.dumps(cur)
    cop = json.loads((apm_h / "github-copilot.json").read_text())
    assert "hooks" in cop
    gemini = json.loads((apm_h / "gemini-cli.json").read_text())
    assert "BeforeTool" in gemini["hooks"]


def test_materialize_hooks_bundle_tier_matches_shared_renderers(tmp_path: Path, monkeypatch):
    """T-090b/T-090c: APM uses the same bundle renderer as fleet sync."""
    registry = {
        "version": 1,
        "hooks": [
            {
                "id": "codex-shell",
                "logical_policy": "codex-shell",
                "logical_event": "PreToolUse",
                "matcher": "Bash",
                "command": "{hook_runner} codex-shell --harness {harness}",
                "timeout": 5,
                "bundle_group": "codex-shell-file-guards",
                "bundle_mode": "enforce-chain",
                "harnesses": ["codex"],
            },
            {
                "id": "codex-file",
                "logical_policy": "codex-file",
                "logical_event": "PreToolUse",
                "matcher": "Write",
                "command": "{hook_runner} codex-file --harness {harness}",
                "timeout": 5,
                "bundle_group": "codex-shell-file-guards",
                "bundle_mode": "enforce-chain",
                "harnesses": ["codex"],
            },
            {
                "id": "cursor-shell",
                "logical_policy": "cursor-shell",
                "logical_event": "PreToolUse",
                "matcher": "Bash",
                "command": "{hook_runner} cursor-shell --harness {harness}",
                "timeout": 5,
                "bundle_group": "cursor-shell-file-guards",
                "bundle_mode": "enforce-chain",
                "harnesses": ["cursor"],
            },
            {
                "id": "cursor-file",
                "logical_policy": "cursor-file",
                "logical_event": "PreToolUse",
                "matcher": "Write",
                "command": "{hook_runner} cursor-file --harness {harness}",
                "timeout": 5,
                "bundle_group": "cursor-shell-file-guards",
                "bundle_mode": "enforce-chain",
                "harnesses": ["cursor"],
            },
            {
                "id": "post-edit-format",
                "logical_policy": "post-edit-format",
                "logical_event": "PostToolUse",
                "command": "./hooks/auto-format.sh",
                "timeout": 60,
                "bundle_group": "copilot-post-edit-quality",
                "harnesses": ["github-copilot"],
            },
            {
                "id": "post-edit-lint",
                "logical_policy": "post-edit-lint",
                "logical_event": "PostToolUse",
                "command": "./hooks/lint-check.sh",
                "timeout": 30,
                "bundle_group": "copilot-post-edit-quality",
                "harnesses": ["github-copilot"],
            },
        ],
    }
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "hook-registry.json").write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(hook_render, "resolve_hook_perf_tier", lambda *, override=None: "bundle")

    materialize_hooks(tmp_path)
    apm_h = tmp_path / ".apm" / "hooks"

    assert json.loads((apm_h / "codex.json").read_text()) == render_codex_hooks(
        registry,
        repo_root=".",
        perf_tier="bundle",
    )
    assert json.loads((apm_h / "cursor.json").read_text()) == render_cursor_hooks(
        registry,
        repo_root="$CURSOR_PROJECT_DIR",
        perf_tier="bundle",
    )
    assert json.loads((apm_h / "github-copilot.json").read_text()) == render_copilot_hooks(
        registry,
        repo_root=".",
        perf_tier="bundle",
    )


def test_materialize_orchestrates_and_updates_apm_yml(tmp_path: Path):
    _write_agent(tmp_path, "reviewer", "r")
    _write_global_instructions(tmp_path)
    _write_hook_registry(tmp_path)
    _write_mcp_registry(tmp_path)

    res = materialize(tmp_path)
    assert res["ok"]
    assert any("reviewer.agent.md" in t for t in res["touched"])
    assert (tmp_path / "apm.yml").exists()
    apm_text = (tmp_path / "apm.yml").read_text()
    assert "BEGIN WAGENTS-MCP" in apm_text
    assert "mcp: []" in apm_text
    assert "brave-search" not in apm_text


def test_materialize_check_mode_reports_without_write(tmp_path: Path):
    _write_agent(tmp_path, "x", "xd")
    _write_global_instructions(tmp_path)
    res = materialize(tmp_path, check=True)
    assert res["check"] is True
    # .apm may have been partially created by prior? but check returns intent list
    assert isinstance(res["touched"], list)


def test_doctor_reports_keys_and_generated(tmp_path: Path):
    # minimal opencode.json with required
    ojc = tmp_path / "opencode.json"
    ojc.write_text(
        json.dumps({
            "plugin": [],
            "model": "x",
            "instructions": [],
            "skills": {"paths": ["skills"]},
        }),
        encoding="utf-8",
    )
    # apm.yml
    (tmp_path / "apm.yml").write_text("name: t\n", encoding="utf-8")
    _write_opencode_agents_config(tmp_path, ["foo"])
    # .apm generated bits
    (tmp_path / ".apm" / "agents").mkdir(parents=True)
    (tmp_path / ".apm" / "agents" / "foo.agent.md").write_text("ok", encoding="utf-8")
    (tmp_path / ".apm" / "instructions").mkdir(parents=True)
    (tmp_path / ".apm" / "instructions" / "bar.instructions.md").write_text("ok", encoding="utf-8")
    (tmp_path / ".opencode" / "agents").mkdir(parents=True)
    (tmp_path / ".opencode" / "agents" / "foo.md").write_text(
        """---
name: foo
description: Foo agent.
mode: subagent
temperature: 0.1
color: primary
permission:
  edit: deny
---

<!-- Managed by wagents sync from agents/ + config/opencode-agents.json -->

ok
""",
        encoding="utf-8",
    )

    rep = doctor(tmp_path)
    assert rep["ok"] is True
    names = [c["name"] for c in rep["checks"]]
    assert "opencode.json" in names
    assert "apm.yml" in names
    assert ".apm/" in names


def test_doctor_fails_when_missing(tmp_path: Path):
    rep = doctor(tmp_path)
    assert rep["ok"] is False
    msgs = " ".join(str(c) for c in rep["checks"])
    assert "opencode.json" in msgs or "apm.yml" in msgs


def _write_opencode_doctor_fixture(tmp: Path) -> None:
    ojc = tmp / "opencode.json"
    ojc.write_text(
        json.dumps({
            "plugin": [],
            "model": "x",
            "instructions": [],
            "skills": {"paths": ["skills"]},
        }),
        encoding="utf-8",
    )
    (tmp / "apm.yml").write_text("name: t\n", encoding="utf-8")
    (tmp / ".apm" / "agents").mkdir(parents=True)
    (tmp / ".apm" / "agents" / "foo.agent.md").write_text("ok", encoding="utf-8")
    (tmp / ".apm" / "instructions").mkdir(parents=True)
    (tmp / ".apm" / "instructions" / "bar.instructions.md").write_text("ok", encoding="utf-8")


def _write_opencode_agents_config(tmp: Path, names: list[str]) -> None:
    config_dir = tmp / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    agents = [
        {
            "name": name,
            "mode": "subagent",
            "temperature": 0.1,
            "color": "primary",
            "permission": {"edit": "deny", "bash": "ask", "webfetch": "allow"},
        }
        for name in names
    ]
    (config_dir / "opencode-agents.json").write_text(
        json.dumps({"version": 1, "agents": agents}),
        encoding="utf-8",
    )


def _managed_opencode_agent_body(name: str, *, include_tools: bool = False) -> str:
    tools_line = "tools: all\npermissionMode: default\n" if include_tools else ""
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {name.title()} agent.\n"
        f"{tools_line}"
        "mode: subagent\n"
        "temperature: 0.1\n"
        "color: primary\n"
        "permission:\n"
        "  edit: deny\n"
        "---\n\n"
        "<!-- Managed by wagents sync from agents/ + config/opencode-agents.json -->\n"
        f"{name.title()} body.\n"
    )


def test_doctor_opencode_agents_contract_ok(tmp_path: Path):
    _write_opencode_doctor_fixture(tmp_path)
    _write_opencode_agents_config(tmp_path, ["reviewer"])
    agents_dir = tmp_path / ".opencode" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "reviewer.md").write_text(_managed_opencode_agent_body("reviewer"), encoding="utf-8")

    rep = doctor(tmp_path)
    contract = next(c for c in rep["checks"] if c["name"] == "opencode-agents-contract")
    assert contract["ok"] is True


def test_doctor_opencode_agents_contract_fails_on_tools_all(tmp_path: Path):
    _write_opencode_doctor_fixture(tmp_path)
    _write_opencode_agents_config(tmp_path, ["reviewer"])
    agents_dir = tmp_path / ".opencode" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "reviewer.md").write_text(
        _managed_opencode_agent_body("reviewer", include_tools=True),
        encoding="utf-8",
    )

    rep = doctor(tmp_path)
    assert rep["ok"] is False
    contract = next(c for c in rep["checks"] if c["name"] == "opencode-agents-contract")
    assert contract["ok"] is False
    assert "sync-opencode" in contract.get("message", "")


def test_doctor_opencode_agents_contract_fails_on_missing_overlay_file(tmp_path: Path):
    _write_opencode_doctor_fixture(tmp_path)
    _write_opencode_agents_config(tmp_path, ["reviewer", "planner"])
    agents_dir = tmp_path / ".opencode" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "reviewer.md").write_text(_managed_opencode_agent_body("reviewer"), encoding="utf-8")

    rep = doctor(tmp_path)
    assert rep["ok"] is False
    contract = next(c for c in rep["checks"] if c["name"] == "opencode-agents-contract")
    assert contract["ok"] is False
    assert "planner.md" in contract.get("message", "")


def test_doctor_opencode_agents_contract_fails_on_unmanaged_portable_file(tmp_path: Path):
    _write_opencode_doctor_fixture(tmp_path)
    _write_opencode_agents_config(tmp_path, ["reviewer", "planner"])
    agents_dir = tmp_path / ".opencode" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "reviewer.md").write_text(_managed_opencode_agent_body("reviewer"), encoding="utf-8")
    (agents_dir / "planner.md").write_text(
        "---\nname: planner\ndescription: Plan.\ntools: all\npermissionMode: default\n---\n\nPlan.\n",
        encoding="utf-8",
    )

    rep = doctor(tmp_path)
    assert rep["ok"] is False
    contract = next(c for c in rep["checks"] if c["name"] == "opencode-agents-contract")
    assert contract["ok"] is False
    assert "planner.md" in contract.get("message", "")
    assert "sync-opencode" in contract.get("message", "")


def test_refresh_lock_hashes_updates_stale_entries(tmp_path: Path):
    from wagents.apm import refresh_lock_hashes

    deployed = ".opencode/agents/reviewer.md"
    path = tmp_path / deployed
    path.parent.mkdir(parents=True)
    path.write_text("managed agent\n", encoding="utf-8")
    stale_hash = "sha256:" + ("0" * 64)
    lock = {
        "lockfile_version": "1",
        "generated_at": "2026-01-01T00:00:00+00:00",
        "dependencies": [],
        "local_deployed_files": [deployed],
        "local_deployed_file_hashes": {deployed: stale_hash},
    }
    (tmp_path / "apm.lock.yaml").write_text(yaml.safe_dump(lock, sort_keys=False), encoding="utf-8")

    result = refresh_lock_hashes(tmp_path)
    assert result["ok"] is True
    updated = yaml.safe_load((tmp_path / "apm.lock.yaml").read_text(encoding="utf-8"))
    assert updated["local_deployed_file_hashes"][deployed] != stale_hash


def test_refresh_lock_hashes_check_detects_drift(tmp_path: Path):
    from wagents.apm import refresh_lock_hashes

    deployed = ".opencode/agents/reviewer.md"
    path = tmp_path / deployed
    path.parent.mkdir(parents=True)
    path.write_text("managed agent\n", encoding="utf-8")
    lock = {
        "lockfile_version": "1",
        "generated_at": "2026-01-01T00:00:00+00:00",
        "dependencies": [],
        "local_deployed_files": [deployed],
        "local_deployed_file_hashes": {deployed: "sha256:" + ("0" * 64)},
    }
    (tmp_path / "apm.lock.yaml").write_text(yaml.safe_dump(lock, sort_keys=False), encoding="utf-8")

    result = refresh_lock_hashes(tmp_path, check=True)
    assert result["ok"] is False
    assert deployed in result["drifts"]


def test_apm_materialize_cli_check_exits_stale(tmp_path: Path, monkeypatch):
    from typer.testing import CliRunner

    from wagents.cli import app

    _write_agent(tmp_path, "stale", "needs regen")
    _write_global_instructions(tmp_path)
    monkeypatch.setattr("wagents.context.get_repo_root", lambda: tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["apm", "materialize", "--check"])
    assert result.exit_code == 1, result.output
    assert "stale" in result.output.lower() or "Would update" in result.output


def test_cli_run_propagates_nonzero_app_return_code():
    repo_root = Path(__file__).resolve().parents[1]
    code = (
        "import wagents.cli as cli; "
        "cli.app = lambda **kwargs: 7; "
        "cli.end_command_telemetry = lambda code: None; "
        "cli.run()"
    )

    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 7, proc.stderr or proc.stdout
