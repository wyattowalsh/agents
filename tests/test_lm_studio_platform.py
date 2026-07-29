"""Tests for the LM Studio full-surface platform adapter."""

from __future__ import annotations

import json
from pathlib import Path

from wagents.platforms.base import SyncContext
from wagents.platforms.lm_studio import (
    AGENT_PRESET_PREFIX,
    INSTRUCTION_PRESET_FILENAME,
    SKILL_MIRROR_ENV,
    Adapter,
    SkillMirrorConfig,
    lm_studio_mcp_path,
    render_all_agent_presets,
    render_instruction_preset,
    render_preset,
    resolve_lm_studio_home,
    resolve_skill_mirror_config,
    select_skill_dirs,
    sync_presets,
    sync_skills,
)


def _mcphub_registry() -> dict:
    return {
        "mcphub": {
            "enabled": True,
            "base_url": "http://127.0.0.1:46683",
            "bearer_token_env_var": "MCPHUB_BEARER_TOKEN",
            "projection_adapters": {"lm-studio": "remote-stdio"},
            "groups": {
                "harness": {"enabled": True, "servers": ["foo"]},
            },
            "clients": {
                "default": {
                    "included_endpoint_kinds": ["group", "server"],
                    "included_groups": ["harness"],
                    "enabled_endpoint_kinds": ["group"],
                    "enabled_groups": ["harness"],
                    "enable_server_endpoints": True,
                },
                "lm-studio": {
                    "included_endpoint_kinds": ["group", "server"],
                    "included_groups": ["harness"],
                    "enabled_endpoint_kinds": ["group"],
                    "enabled_groups": ["harness"],
                    "enable_server_endpoints": True,
                },
            },
        },
        "servers": {
            "foo": {"command": "uvx", "args": ["foo-mcp"], "enabled": True, "env": {}},
        },
    }


def _make_skill(repo: Path, name: str) -> Path:
    skill = repo / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    return skill


