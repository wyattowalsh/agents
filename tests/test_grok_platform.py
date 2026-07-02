"""Tests for the Grok Build platform adapter."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.sync_agent_stack import MCP_REGISTRY_PATH, load_json
from wagents.platforms.base import SyncContext
from wagents.platforms.grok import (
    GROK_CONFIG_POLICY_PATH,
    GROK_FLEET_HOOKS_PATH,
    GROK_LSP_POLICY_PATH,
    GROK_PLANNOTATOR_HOOKS_PATH,
    PLANNOTATOR_CORE_SKILLS,
    PLANNOTATOR_EXIT_PLAN_HOOK_HOME_NAME,
    PLANNOTATOR_EXIT_PLAN_HOOK_PY_PATH,
    PLANNOTATOR_HOOKS_POLICY_LEGACY_PATH,
    PLANNOTATOR_HOOKS_POLICY_PATH,
    Adapter,
    GrokConfigDropError,
    apply_model_defaults,
    assert_no_grok_config_drops,
    blend_owned_table,
    is_grok_blend_header,
    is_grok_owned_header,
    missing_plannotator_core_skills,
    parse_toml_table_kv,
    plannotator_core_skill_roots,
    plannotator_exit_plan_hook_home_path,
    registry_mcp_server_names,
    render_grok_config,
    render_grok_fleet_hooks_json,
    render_grok_hooks,
    render_grok_plannotator_hooks,
    render_preserved_grok_config,
    resolve_plannotator_binary,
    strip_registry_mcp_tables,
    sync_grok_fleet_hooks,
    sync_grok_lsp,
    sync_grok_plannotator,
    sync_grok_skill_overlays,
)


def _fleet_registry() -> dict[str, object]:
    return {
        "version": 1,
        "hooks": [
            {
                "id": "codex-destructive-shell-guard",
                "logical_event": "PreToolUse",
                "matcher": "Bash|bash",
                "mode": "enforce",
                "command": (
                    "python3 {repo_root}/hooks/wagents-hook.py "
                    "codex-destructive-shell-guard --harness {harness}"
                ),
                "timeout": 5,
                "harnesses": ["codex"],
            },
            {
                "id": "image-input-optimizer-guard",
                "logical_event": "PreToolUse",
                "matcher": ".*",
                "mode": "enforce",
                "command": "{hook_runner} image-input-optimizer-guard --harness {harness}",
                "timeout": 60,
                "harnesses": ["codex", "claude-code", "cursor"],
            },
            {
                "id": "verify-before-stop",
                "logical_event": "Stop",
                "mode": "enforce",
                "command": "{repo_root}/hooks/verify-before-stop.sh",
                "timeout": 60,
                "harnesses": ["claude-code"],
            },
            {
                "id": "cursor-only",
                "logical_event": "PreToolUse",
                "command": "python3 {repo_root}/hooks/wagents-hook.py cursor-only --harness {harness}",
                "harnesses": ["cursor"],
            },
        ],
    }


def test_grok_build_subprocess_destructive_shell_emits_block_json():
    runner = Path(__file__).resolve().parents[1] / "hooks" / "run-wagents-hook"
    completed = subprocess.run(
        [str(runner), "cursor-destructive-shell-guard", "--harness", "grok-build"],
        input=json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "bash",
                "tool_input": {"command": "rm -rf /"},
            }
        ),
        text=True,
        capture_output=True,
        cwd=Path(__file__).resolve().parents[1],
        check=False,
    )
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "block"


def test_render_grok_hooks_projects_dispatcher_policies_as_deny_adapter():
    rendered = render_grok_hooks(_fleet_registry(), repo_root="/repo")
    groups = rendered["hooks"]["PreToolUse"]
    commands = [group["hooks"][0]["command"] for group in groups]
    # Codex-sourced dispatcher policies are projected with the grok-build harness.
    assert any("codex-destructive-shell-guard --harness grok-build" in cmd for cmd in commands)
    assert any("image-input-optimizer-guard --harness grok-build" in cmd for cmd in commands)
    assert all(cmd.startswith("/repo/hooks/run-wagents-hook ") for cmd in commands)
    # Nested Claude-style group shape (not Cursor flat).
    for group in groups:
        assert "hooks" in group
        assert group["hooks"][0]["type"] == "command"


def test_render_grok_hooks_excludes_shell_scripts_and_other_harnesses():
    rendered = render_grok_hooks(_fleet_registry(), repo_root="/repo")
    flattened = json.dumps(rendered)
    # Non-dispatcher shell script row is not projected.
    assert "verify-before-stop.sh" not in flattened
    # cursor-only row (not in codex source harness) is excluded.
    assert "cursor-only" not in flattened


def test_render_grok_fleet_hooks_json_real_registry_is_nonempty():
    text = render_grok_fleet_hooks_json("/repo")
    assert text.endswith("\n")
    data = json.loads(text)
    assert data["hooks"]


def test_sync_grok_fleet_hooks_writes_home_file(tmp_path):
    hooks_dir = tmp_path / "grok-hooks"
    ctx = SyncContext(apply=True)
    sync_grok_fleet_hooks(ctx, repo_root="/repo", hooks_dir=hooks_dir)
    written = hooks_dir / GROK_FLEET_HOOKS_PATH.name
    assert written.is_file()
    assert json.loads(written.read_text(encoding="utf-8"))["hooks"]


def test_grok_plannotator_policy_unified_source_and_legacy_parity():
    # The default policy source is the unified harness-neutral file.
    assert PLANNOTATOR_HOOKS_POLICY_PATH.name == "plannotator-hooks.policy.json"
    # The legacy grok-specific file is a byte-identical re-export (no drift).
    assert (
        PLANNOTATOR_HOOKS_POLICY_LEGACY_PATH.read_text(encoding="utf-8")
        == PLANNOTATOR_HOOKS_POLICY_PATH.read_text(encoding="utf-8")
    )


def test_is_grok_owned_header_matches_policy_tables():
    assert is_grok_owned_header("models")
    assert is_grok_owned_header("mcp_servers.mcphub_group_harness")
    assert is_grok_owned_header("compat.claude")
    assert not is_grok_owned_header("cli")
    assert not is_grok_owned_header("marketplace.sources")


def test_is_grok_blend_header_matches_blend_tables():
    assert is_grok_blend_header("ui")
    assert is_grok_blend_header("features.lsp")
    assert not is_grok_blend_header("models")
    assert not is_grok_blend_header("mcp_servers.foo")


def test_parse_toml_table_kv_extracts_header_and_keys():
    chunk = '[ui]\nyolo = true\ntheme = "dark"\n'
    header, values = parse_toml_table_kv(chunk)
    assert header == "ui"
    assert values["yolo"] == "true"
    assert values["theme"] == '"dark"'


def test_blend_owned_table_policy_overrides_shared_keys():
    policy = '[ui]\nyolo = true\npermission_mode = "always-approve"\n'
    user = '[ui]\nyolo = false\ntheme = "dark"\n'
    blended = blend_owned_table(policy, user)
    assert "yolo = true" in blended
    assert 'theme = "dark"' in blended
    assert 'permission_mode = "always-approve"' in blended
    assert "yolo = false" not in blended


def test_blend_owned_table_keeps_user_only_keys():
    policy = "[ui]\nyolo = true\n"
    user = "[ui]\nnotifications = false\n"
    blended = blend_owned_table(policy, user)
    assert "yolo = true" in blended
    assert "notifications = false" in blended


def test_render_preserved_grok_config_keeps_user_tables():
    current = """
