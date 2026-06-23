"""Unit tests for wagents.apm materialize using tmp_path fixtures.

No real apm CLI or install required.
"""

import json
from pathlib import Path

from wagents.apm import (
    doctor,
    materialize,
    materialize_agents,
    materialize_hooks,
    materialize_instructions,
)


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
                "harnesses": ["claude-code", "cursor", "github-copilot"],
            },
            {
                "id": "pre",
                "logical_event": "PreToolUse",
                "command": "python check.py",
                "matcher": "Write",
                "timeout": 5,
                "harnesses": ["cursor"],
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
    assert "claude-code.json" in names
    assert "cursor.json" in names
    assert "github-copilot.json" in names
    claude = json.loads((apm_h / "claude-code.json").read_text())
    assert "hooks" in claude
    cur = json.loads((apm_h / "cursor.json").read_text())
    assert cur.get("version") == 1
    cop = json.loads((apm_h / "github-copilot.json").read_text())
    assert "hooks" in cop


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
    # .apm generated bits
    (tmp_path / ".apm" / "agents").mkdir(parents=True)
    (tmp_path / ".apm" / "agents" / "foo.agent.md").write_text("ok", encoding="utf-8")
    (tmp_path / ".apm" / "instructions").mkdir(parents=True)
    (tmp_path / ".apm" / "instructions" / "bar.instructions.md").write_text("ok", encoding="utf-8")

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
