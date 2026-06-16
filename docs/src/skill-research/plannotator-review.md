---
skill: plannotator-review
source_type: curated-external
researched_at: '2026-06-16T06:01:40Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Install Plannotator core slash commands (`/plannotator-review`, `/plannotator-annotate`, `/plannotator-last`). Pair with `curl -fsSL https://plannotator.ai/install.sh | bash` or `uv run wagents grok plannotator install` for the `plannotator` CLI binary. Grok uses skills plus repo-synced hooks in `config/grok-plannotator-hooks.json`; there is no Grok npm plugin equivalent to OpenCode's `@plannotator/opencode`.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command; risks=Install Plannotator core slash commands (`/plannotator-review`, `/plannotator-annotate`, `/plannotator-last`). Pair with `curl -fsSL https://plannotator.ai/install.sh | bash` or `uv run wagents grok plannotator install` for the `plannotator` CLI binary. Grok uses skills plus repo-synced hooks in `config/grok-plannotator-hooks.json`; there is no Grok npm plugin equivalent to OpenCode's `@plannotator/opencode`.; policy=Install only after trust gate; audit again before repo promotion.; evidence=Curated `npx skills add` command with named `--skill` selectors under `install-now-after-trust-gate` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add backnotprop/plannotator/apps/skills/core --skill plannotator-review --skill plannotator-annotate --skill plannotator-last -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

backnotprop/plannotator/apps/skills/core

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.