[cli]
auto_update = true

[models]
default = "old-model"
"""
    preserved = render_preserved_grok_config(current)
    assert "[cli]" in preserved
    assert "auto_update = true" in preserved
    assert "[models]" not in preserved


def test_assert_no_grok_config_drops_detects_user_table_loss():
    before = "[cli]\nauto_update = true\n"
    after = ""
    with pytest.raises(GrokConfigDropError):
        assert_no_grok_config_drops(before, after)


def test_assert_no_drops_ignores_blend_tables():
    before = '[ui]\ntheme = "dark"\n'
    after = render_grok_config(before, load_json(MCP_REGISTRY_PATH), repo_only=False)
    assert_no_grok_config_drops(before, after, load_json(MCP_REGISTRY_PATH))


def test_grok_merge_preserves_user_sections(tmp_path, monkeypatch):
    registry = load_json(MCP_REGISTRY_PATH)
    policy_path = tmp_path / "config" / "grok-config.toml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text("[ui]\nyolo = true\n", encoding="utf-8")
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_POLICY_PATH", policy_path)

    current = """
[user_custom]
flag = true

[ui]
theme = "dark"
"""
    rendered = render_grok_config(current, registry, repo_only=False, repo_root=tmp_path)
    assert "[user_custom]" in rendered
    assert "flag = true" in rendered
    assert 'theme = "dark"' in rendered
    assert "yolo = true" in rendered


def test_strip_registry_mcp_without_markers():
    registry = load_json(MCP_REGISTRY_PATH)
    names = registry_mcp_server_names(registry)
    current = """
