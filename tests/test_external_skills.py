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
    assert by_name["security-best-practices"].trust_tier == "needs-inspection"
    assert by_name["find-skills"].status == "global-only-or-avoid"
    assert by_name["find-skills"].provenance_status == "explicit-unresolved"
    assert by_name["find-skills"].source_url == "https://github.com/vercel-labs/skills"


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
