import json
import subprocess
import sys
from typing import Any, cast

import pytest

from wagents.external_skills import parse_external_skill_entries
from wagents.installed_inventory import (
    CLEANUP_ACTION_MANUAL_REVIEW,
    CLEANUP_ACTION_NONE,
    CLEANUP_ACTION_PRESERVE,
    CLEANUP_ACTION_REFRESH_PLUGIN_CACHE,
    CLEANUP_ACTION_REMOVE_GENERATED_SYMLINK,
    DUPLICATE_CLASS_DIVERGENT_BODY,
    DUPLICATE_CLASS_SAME_BODY,
    DUPLICATE_CLASS_SAME_REALPATH,
    EXPOSURE_OWNER_DIRECT_REPO_PATH,
    EXPOSURE_OWNER_PLUGIN,
    HarnessQueryResult,
    _merge_local_skill_roots_into_query,
    _run_harness_command,
    build_skill_cleanup_report,
    collect_installed_inventory,
    collect_skill_cleanup_exposures,
    load_installed_skill_supersession_aliases,
    mirror_grok_skills_from_claude,
    query_harness_skills,
    repo_skill_exposure_owner_for_agent,
    skills_cli_agent_id,
)


def _completed(cmd, payload):
    return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")


def _write_skill(path, name: str, description: str = "Demo") -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
        encoding="utf-8",
    )


def test_collect_installed_inventory_normalizes_repo_curated_and_lock_sources(tmp_path):
    root = tmp_path / "repo"
    home = tmp_path / "home"
    repo_skill_dir = root / "skills" / "repo-skill"
    repo_skill_dir.mkdir(parents=True)
    (repo_skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: repo-skill\n"
        "description: Repo owned\n"
        "license: MIT\n"
        "metadata:\n"
        "  version: 1.2.3\n"
        "  author: Repo\n"
        "---\n\n"
        "# Repo Skill\n"
    )

    curated_skill_dir = home / ".agents" / "skills" / "curated-skill"
    curated_skill_dir.mkdir(parents=True)
    (curated_skill_dir / "SKILL.md").write_text(
        "---\nname: curated-skill\ndescription: Curated install\n---\n\n# Curated Skill\n"
    )

    lock_skill_dir = home / ".agents" / "skills" / "lock-skill"
    lock_skill_dir.mkdir(parents=True)
    (lock_skill_dir / "SKILL.md").write_text(
        "---\nname: lock-skill\ndescription: Lock sourced\nmetadata:\n  author: Lock Author\n---\n\n# Lock Skill\n"
    )

    state_dir = home / ".local" / "state" / "skills"
    state_dir.mkdir(parents=True)
    (state_dir / ".skill-lock.json").write_text(
        json.dumps({"skills": {"lock-skill": {"source": "example/skills", "sourceType": "github"}}})
    )

    curated_entries = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add vercel-labs/agent-skills --skill curated-skill -y -g -a codex claude-code
