---
skill: biome-developer
source_type: curated-external
researched_at: '2026-06-16T08:45:57Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

biome-developer supplies internal best practices and gotchas for contributors working on the Biome (formatter/linter) codebase itself. It covers AST navigation, string extraction without allocation, embedded language handling, clippy/style rules (no emojis, let chains, path imports), dev-dependency path usage, comment guidelines, testing via quick_test, and common API confusion tables. Marked as compatibility: "Designed for coding agents working on the Biome codebase (github.com/biomejs/biome)."

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. The skill is scoped to Biome-repo development tasks; it is not a general "use Biome" user skill.

## Trust And Risks

install-now-after-trust-gate / curated-trust-gated. Official content maintained inside the biomejs/biome repository (under .claude/skills). Low risk for its intended narrow use (Biome contributors). For general projects, the content may be irrelevant or overly prescriptive (e.g., the strict no-emoji policy). Treat as repo-specific conventions.

## Install Prerequisites

`npx skills add biomejs/biome --skill biome-developer -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`

Intended to be used while editing the Biome monorepo; requires familiarity with Rust, the parser/analyzer crates, and the project's justfile test helpers.

## Upstream Maintainer

biomejs (https://github.com/biomejs/biome). Main site and docs: https://biomejs.dev/

## Comparable Alternatives

General Rust or web-tooling contributor guidelines; local project-specific AGENTS.md or CLAUDE.md files when not working inside the Biome repo.

> Evidence gathered from public GitHub (raw .claude/skills/biome-developer/SKILL.md and repo files). Not an endorsement or authority; this skill encodes Biome-project conventions only.