[cli]
auto_update = true

[mcp_servers.mcphub_group_harness]
url = "http://127.0.0.1:46683/mcp/harness"
enabled = true
"""
    stripped = strip_registry_mcp_tables(current, names)
    assert "mcphub_group_harness" not in stripped
    assert "[cli]" in stripped


def test_render_grok_config_repo_only_is_mcp_block():
    registry = load_json(MCP_REGISTRY_PATH)
    rendered = render_grok_config("", registry, repo_only=True)
    assert "BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS" in rendered
    assert "[mcp_servers.mcphub_group_harness]" in rendered


def test_render_grok_config_home_includes_policy_and_preserves_user(tmp_path, monkeypatch):
    registry = load_json(MCP_REGISTRY_PATH)
    policy_path = tmp_path / "config" / "grok-config.toml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text('[models]\ndefault = "grok-composer-2.5-fast"\n', encoding="utf-8")
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_POLICY_PATH", policy_path)

    current = "[cli]\nauto_update = false\n"
    rendered = render_grok_config(current, registry, repo_only=False, repo_root=tmp_path)
    assert "[cli]" in rendered
    assert "GROK_POLICY" in rendered or "grok-composer-2.5-fast" in rendered
    assert "BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS" in rendered


def test_render_grok_config_home_blend_ui(tmp_path, monkeypatch):
    registry = load_json(MCP_REGISTRY_PATH)
    policy_path = tmp_path / "config" / "grok-config.toml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(
        '[ui]\nyolo = true\npermission_mode = "always-approve"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_POLICY_PATH", policy_path)

    current = '[ui]\ntheme = "solarized"\n'
    rendered = render_grok_config(current, registry, repo_only=False, repo_root=tmp_path)
    assert 'theme = "solarized"' in rendered
    assert "yolo = true" in rendered


def test_apply_model_defaults_from_tooling_policy():
    body = '[models]\ndefault = "old"\n'
    policy = {"model_defaults": {"grok": {"default": "grok-composer-2.5-fast", "web_search": "grok-4.20-multi-agent"}}}
    rendered = apply_model_defaults(body, policy)
    assert 'default = "grok-composer-2.5-fast"' in rendered
    assert 'web_search = "grok-4.20-multi-agent"' in rendered


def test_grok_config_copy_matches_sanitized_template():
    if not GROK_CONFIG_POLICY_PATH.exists():
        pytest.skip("policy template missing")
    text = GROK_CONFIG_POLICY_PATH.read_text(encoding="utf-8")
    assert "[models]" in text
    assert "grok-composer-2.5-fast" in text
    assert "[ui]" in text
    assert "/Users/" not in text


def test_grok_adapter_is_available_when_config_exists(monkeypatch, tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text('[models]\ndefault = "x"\n', encoding="utf-8")
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_PATH", cfg)
    monkeypatch.setattr("wagents.platforms.grok.GROK_BINARY_PATH", tmp_path / "missing-grok")
    assert Adapter().is_available()


def test_sync_repo_writes_project_mcp_only(tmp_path, monkeypatch):
    repo_cfg = tmp_path / ".grok" / "config.toml"
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_REPO_PATH", repo_cfg)
    monkeypatch.setattr("wagents.platforms.grok.AGENTS_DIR", tmp_path / "agents")
    registry = load_json(MCP_REGISTRY_PATH)
    ctx = SyncContext(apply=True)
    Adapter().sync_repo(ctx, registry, {}, {})
    assert repo_cfg.exists()
    text = repo_cfg.read_text(encoding="utf-8")
    assert "MCP_SERVERS" in text
    assert "GROK_POLICY" not in text


def test_sync_grok_agents_creates_symlinks(tmp_path, monkeypatch):
    from wagents.platforms.grok import sync_grok_agents

    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "planner.md").write_text("---\nname: planner\ndescription: Plan\n---\n", encoding="utf-8")
    grok_agents = tmp_path / ".grok" / "agents"
    monkeypatch.setattr("wagents.platforms.grok.AGENTS_DIR", agents_dir)
    monkeypatch.setattr("wagents.platforms.grok.GROK_AGENTS_HOME_DIR", grok_agents)

    ctx = SyncContext(apply=True)
    sync_grok_agents(ctx)

    link = grok_agents / "planner.md"
    assert link.is_symlink()
    assert link.resolve() == (agents_dir / "planner.md").resolve()


def test_resolve_plannotator_binary_uses_home_local_bin():
    path = resolve_plannotator_binary()
    assert path.name == "plannotator"
    assert path.parent.name == "bin"
    assert ".local" in str(path)


def test_render_grok_plannotator_hooks_substitutes_placeholders(tmp_path, monkeypatch):
    hooks_dir = tmp_path / "hooks"
    policy = tmp_path / "grok-plannotator-hooks.json"
    policy.write_text(
        '{"hooks":{"PreToolUse":[{"command":"__PLANNOTATOR_EXIT_PLAN_HOOK__","bin":"__PLANNOTATOR_BIN__"}]}}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("wagents.platforms.grok.PLANNOTATOR_HOOKS_POLICY_PATH", policy)

    rendered = render_grok_plannotator_hooks(hooks_dir=hooks_dir)
    assert "__PLANNOTATOR_" not in rendered
    assert str(plannotator_exit_plan_hook_home_path(hooks_dir=hooks_dir).resolve()) in rendered
    assert str(resolve_plannotator_binary()) in rendered


def test_render_grok_plannotator_hooks_returns_empty_when_policy_missing(tmp_path, monkeypatch):
    missing = tmp_path / "missing.json"
    monkeypatch.setattr("wagents.platforms.grok.PLANNOTATOR_HOOKS_POLICY_PATH", missing)
    assert render_grok_plannotator_hooks(hooks_dir=tmp_path / "hooks") == ""


def test_sync_grok_plannotator_writes_home_hooks_and_shim(tmp_path, monkeypatch):
    hooks_home = tmp_path / "grok-hooks"
    destination = hooks_home / "plannotator.json"
    hook_destination = hooks_home / PLANNOTATOR_EXIT_PLAN_HOOK_HOME_NAME
    policy = tmp_path / "grok-plannotator-hooks.json"
    policy.write_text('{"hooks":{}}\n', encoding="utf-8")
    source_py = tmp_path / "plannotator-exit-plan-hook.py"
    source_py.write_text('print("ok")\n', encoding="utf-8")
    monkeypatch.setattr("wagents.platforms.grok.PLANNOTATOR_HOOKS_POLICY_PATH", policy)
    monkeypatch.setattr("wagents.platforms.grok.GROK_PLANNOTATOR_HOOKS_PATH", destination)
    monkeypatch.setattr("wagents.platforms.grok.GROK_HOOKS_DIR", hooks_home)
    monkeypatch.setattr("wagents.platforms.grok.PLANNOTATOR_EXIT_PLAN_HOOK_PY_PATH", source_py)

    ctx = SyncContext(apply=True)
    sync_grok_plannotator(ctx)

    assert destination.exists()
    assert destination.read_text(encoding="utf-8").startswith("{")
    assert hook_destination.exists()
    assert hook_destination.stat().st_mode & 0o111


def test_sync_home_skips_plannotator_when_disabled(tmp_path, monkeypatch):
    if not PLANNOTATOR_EXIT_PLAN_HOOK_PY_PATH.is_file():
        pytest.skip("plannotator hook source missing")
    hooks_home = tmp_path / "grok-hooks"
    monkeypatch.setattr("wagents.platforms.grok.GROK_HOOKS_DIR", hooks_home)
    monkeypatch.setattr("wagents.platforms.grok.GROK_PLANNOTATOR_HOOKS_PATH", hooks_home / "plannotator.json")
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_PATH", tmp_path / "config.toml")
    monkeypatch.setattr("wagents.platforms.grok.GROK_AGENTS_HOME_DIR", tmp_path / "agents")
    monkeypatch.setattr("wagents.platforms.grok.AGENTS_DIR", tmp_path / "missing-agents")

    registry = load_json(MCP_REGISTRY_PATH)
    ctx = SyncContext(apply=True, grok_plannotator_hooks=False)
    Adapter().sync_home(ctx, registry, {}, {}, {})
    assert not (hooks_home / "plannotator.json").exists()


def test_missing_plannotator_core_skills_detects_repo_overlays(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    skills_dir = repo / ".grok" / "skills"
    (skills_dir / "plannotator-review").mkdir(parents=True)
    skill_md = skills_dir / "plannotator-review" / "SKILL.md"
    skill_md.write_text("---\nname: plannotator-review\n---\n", encoding="utf-8")
    monkeypatch.setattr("wagents.platforms.grok.REPO_ROOT", repo)
    monkeypatch.setattr(
        "wagents.platforms.grok.plannotator_core_skill_roots",
        lambda *, home=None: (skills_dir,),
    )

    missing = missing_plannotator_core_skills()
    assert "plannotator-review" not in missing
    assert "plannotator-annotate" in missing
    assert "plannotator-last" in missing
    assert set(PLANNOTATOR_CORE_SKILLS) - set(missing) == {"plannotator-review"}


def test_sync_grok_skill_overlays_symlinks_all_repo_skills(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    skills_dir = repo / ".grok" / "skills"
    grill = skills_dir / "grill-me"
    grill.mkdir(parents=True)
    (grill / "SKILL.md").write_text("---\nname: grill-me\n---\n", encoding="utf-8")
    plannotator = skills_dir / "plannotator-review"
    plannotator.mkdir(parents=True)
    (plannotator / "SKILL.md").write_text("---\nname: plannotator-review\n---\n", encoding="utf-8")

    home_skills = tmp_path / "home" / ".grok" / "skills"
    monkeypatch.setattr("wagents.platforms.grok.GROK_SKILLS_REPO_DIR", skills_dir)
    monkeypatch.setattr("wagents.platforms.grok.GROK_SKILLS_HOME_DIR", home_skills)

    ctx = SyncContext(apply=True)
    sync_grok_skill_overlays(ctx)

    assert (home_skills / "grill-me").is_symlink()
    assert (home_skills / "plannotator-review").is_symlink()
    assert (home_skills / "grill-me").resolve() == grill.resolve()


def test_plannotator_core_skill_roots_includes_project_overlay_when_present(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    project_skills = repo / ".grok" / "skills"
    project_skills.mkdir(parents=True)
    monkeypatch.setattr("wagents.platforms.grok.REPO_ROOT", repo)
    monkeypatch.setattr("wagents.platforms.grok.HOME", tmp_path / "home")

    roots = plannotator_core_skill_roots(home=tmp_path / "home")
    assert project_skills in roots


def test_grok_plannotator_policy_template_exists_in_repo():
    if not PLANNOTATOR_HOOKS_POLICY_PATH.exists():
        pytest.skip("plannotator hooks policy missing")
    text = PLANNOTATOR_HOOKS_POLICY_PATH.read_text(encoding="utf-8")
    assert "__PLANNOTATOR_EXIT_PLAN_HOOK__" in text
    assert "__PLANNOTATOR_BIN__" in text
    assert "exit_plan_mode" in text


def test_grok_plannotator_hooks_path_under_home_hooks():
    assert GROK_PLANNOTATOR_HOOKS_PATH.name == "plannotator.json"
    assert GROK_PLANNOTATOR_HOOKS_PATH.parent.name == "hooks"


def test_grok_lsp_policy_json_valid():
    assert GROK_LSP_POLICY_PATH.is_file(), "config/grok-lsp.json must be tracked in the repo"
    import json

    payload = json.loads(GROK_LSP_POLICY_PATH.read_text(encoding="utf-8"))
    required = {"command", "extensionToLanguage", "startupTimeout"}
    for key, server in payload.items():
        assert required.issubset(server), key


def test_grok_config_policy_includes_subagent_composer_pins():
    if not GROK_CONFIG_POLICY_PATH.is_file():
        pytest.skip("grok policy template missing")
    text = GROK_CONFIG_POLICY_PATH.read_text(encoding="utf-8")
    assert 'explore = "grok-composer-2.5-fast"' in text
    assert 'plan = "grok-composer-2.5-fast"' in text
    assert 'general-purpose = "grok-composer-2.5-fast"' in text
    assert 'fork_secondary_model = "grok-composer-2.5-fast"' in text
    assert "load_envrc = true" in text


def test_sync_grok_lsp_copies_policy_to_home(tmp_path, monkeypatch):
    policy = tmp_path / "grok-lsp.json"
    policy.write_text('{"typescript":{"command":"npx"}}\n', encoding="utf-8")
    destination = tmp_path / "home-lsp.json"
    monkeypatch.setattr("wagents.platforms.grok.GROK_LSP_POLICY_PATH", policy)
    monkeypatch.setattr("wagents.platforms.grok.GROK_LSP_HOME_PATH", destination)

    ctx = SyncContext(apply=True)
    sync_grok_lsp(ctx)

    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == policy.read_text(encoding="utf-8")


def test_sync_grok_lsp_idempotent(tmp_path, monkeypatch):
    policy = tmp_path / "grok-lsp.json"
    policy.write_text('{"go":{"command":"gopls"}}\n', encoding="utf-8")
    destination = tmp_path / "home-lsp.json"
    destination.write_text(policy.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr("wagents.platforms.grok.GROK_LSP_POLICY_PATH", policy)
    monkeypatch.setattr("wagents.platforms.grok.GROK_LSP_HOME_PATH", destination)

    ctx = SyncContext(apply=True)
    sync_grok_lsp(ctx)

    assert ctx.changes == []