```
"""
    )

    def runner(cmd, **kwargs):
        agent = cmd[6]
        payload = [
            {
                "name": "repo-skill",
                "path": str(repo_skill_dir),
                "scope": "global",
                "agents": ["Claude Code"],
            },
        ]
        if agent == "claude-code":
            payload.append({
                "name": "curated-skill",
                "path": str(curated_skill_dir),
                "scope": "global",
                "agents": ["Codex", "Claude Code"],
            })
        payload.append(
            {
                "name": "lock-skill",
                "path": str(lock_skill_dir),
                "scope": "global",
                "agents": ["Antigravity"] if agent == "antigravity" else [],
            },
        )
        return _completed(cmd, payload)

    snapshot = collect_installed_inventory(
        agent_ids=("antigravity", "claude-code"),
        root=root,
        home=home,
        runner=runner,
        external_entries=curated_entries,
    )

    by_name = {row.name: row for row in snapshot.rows}

    assert by_name["repo-skill"].provenance_status == "repo-owned"
    assert by_name["repo-skill"].install_source == str(root.resolve())
    assert by_name["repo-skill"].version == "1.2.3"

    assert by_name["curated-skill"].provenance_status == "verified-curated-external"
    assert by_name["curated-skill"].source == "vercel-labs/agent-skills"
    assert by_name["curated-skill"].installed_agents == ("antigravity", "claude-code", "codex")

    assert by_name["lock-skill"].provenance_status == "installed-external"
    assert by_name["lock-skill"].source == "example/skills"
    assert by_name["lock-skill"].author == "Lock Author"


def test_curated_collision_prefers_verified_install_command(tmp_path):
    """verified-install-command entry must win over a same-name unresolved entry."""
    root = tmp_path / "repo"
    home = tmp_path / "home"
    skill_dir = home / ".agents" / "skills" / "stripe-best-practices"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: stripe-best-practices\ndescription: Stripe\n---\n")

    # Verified install entry first, unresolved avoid entry second — last-write-wins
    # would leave the unresolved entry in control.
    curated_entries = parse_external_skill_entries(
        """
        ## Install Now After Trust Gate

        ```bash
        npx skills add stripe/ai --skill stripe-best-practices -y -g -a claude-code
        ```

        ## Keep Global Only Or Avoid

        - `docs.stripe.com@stripe-best-practices`: registry syntax and provenance still need verification.
        """
    )

    def runner(cmd, **kwargs):
        return _completed(
            cmd,
            [{"name": "stripe-best-practices", "path": str(skill_dir), "scope": "global", "agents": ["Claude Code"]}],
        )

    snapshot = collect_installed_inventory(
        agent_ids=("claude-code",),
        root=root,
        home=home,
        runner=runner,
        external_entries=curated_entries,
    )

    by_name = {row.name: row for row in snapshot.rows}
    row = by_name["stripe-best-practices"]
    assert row.provenance_status == "verified-curated-external", (
        f"Expected verified-curated-external, got {row.provenance_status}"
    )
    assert row.is_installable(), "verified row must be installable"
    assert "stripe-best-practices" in row.install_command


def test_collect_installed_inventory_reports_query_errors(tmp_path):
    home = tmp_path / "home"
    root = tmp_path / "repo"
    root.mkdir()
    home.mkdir()

    def runner(cmd, **kwargs):
        if cmd[6] == "github-copilot":
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Invalid agents: github-copilot")
        return _completed(cmd, [])

    snapshot = collect_installed_inventory(
        agent_ids=("claude-code", "github-copilot"),
        root=root,
        home=home,
        runner=runner,
        external_entries=[],
    )

    errors = {query.agent_id: query.error for query in snapshot.queries if not query.ok}
    assert errors["github-copilot"] == "Invalid agents: github-copilot"


def test_query_harness_skills_reports_timeout(tmp_path):
    def runner(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    (result,) = query_harness_skills(agent_ids=("claude-code",), runner=runner, timeout_sec=3, home=tmp_path)

    assert not result.ok
    assert result.error.startswith("Timed out after 3s:")


def test_query_harness_skills_falls_back_to_local_root_on_timeout(tmp_path):
    skill_dir = tmp_path / ".claude" / "skills" / "fallback-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: fallback-skill\ndescription: Local fallback\n---\n")

    def runner(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    (result,) = query_harness_skills(agent_ids=("claude-code",), runner=runner, timeout_sec=3, home=tmp_path)

    assert result.ok
    assert result.error.startswith("Fallback local skill-root inventory after timeout:")
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.queried_agent == "claude-code"
    assert entry.name == "fallback-skill"
    assert entry.path == str(skill_dir)
    assert entry.scope == "global"
    assert entry.raw_agents == ("Claude Code",)


def test_query_harness_skills_falls_back_for_plugin_overlap_harnesses(tmp_path):
    roots = {
        "antigravity": (tmp_path / ".agents" / "skills" / "fallback-skill", "Antigravity"),
        "crush": (tmp_path / ".config" / "crush" / "skills" / "fallback-skill", "Crush"),
        "cursor": (tmp_path / ".cursor" / "skills" / "fallback-skill", "Cursor"),
    }
    for skill_dir, _label in roots.values():
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: fallback-skill\ndescription: Local fallback\n---\n")

    def runner(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    results = query_harness_skills(
        agent_ids=("antigravity", "crush", "cursor"),
        runner=runner,
        timeout_sec=3,
        home=tmp_path,
    )

    by_agent = {result.agent_id: result for result in results}
    for agent_id, (skill_dir, label) in roots.items():
        result = by_agent[agent_id]
        assert result.ok
        assert result.error.startswith("Fallback local skill-root inventory after timeout:")
        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.queried_agent == agent_id
        assert entry.name == "fallback-skill"
        assert entry.path == str(skill_dir)
        assert entry.scope == "global"
        assert entry.raw_agents == (label,)


def test_query_harness_skills_fallback_includes_universal_root_for_codex_and_opencode(tmp_path):
    universal_skill = tmp_path / ".agents" / "skills" / "universal-skill"
    universal_skill.mkdir(parents=True)
    (universal_skill / "SKILL.md").write_text(
        "---\nname: universal-skill\ndescription: Universal fallback\n---\n"
    )

    def runner(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    results = query_harness_skills(
        agent_ids=("codex", "opencode"),
        runner=runner,
        timeout_sec=3,
        home=tmp_path,
    )

    by_agent = {result.agent_id: result for result in results}
    for agent_id, label in (("codex", "Codex"), ("opencode", "OpenCode")):
        result = by_agent[agent_id]
        assert result.ok
        assert result.error.startswith("Fallback local skill-root inventory after timeout:")
        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.name == "universal-skill"
        assert entry.path == str(universal_skill)
        assert entry.raw_agents == (label,)


def test_run_harness_command_captures_large_stdout():
    script = (
        "import json; "
        "print(json.dumps([{'name': str(i), 'path': 'x' * 80, 'scope': 'global', "
        "'agents': ['Codex']} for i in range(2000)]))"
    )

    result = _run_harness_command(
        [sys.executable, "-c", script],
        runner=subprocess.run,
        timeout_sec=10,
    )

    assert result.returncode == 0
    assert len(result.stdout) > 65536
    assert json.loads(result.stdout)[0]["agents"] == ["Codex"]


def test_query_grok_harness_scans_grok_and_claude_skill_roots(tmp_path):
    grok_skill_dir = tmp_path / ".grok" / "skills" / "grok-only"
    claude_skill_dir = tmp_path / ".claude" / "skills" / "shared-skill"
    grok_skill_dir.mkdir(parents=True)
    claude_skill_dir.mkdir(parents=True)
    (grok_skill_dir / "SKILL.md").write_text("---\nname: grok-only\ndescription: Grok\n---\n")
    (claude_skill_dir / "SKILL.md").write_text("---\nname: shared-skill\ndescription: Shared\n---\n")

    (result,) = query_harness_skills(agent_ids=("grok",), home=tmp_path, repo_root=tmp_path)

    assert result.ok
    by_name = {entry.name: entry for entry in result.entries}
    assert set(by_name) == {"grok-only", "shared-skill"}
    assert by_name["grok-only"].path == str(grok_skill_dir)
    assert by_name["shared-skill"].raw_agents == ("Claude Code",)


def test_mirror_grok_skills_from_claude_symlinks_missing_entries(tmp_path):
    claude_skill_dir = tmp_path / ".claude" / "skills" / "demo-skill"
    claude_skill_dir.mkdir(parents=True)
    (claude_skill_dir / "SKILL.md").write_text("---\nname: demo-skill\ndescription: Demo\n---\n")

    mirrored = mirror_grok_skills_from_claude(home=tmp_path)

    dest = tmp_path / ".grok" / "skills" / "demo-skill"
    assert mirrored == 1
    assert dest.is_symlink()
    assert dest.resolve() == claude_skill_dir.resolve()


def test_skills_cli_agent_id_maps_grok_to_claude_code():
    assert skills_cli_agent_id("grok") == "claude-code"
    assert skills_cli_agent_id("codex") == "codex"


def test_collect_installed_inventory_counts_queried_harness_with_stale_cli_label(tmp_path):
    root = tmp_path / "repo"
    home = tmp_path / "home"
    skill_dir = home / ".agents" / "skills" / "demo-installed-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: demo-installed-skill\ndescription: Demo\n---\n")

    curated_entries = parse_external_skill_entries(
        """
        ## Install Now After Trust Gate

        ```bash
        npx skills add example/installed-skills --skill demo-installed-skill -y -g -a opencode
        ```
        """
    )

    def runner(cmd, **kwargs):
        return _completed(
            cmd,
            [
                {
                    "name": "demo-installed-skill",
                    "path": str(skill_dir),
                    "scope": "global",
                    "agents": ["Claude Code"],
                }
            ],
        )

    snapshot = collect_installed_inventory(
        agent_ids=("opencode",),
        root=root,
        home=home,
        runner=runner,
        external_entries=curated_entries,
    )

    by_name = {row.name: row for row in snapshot.rows}
    assert by_name["demo-installed-skill"].installed_agents == ("claude-code", "opencode")


def test_query_grok_harness_includes_repo_project_skills(tmp_path):
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    global_skill = home / ".grok" / "skills" / "shared-skill"
    project_skill = repo / ".grok" / "skills" / "shared-skill"
    global_skill.mkdir(parents=True)
    project_skill.mkdir(parents=True)
    (global_skill / "SKILL.md").write_text("---\nname: shared-skill\ndescription: Global\n---\n", encoding="utf-8")
    (project_skill / "SKILL.md").write_text("---\nname: shared-skill\ndescription: Project\n---\n", encoding="utf-8")

    (result,) = query_harness_skills(agent_ids=("grok",), home=home, repo_root=repo)

    assert result.ok
    by_name = {entry.name: entry for entry in result.entries}
    assert by_name["shared-skill"].scope == "project"
    assert by_name["shared-skill"].path == str(project_skill)


def test_repo_skill_exposure_owner_prefers_codex_plugin_when_enabled(tmp_path):
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    config = home / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text('[plugins."agents@agents"]\nenabled = true\n', encoding="utf-8")

    assert repo_skill_exposure_owner_for_agent("codex", home=home, root=repo) == EXPOSURE_OWNER_PLUGIN

    config.write_text('[plugins."agents@agents"]\nenabled = false\n', encoding="utf-8")

    assert repo_skill_exposure_owner_for_agent("codex", home=home, root=repo) == "skills-cli"


def test_merge_local_skill_roots_into_query_adds_internal_skills(tmp_path):
    home = tmp_path / "home"
    internal_dir = home / ".cursor" / "skills" / "skill-registry-lock"
    internal_dir.mkdir(parents=True)
    (internal_dir / "SKILL.md").write_text(
        "---\n"
        "name: skill-registry-lock\n"
        "description: Internal scaffold\n"
        "metadata:\n"
        "  internal: true\n"
        "---\n\n"
        "# Skill Registry Lock\n",
        encoding="utf-8",
    )

    query = HarnessQueryResult(agent_id="cursor", ok=True, entries=())
    merged = _merge_local_skill_roots_into_query(query, home=home)
    names = {entry.name for entry in merged.entries}
    assert "skill-registry-lock" in names


@pytest.mark.parametrize(("agent_id", "label"), [("gemini-cli", "Gemini CLI"), ("github-copilot", "GitHub Copilot")])
def test_merge_local_skill_roots_scans_universal_agents_root_for_cli_shared_harnesses(
    tmp_path,
    agent_id: str,
    label: str,
) -> None:
    home = tmp_path / "home"
    skill_dir = home / ".agents" / "skills" / "skill-registry-lock"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: skill-registry-lock\ndescription: Internal scaffold\n---\n\n# Skill Registry Lock\n",
        encoding="utf-8",
    )

    query = HarnessQueryResult(agent_id=agent_id, ok=True, entries=())
    merged = _merge_local_skill_roots_into_query(query, home=home)
    (entry,) = [item for item in merged.entries if item.name == "skill-registry-lock"]

    assert entry.queried_agent == agent_id
    assert entry.path == str(skill_dir)
    assert entry.raw_agents == (label,)


def test_repo_skill_exposure_owner_prefers_opencode_direct_repo_path(tmp_path):
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    (repo / "skills").mkdir(parents=True)
    (repo / "opencode.json").write_text('{"skills": {"paths": ["skills"]}}', encoding="utf-8")

    assert repo_skill_exposure_owner_for_agent("opencode", home=home, root=repo) == EXPOSURE_OWNER_DIRECT_REPO_PATH


def test_collect_skill_cleanup_exposures_marks_repo_symlink_removed_when_plugin_owned(tmp_path):
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    _write_skill(repo / "skills" / "demo-skill", "demo-skill")
    codex_config = home / ".codex" / "config.toml"
    codex_config.parent.mkdir(parents=True)
    codex_config.write_text('[plugins."agents@agents"]\nenabled = true\n', encoding="utf-8")
    codex_skill_root = home / ".codex" / "skills"
    codex_skill_root.mkdir(parents=True)
    (codex_skill_root / "demo-skill").symlink_to(repo / "skills" / "demo-skill", target_is_directory=True)

    exposures = collect_skill_cleanup_exposures(root=repo, home=home)
    (exposure,) = [item for item in exposures if item.name == "demo-skill" and item.harness == "codex"]

    assert exposure.repo_owned is True
    assert exposure.canonical_owner == EXPOSURE_OWNER_PLUGIN
    assert exposure.cleanup_action == CLEANUP_ACTION_REMOVE_GENERATED_SYMLINK


def test_collect_skill_cleanup_exposures_classifies_duplicate_bodies(tmp_path):
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    _write_skill(repo / "skills" / "same-realpath", "same-realpath")
    for root in (home / ".claude" / "skills", home / ".grok" / "skills"):
        root.mkdir(parents=True)
        (root / "same-realpath").symlink_to(repo / "skills" / "same-realpath", target_is_directory=True)

    _write_skill(home / ".claude" / "skills" / "same-body", "same-body", "Shared")
    _write_skill(home / ".grok" / "skills" / "same-body", "same-body", "Shared")
    _write_skill(home / ".claude" / "skills" / "divergent-body", "divergent-body", "One")
    _write_skill(home / ".grok" / "skills" / "divergent-body", "divergent-body", "Two")

    exposures = collect_skill_cleanup_exposures(root=repo, home=home)
    by_name = {}
    for exposure in exposures:
        by_name.setdefault(exposure.name, []).append(exposure)

    assert {item.duplicate_class for item in by_name["same-realpath"]} == {DUPLICATE_CLASS_SAME_REALPATH}
    assert {item.duplicate_class for item in by_name["same-body"]} == {DUPLICATE_CLASS_SAME_BODY}
    divergent = by_name["divergent-body"]
    assert {item.duplicate_class for item in divergent} == {DUPLICATE_CLASS_DIVERGENT_BODY}
    assert {item.cleanup_action for item in divergent} == {CLEANUP_ACTION_MANUAL_REVIEW}
    assert {item.cleanup_action for item in by_name["same-body"]} == {CLEANUP_ACTION_PRESERVE}


def test_collect_skill_cleanup_exposures_hashes_nested_behavior_files(tmp_path):
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    for root, script_body in (
        (home / ".claude" / "skills" / "nested-diff", "print('claude')\n"),
        (home / ".grok" / "skills" / "nested-diff", "print('grok')\n"),
    ):
        _write_skill(root, "nested-diff", "Shared")
        scripts_dir = root / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "check.py").write_text(script_body, encoding="utf-8")

    exposures = collect_skill_cleanup_exposures(root=repo, home=home)
    nested = [item for item in exposures if item.name == "nested-diff"]

    assert {item.duplicate_class for item in nested} == {DUPLICATE_CLASS_DIVERGENT_BODY}
    assert {item.cleanup_action for item in nested} == {CLEANUP_ACTION_MANUAL_REVIEW}


@pytest.mark.parametrize(
    ("cache_head", "expected_action", "expected_risk"),
    (
        ("", CLEANUP_ACTION_REFRESH_PLUGIN_CACHE, "approval-required"),
        ("a" * 40, CLEANUP_ACTION_NONE, "none"),
        ("b" * 40, CLEANUP_ACTION_REFRESH_PLUGIN_CACHE, "approval-required"),
    ),
)
def test_build_skill_cleanup_report_classifies_codex_plugin_cache_heads(
    tmp_path,
    monkeypatch,
    cache_head,
    expected_action,
    expected_risk,
):
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    repo.mkdir()
    cache = home / ".codex" / "plugins" / "cache" / "agents" / "agents" / "local"
    config = home / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text('[plugins."agents@agents"]\nenabled = true\n', encoding="utf-8")
    repo_head = "a" * 40

    def fake_git_head(path):
        if path == repo:
            return repo_head
        if path == cache:
            return cache_head
        return ""

    monkeypatch.setattr("wagents.installed_inventory._git_head", fake_git_head)

    report = build_skill_cleanup_report(root=repo, home=home)
    plugins = report.get("plugins", [])
    assert isinstance(plugins, list)
    (codex_row,) = [row for row in plugins if isinstance(row, dict) and row.get("harness") == "codex"]
    codex_row = cast("dict[str, Any]", codex_row)

    assert codex_row["cleanup_action"] == expected_action
    assert codex_row["risk"] == expected_risk
    assert codex_row["installed_state"] == {"cache_head": cache_head[:12], "repo_head": repo_head[:12]}


def test_load_installed_skill_supersession_aliases_reads_config(tmp_path):
    repo = tmp_path / "repo"
    config_dir = repo / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "skill-installed-supersession.json").write_text(
        json.dumps({"aliases": {"stale-skill": "verified-skill"}}),
        encoding="utf-8",
    )

    assert load_installed_skill_supersession_aliases(repo_root=repo) == {
        "stale-skill": "verified-skill",
    }


def test_load_installed_skill_supersession_aliases_returns_empty_when_missing(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    assert load_installed_skill_supersession_aliases(repo_root=repo) == {}
