from wagents.external_skills import parse_external_skill_entries


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

- `vercel-labs/skills@find-skills`: duplicate of `discover-skills`.
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
    assert by_name["find-skills"].risk_notes == "duplicate of `discover-skills`."
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
