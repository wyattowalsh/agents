---
skill: golang-spf13-viper
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Extended `samber/cc-skills-golang` row for Go depth beyond the original six-skill subset. Keep `golang-google-wire`, `golang-uber-fx`, `golang-uber-dig`, and `golang-samber-do` global-only unless explicitly requested.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Extended `samber/cc-skills-golang` row for Go depth beyond the original six-skill subset. Keep `golang-google-wire`, `golang-uber-fx`, `golang-uber-dig`, and `golang-samber-do` global-only unless explicitly requested.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add samber/cc-skills-golang --skill golang-concurrency --skill golang-testing --skill golang-security --skill golang-how-to --skill golang-observability --skill golang-grpc --skill golang-error-handling --skill golang-cli --skill golang-spf13-cobra --skill golang-spf13-viper --skill golang-lint --skill golang-benchmark --skill golang-performance --skill golang-stretchr-testify --skill golang-database --skill golang-graphql --skill golang-project-layout --skill golang-modernize --skill golang-troubleshooting --skill golang-safety --skill golang-popular-libraries -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[samber/cc-skills-golang](https://github.com/samber/cc-skills-golang)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.
