import json
import subprocess
import sys

from wagents.external_skills import parse_external_skill_entries
from wagents.installed_inventory import (
    _run_harness_command,
    collect_installed_inventory,
    mirror_grok_skills_from_claude,
    query_harness_skills,
    skills_cli_agent_id,
)


def _completed(cmd, payload):
    return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")


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
    assert by_name["repo-skill"].install_source == "github:wyattowalsh/agents"
    assert by_name["repo-skill"].version == "1.2.3"

    assert by_name["curated-skill"].provenance_status == "verified-curated-external"
    assert by_name["curated-skill"].source == "vercel-labs/agent-skills"
    assert by_name["curated-skill"].installed_agents == ("claude-code", "codex")

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


def test_query_harness_skills_reports_timeout():
    def runner(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    (result,) = query_harness_skills(agent_ids=("claude-code",), runner=runner, timeout_sec=3)

    assert not result.ok
    assert result.error.startswith("Timed out after 3s:")


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
