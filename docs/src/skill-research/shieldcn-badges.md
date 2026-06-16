---
skill: shieldcn-badges
source_type: curated-external
researched_at: '2026-06-16T06:01:40Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Install `shieldcn-badges` from `jal-co/shieldcn` for local badge-generation workflows. The source at audited HEAD `55daa08d15c92dab7f443facd55a91b8c914c78d` exposes one skill, has MIT licensing, and no observed hooks, command substitutions, `allowed-tools`, or skill-local scripts; keep usage scoped to README/docs badge generation. Dynamic JSON badge patterns can embed arbitrary external JSON endpoints in documentation, so avoid adding badges for private or secret-bearing URLs. The command intentionally enumerates observed local Skills CLI adapters instead of using `--all`; current Skills CLI installs these adapters through the universal `~/.agents/skills/shieldcn-badges` root and symlinks Crush.

## Harness Coverage

Target agents: adal, antigravity, augment, bob, claude-code, cline, codearts-agent, codebuddy, codemaker, codestudio, codex, command-code, continue, cortex, crush, cursor, devin, droid, forgecode, gemini-cli, github-copilot, goose, hermes-agent, iflow-cli, junie, kilo, kiro-cli, kode, mcpjam, mistral-vibe, mux, neovate, opencode, openhands, pi, pochi, qoder, qwen-code, rovodev, roo, tabnine-cli, trae, trae-cn, warp, windsurf, zencoder.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command; risks=Install `shieldcn-badges` from `jal-co/shieldcn` for local badge-generation workflows. The source at audited HEAD `55daa08d15c92dab7f443facd55a91b8c914c78d` exposes one skill, has MIT licensing, and no observed hooks, command substitutions, `allowed-tools`, or skill-local scripts; keep usage scoped to README/docs badge generation. Dynamic JSON badge patterns can embed arbitrary external JSON endpoints in documentation, so avoid adding badges for private or secret-bearing URLs. The command intentionally enumerates observed local Skills CLI adapters instead of using `--all`; current Skills CLI installs these adapters through the universal `~/.agents/skills/shieldcn-badges` root and symlinks Crush.; policy=Install only after trust gate; audit again before repo promotion.; evidence=Curated `npx skills add` command with named `--skill` selectors under `install-now-after-trust-gate` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add jal-co/shieldcn --skill shieldcn-badges -y -g -a adal antigravity augment bob claude-code cline codearts-agent codebuddy codemaker codestudio codex command-code continue cortex crush cursor devin droid forgecode gemini-cli github-copilot goose hermes-agent iflow-cli junie kilo kiro-cli kode mcpjam mistral-vibe mux neovate opencode openhands pi pochi qoder qwen-code rovodev roo tabnine-cli trae trae-cn warp windsurf zencoder` status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

[jal-co/shieldcn](https://github.com/jal-co/shieldcn)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.
