import json
import subprocess

from wagents.external_skills import parse_external_skill_entries
from wagents.installed_inventory import collect_installed_inventory


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
            payload.append(
                {
                    "name": "curated-skill",
                    "path": str(curated_skill_dir),
                    "scope": "global",
                    "agents": ["Codex", "Claude Code"],
                }
            )
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


def test_collect_installed_inventory_counts_queried_harness_with_stale_cli_label(tmp_path):
    root = tmp_path / "repo"
    home = tmp_path / "home"
    skill_dir = home / ".agents" / "skills" / "ui-ux-pro-max"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: ui-ux-pro-max\ndescription: UI UX\n---\n")

    curated_entries = parse_external_skill_entries(
        """
        ## Install Now After Trust Gate

        ```bash
        npx skills add nextlevelbuilder/ui-ux-pro-max-skill --skill ui-ux-pro-max -y -g -a opencode
        ```
        """
    )

    def runner(cmd, **kwargs):
        return _completed(
            cmd,
            [
                {
                    "name": "ui-ux-pro-max",
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
    assert by_name["ui-ux-pro-max"].installed_agents == ("claude-code", "opencode")