def test_resolve_lm_studio_home_prefers_pointer(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    pointer_home = tmp_path / "lms-home"
    pointer_home.mkdir()
    default_home = home / ".lmstudio"
    default_home.mkdir()
    pointer = home / ".lmstudio-home-pointer"
    pointer.write_text(str(pointer_home), encoding="utf-8")

    monkeypatch.setattr("wagents.platforms.lm_studio.HOME", home)
    monkeypatch.setattr("wagents.platforms.lm_studio.LM_STUDIO_HOME_POINTER", pointer)
    monkeypatch.setattr("wagents.platforms.lm_studio.LM_STUDIO_DEFAULT_HOME", default_home)

    assert resolve_lm_studio_home() == pointer_home
    assert lm_studio_mcp_path() == pointer_home / "mcp.json"


def test_resolve_lm_studio_home_falls_back_to_default(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    default_home = home / ".lmstudio"
    default_home.mkdir()
    pointer = home / ".lmstudio-home-pointer"

    monkeypatch.setattr("wagents.platforms.lm_studio.HOME", home)
    monkeypatch.setattr("wagents.platforms.lm_studio.LM_STUDIO_HOME_POINTER", pointer)
    monkeypatch.setattr("wagents.platforms.lm_studio.LM_STUDIO_DEFAULT_HOME", default_home)

    assert resolve_lm_studio_home() == default_home


def test_resolve_lm_studio_home_missing(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr("wagents.platforms.lm_studio.HOME", home)
    monkeypatch.setattr("wagents.platforms.lm_studio.LM_STUDIO_HOME_POINTER", home / ".lmstudio-home-pointer")
    monkeypatch.setattr("wagents.platforms.lm_studio.LM_STUDIO_DEFAULT_HOME", home / ".lmstudio")

    assert resolve_lm_studio_home() is None
    assert lm_studio_mcp_path() is None


def test_render_mcp_remote_stdio_uses_placeholders(monkeypatch) -> None:
    monkeypatch.delenv("MCPHUB_BEARER_TOKEN", raising=False)
    adapter = Adapter()
    rendered = adapter.render_mcp(_mcphub_registry(), {})["mcpServers"]

    assert "mcphub_group_harness" in rendered
    entry = rendered["mcphub_group_harness"]
    assert entry["command"].endswith("scripts/mcphub/remote-stdio.sh")
    assert not entry["command"].startswith("${")
    assert Path(entry["command"]).is_absolute()
    assert entry["args"][0].startswith("http://127.0.0.1:46683/mcp")
    assert "env" not in entry
    monkeypatch.setenv("MCPHUB_BEARER_TOKEN", "sk-secret-token")
    rendered2 = adapter.render_mcp(_mcphub_registry(), {})["mcpServers"]
    assert "env" not in rendered2["mcphub_group_harness"]


def test_render_instruction_and_agent_presets() -> None:
    preset = render_instruction_preset()
    assert preset["name"] == "wagents/repo-instructions"
    assert "pre_prompt" in preset["inference_params"]
    assert "Managed by wagents" in preset["inference_params"]["pre_prompt"]
    assert "wagents" in preset
    assert preset["wagents"]["managed"] is True

    body = preset["inference_params"]["pre_prompt"]
    # RV-S-001: no absolute machine path to the repo clone
    assert "Repo root:" not in body
    assert "/Users/" not in body
    assert "path not embedded" in body
    assert "default" in body.casefold() or "none" in body.casefold()

    agents = render_all_agent_presets()
    assert agents
    assert any(name.startswith(AGENT_PRESET_PREFIX) for name in agents)
    sample = next(iter(agents.values()))
    assert sample["inference_params"]["pre_prompt"]
    assert sample["wagents"]["managed"] is True


def test_render_preset_structural_keys() -> None:
    preset = render_preset("wagents/sample", "hello system")
    assert preset["name"] == "wagents/sample"
    assert preset["inference_params"]["pre_prompt"] == "hello system"
    assert "pre_prompt_prefix" in preset["inference_params"]
    assert preset["wagents"]["managed"] is True


def test_sync_presets_preserves_user_files(tmp_path: Path) -> None:
    home = tmp_path / "lms"
    presets = home / "config-presets"
    presets.mkdir(parents=True)
    user = presets / "my-custom.preset.json"
    user.write_text(json.dumps({"name": "custom"}), encoding="utf-8")
    stale = presets / f"{AGENT_PRESET_PREFIX}stale.preset.json"
    stale.write_text("{}", encoding="utf-8")

    ctx = SyncContext(apply=True)
    sync_presets(ctx, home)

    assert (presets / INSTRUCTION_PRESET_FILENAME).is_file()
    assert user.is_file()
    assert json.loads(user.read_text(encoding="utf-8"))["name"] == "custom"
    assert not stale.exists()
    assert any(p.name.startswith(AGENT_PRESET_PREFIX) for p in presets.iterdir())


def test_resolve_skill_mirror_config_parse() -> None:
    assert resolve_skill_mirror_config({}).mode == "none"
    assert resolve_skill_mirror_config({SKILL_MIRROR_ENV: ""}).mode == "none"
    assert resolve_skill_mirror_config({SKILL_MIRROR_ENV: "none"}).mode == "none"
    assert resolve_skill_mirror_config({SKILL_MIRROR_ENV: "ALL"}).mode == "all"
    assert resolve_skill_mirror_config({SKILL_MIRROR_ENV: "bogus"}).mode == "none"

    allow = resolve_skill_mirror_config({SKILL_MIRROR_ENV: "allowlist:alpha,beta"})
    assert allow.mode == "allowlist"
    assert allow.allowlist == frozenset({"alpha", "beta"})

    csv = resolve_skill_mirror_config({SKILL_MIRROR_ENV: "alpha, beta"})
    assert csv.mode == "allowlist"
    assert csv.allowlist == frozenset({"alpha", "beta"})


def test_select_skill_dirs() -> None:
    paths = [Path("/r/skills/a"), Path("/r/skills/b")]
    assert select_skill_dirs(paths, SkillMirrorConfig(mode="none")) == []
    assert select_skill_dirs(paths, SkillMirrorConfig(mode="all")) == paths
    assert select_skill_dirs(paths, SkillMirrorConfig(mode="allowlist", allowlist=frozenset({"b"}))) == [
        Path("/r/skills/b")
    ]


def test_sync_skills_default_none(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    _make_skill(repo, "alpha")
    home = tmp_path / "lms"
    monkeypatch.setattr("wagents.platforms.lm_studio.get_repo_root", lambda: repo)
    monkeypatch.delenv(SKILL_MIRROR_ENV, raising=False)

    ctx = SyncContext(apply=True)
    sync_skills(ctx, home, repo_root=repo)

    skills = home / "skills"
    assert not skills.exists() or list(skills.iterdir()) == []


def test_sync_skills_mode_all(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    skill_a = _make_skill(repo, "alpha")
    home = tmp_path / "lms"
    monkeypatch.setattr("wagents.platforms.lm_studio.get_repo_root", lambda: repo)

    ctx = SyncContext(apply=True)
    sync_skills(ctx, home, repo_root=repo, cfg=SkillMirrorConfig(mode="all"))

    link = home / "skills" / "alpha"
    assert link.is_symlink()
    assert link.resolve() == skill_a.resolve()


def test_sync_skills_allowlist(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    _make_skill(repo, "alpha")
    skill_b = _make_skill(repo, "beta")
    home = tmp_path / "lms"
    monkeypatch.setattr("wagents.platforms.lm_studio.get_repo_root", lambda: repo)

    ctx = SyncContext(apply=True)
    sync_skills(
        ctx,
        home,
        repo_root=repo,
        cfg=SkillMirrorConfig(mode="allowlist", allowlist=frozenset({"beta"})),
    )

    assert not (home / "skills" / "alpha").exists()
    link = home / "skills" / "beta"
    assert link.is_symlink()
    assert link.resolve() == skill_b.resolve()


def test_sync_skills_purge_on_none_keeps_user_dir(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    skill_a = _make_skill(repo, "alpha")
    home = tmp_path / "lms"
    skills_home = home / "skills"
    skills_home.mkdir(parents=True)
    managed = skills_home / "alpha"
    managed.symlink_to(skill_a)
    user_dir = skills_home / "my-plugin-data"
    user_dir.mkdir()
    (user_dir / "note.txt").write_text("keep", encoding="utf-8")

    monkeypatch.setattr("wagents.platforms.lm_studio.get_repo_root", lambda: repo)

    ctx = SyncContext(apply=True)
    sync_skills(ctx, home, repo_root=repo, cfg=SkillMirrorConfig(mode="none"))

    assert not managed.exists()
    assert user_dir.is_dir()
    assert (user_dir / "note.txt").read_text(encoding="utf-8") == "keep"


def test_sync_skills_does_not_purge_skills_evil_sibling(tmp_path: Path, monkeypatch) -> None:
    """startswith false-positive: /skills-evil must not count as under /skills."""
    repo = tmp_path / "repo"
    skills = repo / "skills"
    skills.mkdir(parents=True)
    evil_root = repo / "skills-evil"
    evil_root.mkdir()
    evil_skill = evil_root / "evil"
    evil_skill.mkdir()
    (evil_skill / "SKILL.md").write_text("# evil\n", encoding="utf-8")

    home = tmp_path / "lms"
    skills_home = home / "skills"
    skills_home.mkdir(parents=True)
    evil_link = skills_home / "evil"
    evil_link.symlink_to(evil_skill)

    monkeypatch.setattr("wagents.platforms.lm_studio.get_repo_root", lambda: repo)

    ctx = SyncContext(apply=True)
    sync_skills(ctx, home, repo_root=repo, cfg=SkillMirrorConfig(mode="none"))

    # Not under repo/skills → not managed → must remain
    assert evil_link.is_symlink()
    assert evil_link.resolve() == evil_skill.resolve()


def test_sync_home_full_surface(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    lms_home = home / ".lmstudio"
    lms_home.mkdir(parents=True)
    monkeypatch.setattr("wagents.platforms.lm_studio.HOME", home)
    monkeypatch.setattr("wagents.platforms.lm_studio.LM_STUDIO_HOME_POINTER", home / ".lmstudio-home-pointer")
    monkeypatch.setattr("wagents.platforms.lm_studio.LM_STUDIO_DEFAULT_HOME", lms_home)
    monkeypatch.delenv("MCPHUB_BEARER_TOKEN", raising=False)
    monkeypatch.delenv(SKILL_MIRROR_ENV, raising=False)

    adapter = Adapter()
    ctx = SyncContext(apply=True)
    adapter.sync_home(ctx, _mcphub_registry(), {}, {}, {})

    assert (lms_home / "mcp.json").is_file()
    assert (lms_home / "config-presets" / INSTRUCTION_PRESET_FILENAME).is_file()
    # Default skill mode none: do not require skills dir or flood of links
    skills = lms_home / "skills"
    assert not skills.exists() or not any(skills.iterdir())
    payload = json.loads((lms_home / "mcp.json").read_text(encoding="utf-8"))
    assert "mcphub_group_harness" in payload["mcpServers"]


def test_sync_home_noop_without_home(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr("wagents.platforms.lm_studio.HOME", home)
    monkeypatch.setattr("wagents.platforms.lm_studio.LM_STUDIO_HOME_POINTER", home / ".lmstudio-home-pointer")
    monkeypatch.setattr("wagents.platforms.lm_studio.LM_STUDIO_DEFAULT_HOME", home / ".lmstudio")

    adapter = Adapter()
    ctx = SyncContext(apply=True)
    adapter.sync_home(ctx, _mcphub_registry(), {}, {}, {})
    assert not (home / ".lmstudio").exists()
    assert ctx.changes == []


def test_adapter_registered() -> None:
    from wagents.platforms import get_adapter, list_adapters

    assert "lm-studio" in list_adapters()
    assert get_adapter("lm-studio").name == "lm-studio"
