import json
from pathlib import Path

import pytest

# Retargeted after discovery move to harness-master; dedupe string
# (historical duplicate-of discover-skills) is preserved as test data.
from wagents.external_skills import (
    ExternalSkillCatalogError,
    parse_external_skill_entries,
    read_external_skill_entries,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_authoring_mdx(
    authoring_dir: Path,
    name: str,
    *,
    install_command: str,
    sync_kind: str | None = "skills-cli",
    source: str = "owner/repo",
    install_source: str | None = None,
    status: str = "install-now-after-trust-gate",
    trust_tier: str = "curated-trust-gated",
    provenance_status: str = "verified-install-command",
    selector_mode: str = "named",
    target_agents: tuple[str, ...] = ("codex",),
) -> Path:
    install_source = install_source or source
    sync_kind_line = f"sync_kind: {sync_kind}\n" if sync_kind is not None else ""
    path = authoring_dir / f"{name}.mdx"
    targets = ", ".join(target_agents)
    path.write_text(
        f"""---
name: {name}
description: Demo curated skill.
source_kind: curated-external
source: {source}
install_source: {install_source}
status: {status}
trust_tier: {trust_tier}
provenance_status: {provenance_status}
source_url: https://github.com/{source}
target_agents: [{targets}]
{sync_kind_line}selector_mode: {selector_mode}
install_command: {install_command}
---

Audit notes.
""",
        encoding="utf-8",
    )
    return path


def _catalog_row(
    name: str = "demo-skill",
    *,
    source: str = "owner/repo",
    install_source: str | None = None,
    install_command: str | None = None,
    target_agents: list[str] | None = None,
    sync_kind: str = "skills-cli",
) -> dict[str, object]:
    install_source = install_source or source
    install_command = install_command or f"npx skills add {install_source} --skill {name} -y -g -a codex"
    return {
        "name": name,
        "description": "Generated row.",
        "sourceType": "curated-external",
        "sourceRoot": source,
        "installSource": install_source,
        "status": "install-now-after-trust-gate",
        "trustTier": "curated-trust-gated",
        "provenanceStatus": "verified-install-command",
        "targetAgents": target_agents or ["codex"],
        "selectorMode": "named",
        "syncKind": sync_kind,
        "installCommand": install_command,
    }


def _write_catalog_index(index_path: Path, rows: list[dict[str, object]]) -> None:
    index_path.write_text(json.dumps({"externalSkillIndex": rows}, indent=2), encoding="utf-8")


def test_parse_external_skill_entries_from_curated_markdown():
    entries = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add addyosmani/web-quality-skills --skill accessibility --skill performance -y -g -a codex claude-code
```

## Inspect Then Install

```bash
npx skills add openai/skills --skill security-best-practices -y -g -a codex
```

## Keep Global Only Or Avoid

- `vercel-labs/skills@find-skills`: duplicate of `harness-master` discover (systematic gap pipeline).
"""
    )

    by_name = {entry.name: entry for entry in entries}

    assert by_name["accessibility"].source == "addyosmani/web-quality-skills"
    assert by_name["accessibility"].install_source == "addyosmani/web-quality-skills"
    assert by_name["accessibility"].status == "install-now-after-trust-gate"
    assert by_name["accessibility"].target_agents == ("codex", "claude-code")
    assert by_name["accessibility"].provenance_status == "verified-install-command"
    assert (
        by_name["accessibility"].promotion_policy == "Install only after trust gate; audit again before repo promotion."
    )
    assert "named `--skill` selectors" in by_name["accessibility"].provenance_evidence
    assert by_name["security-best-practices"].trust_tier == "needs-inspection"
    assert by_name["security-best-practices"].promotion_policy.startswith("Inspect source")
    assert by_name["find-skills"].status == "global-only-or-avoid"
    assert by_name["find-skills"].provenance_status == "explicit-unresolved"
    assert by_name["find-skills"].source_url == "https://github.com/vercel-labs/skills"
    assert "harness-master" in by_name["find-skills"].risk_notes
    assert by_name["find-skills"].promotion_policy.startswith("Keep global-only")


def test_parse_external_skill_entries_supports_wildcards():
    entries = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add github:wyattowalsh/agents --skill "*" -y -g -a claude-code
```
"""
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.name == "wyattowalsh-agents-all"
    assert entry.source == "wyattowalsh/agents"
    assert entry.install_source == "github:wyattowalsh/agents"
    assert entry.selector_mode == "wildcard"
    assert entry.provenance_status == "verified-install-command"
    assert "wildcard" in entry.provenance_evidence


def test_parse_external_skill_entries_supports_source_specs():
    entries = parse_external_skill_entries(
        """
## Inspect Then Install

```bash
npx skills add docs.stripe.com@stripe-best-practices -y -g -a claude-code
```
"""
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.name == "stripe-best-practices"
    assert entry.source == "docs.stripe.com"
    assert entry.install_source == "docs.stripe.com@stripe-best-practices"
    assert entry.selector_mode == "source-spec"
    assert entry.source_url == "https://docs.stripe.com"
    assert "source-embedded skill selector" in entry.provenance_evidence


def test_parse_external_skill_entries_keeps_explicit_unresolved_rows():
    entries = parse_external_skill_entries(
        """
## Keep Global Only Or Avoid

- `docs.stripe.com@stripe-best-practices`: registry syntax and provenance still need verification.
"""
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.name == "stripe-best-practices"
    assert entry.source == "docs.stripe.com"
    assert entry.provenance_status == "explicit-unresolved"
    assert entry.unresolved_reason == "registry syntax and provenance still need verification."
    assert entry.risk_notes == "registry syntax and provenance still need verification."


def test_parse_external_skill_entries_attaches_adjacent_audit_notes_to_command_entries():
    entries = parse_external_skill_entries(
        """
## Inspect Then Install

```bash
npx skills add example/skills --skill demo --skill second -y -g -a codex
```

Install only after reviewing hooks and scripts. Avoid private credential-bearing URLs.
"""
    )

    by_name = {entry.name: entry for entry in entries}

    for name in ("demo", "second"):
        assert (
            by_name[name].notes
            == "Install only after reviewing hooks and scripts. Avoid private credential-bearing URLs."
        )
        assert (
            by_name[name].risk_notes
            == "Install only after reviewing hooks and scripts. Avoid private credential-bearing URLs."
        )
        assert "named `--skill` selectors" in by_name[name].provenance_evidence
        assert (
            by_name[name].promotion_policy == "Inspect source, hooks, scripts, credentials, and dedupe before install."
        )


def test_parse_external_skill_entries_dedupes_by_source_and_name_preferring_verified():
    entries = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add example/skills --skill demo -y -g -a codex
```

## Keep Global Only Or Avoid

- `example/skills@demo`: duplicate note.
"""
    )

    assert len(entries) == 1
    assert entries[0].name == "demo"
    assert entries[0].provenance_status == "verified-install-command"


def test_parse_external_skill_entries_flags_unsupported_target_agents():
    entries = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add example/skills --skill demo -y -g -a codex made-up-agent
```
"""
    )

    assert entries[0].unsupported_target_agents == ("made-up-agent",)


def test_parse_external_skill_entries_accepts_current_skills_cli_target_agents():
    entries = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add example/skills --skill demo -y -g -a codex windsurf augment openhands
```
"""
    )

    assert entries[0].unsupported_target_agents == ()


def test_read_external_skill_entries_prefers_authoring_over_stale_index(tmp_path, monkeypatch):
    authoring_dir = tmp_path / "authoring" / "skills"
    authoring_dir.mkdir(parents=True)
    _write_authoring_mdx(
        authoring_dir,
        "demo-skill",
        install_command="npx skills add owner/repo --skill demo-skill -y -g -a codex",
        sync_kind="skills-cli",
    )
    index_path = tmp_path / "skills-catalog-index.json"
    _write_catalog_index(
        index_path,
        [
            _catalog_row(
                install_command="pip install stale-demo",
                sync_kind="external-tool",
            )
        ],
    )
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", authoring_dir)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", index_path)

    entries = read_external_skill_entries()

    assert len(entries) == 1
    assert entries[0].install_command.startswith("npx skills add owner/repo")
    assert entries[0].sync_kind == "skills-cli"


def test_read_external_skill_entries_strict_rejects_stale_index_extra_row(tmp_path, monkeypatch):
    authoring_dir = tmp_path / "authoring" / "skills"
    authoring_dir.mkdir(parents=True)
    _write_authoring_mdx(
        authoring_dir,
        "demo-skill",
        install_command="npx skills add owner/repo --skill demo-skill -y -g -a codex",
    )
    index_path = tmp_path / "skills-catalog-index.json"
    _write_catalog_index(
        index_path,
        [
            _catalog_row(),
            _catalog_row(
                "stale-skill",
                source="owner/stale",
                install_command="npx skills add owner/stale --skill stale-skill -y -g -a codex",
            ),
        ],
    )
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", authoring_dir)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", index_path)

    with pytest.raises(ExternalSkillCatalogError, match=r"stale-skill.*docs generate"):
        read_external_skill_entries(strict=True)


def test_read_external_skill_entries_strict_rejects_index_mismatch(tmp_path, monkeypatch):
    authoring_dir = tmp_path / "authoring" / "skills"
    authoring_dir.mkdir(parents=True)
    _write_authoring_mdx(
        authoring_dir,
        "demo-skill",
        install_command="npx skills add owner/repo --skill demo-skill -y -g -a codex",
    )
    index_path = tmp_path / "skills-catalog-index.json"
    _write_catalog_index(
        index_path,
        [
            _catalog_row(
                install_command="npx skills add owner/repo --skill demo-skill -y -g -a claude-code",
                target_agents=["claude-code"],
            )
        ],
    )
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", authoring_dir)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", index_path)

    with pytest.raises(ExternalSkillCatalogError, match=r"mismatched index rows.*demo-skill"):
        read_external_skill_entries(strict=True)


def test_read_external_skill_entries_strict_accepts_public_grok_command_normalization(tmp_path, monkeypatch):
    authoring_dir = tmp_path / "authoring" / "skills"
    authoring_dir.mkdir(parents=True)
    _write_authoring_mdx(
        authoring_dir,
        "demo-skill",
        install_command="npx skills add owner/repo --skill demo-skill -y -g -a codex grok",
        target_agents=("codex", "grok"),
    )
    index_path = tmp_path / "skills-catalog-index.json"
    _write_catalog_index(
        index_path,
        [
            _catalog_row(
                install_command="npx skills add owner/repo --skill demo-skill -y -g -a codex",
                target_agents=["codex", "grok"],
            )
        ],
    )
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", authoring_dir)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", index_path)

    entries = read_external_skill_entries(strict=True)

    assert entries[0].target_agents == ("codex", "grok")


def test_read_external_skill_entries_falls_back_to_index_without_authoring(tmp_path, monkeypatch):
    authoring_dir = tmp_path / "authoring" / "skills"
    authoring_dir.mkdir(parents=True)
    index_path = tmp_path / "skills-catalog-index.json"
    _write_catalog_index(index_path, [_catalog_row()])
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", authoring_dir)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", index_path)

    entries = read_external_skill_entries(strict=True)

    assert [entry.name for entry in entries] == ["demo-skill"]


def test_read_external_skill_entries_strict_rejects_missing_sync_kind(tmp_path, monkeypatch):
    authoring_dir = tmp_path / "authoring" / "skills"
    authoring_dir.mkdir(parents=True)
    _write_authoring_mdx(
        authoring_dir,
        "demo-skill",
        install_command="npx skills add owner/repo --skill demo-skill -y -g -a codex",
        sync_kind=None,
    )
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", authoring_dir)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", tmp_path / "missing-index.json")

    with pytest.raises(ExternalSkillCatalogError, match="sync_kind"):
        read_external_skill_entries(strict=True)


def test_read_external_skill_entries_strict_rejects_global_only_install_command(tmp_path, monkeypatch):
    authoring_dir = tmp_path / "authoring" / "skills"
    authoring_dir.mkdir(parents=True)
    _write_authoring_mdx(
        authoring_dir,
        "avoid-skill",
        install_command="npx skills add owner/repo --skill avoid-skill -y -g -a codex",
        sync_kind="none",
        status="global-only-or-avoid",
        trust_tier="global-only-or-avoid",
        provenance_status="explicit-unresolved",
        selector_mode="unresolved",
    )
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", authoring_dir)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", tmp_path / "missing-index.json")

    with pytest.raises(ExternalSkillCatalogError, match="must leave 'install_command' empty"):
        read_external_skill_entries(strict=True)


def test_read_external_skill_entries_strict_reports_bad_authoring(tmp_path, monkeypatch):
    authoring_dir = tmp_path / "authoring" / "skills"
    authoring_dir.mkdir(parents=True)
    bad_file = authoring_dir / "bad.mdx"
    bad_file.write_text("not frontmatter", encoding="utf-8")
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", authoring_dir)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", tmp_path / "missing-index.json")

    with pytest.raises(ExternalSkillCatalogError, match=str(bad_file)):
        read_external_skill_entries(strict=True)


def test_read_external_skill_entries_strict_reports_bad_index_but_default_uses_authoring(tmp_path, monkeypatch):
    authoring_dir = tmp_path / "authoring" / "skills"
    authoring_dir.mkdir(parents=True)
    _write_authoring_mdx(
        authoring_dir,
        "demo-skill",
        install_command="npx skills add owner/repo --skill demo-skill -y -g -a codex",
    )
    index_path = tmp_path / "skills-catalog-index.json"
    index_path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", authoring_dir)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", index_path)

    assert [entry.name for entry in read_external_skill_entries()] == ["demo-skill"]
    with pytest.raises(ExternalSkillCatalogError, match=str(index_path)):
        read_external_skill_entries(strict=True)


def test_curated_plannotator_entries_include_grok_target():
    entries = read_external_skill_entries()
    by_name = {entry.name: entry for entry in entries}

    for skill_name in (
        "plannotator-review",
        "plannotator-annotate",
        "plannotator-last",
        "plannotator-compound",
        "plannotator-setup-goal",
        "plannotator-visual-explainer",
    ):
        assert skill_name in by_name, f"missing curated entry for {skill_name}"
        assert "grok" in by_name[skill_name].target_agents

    for extra in ("plannotator-compound", "plannotator-setup-goal", "plannotator-visual-explainer"):
        entry = by_name[extra]
        assert "apps/skills" in entry.source
        assert "apps/skills" in entry.install_command
        assert "backnotprop/plannotator --skill" not in entry.install_command


def test_curated_shadcn_install_now_is_folded_into_design():
    from wagents.external_skills import desired_install_now_entries

    shadcn_install_rows = [
        entry
        for entry in desired_install_now_entries()
        if entry.name == "shadcn" or ("shadcn" in entry.install_command and "--skill shadcn" in entry.install_command)
    ]
    assert shadcn_install_rows == []


def test_plannotator_extras_sync_command_uses_apps_skills_path():
    from wagents.cli import PLANNOTATOR_EXTRAS_SYNC_COMMAND

    assert "backnotprop/plannotator/apps/skills" in PLANNOTATOR_EXTRAS_SYNC_COMMAND
    root_only = [part for part in PLANNOTATOR_EXTRAS_SYNC_COMMAND if part == "backnotprop/plannotator"]
    assert root_only == []
