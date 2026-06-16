---
skill: vite
source_type: curated-external
researched_at: '2026-06-16T08:36:25Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

Skill for Vite build tool: config, plugins, SSR, library mode. Generated from official vitejs/vite docs and fine-tuned. Unopinionated but modern-stack tilt (TS, ESM). Helps agents with Vite-powered projects in the broader antfu/Vite/Nuxt collection.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

Curated mostly install-now-after-trust-gate / curated-trust-gated (except vue which is inspect-then-install). MIT. High-quality maintainer (Anthony Fu, core contributor to Vite/Vitest/Vue ecosystem). 5.3k stars. Skills generated/synced from official upstream docs where possible (except hand-maintained antfu and vendored slidev). Config provenance verified-install-command for listed. For vue specifically: needs-inspection per catalog (reason not expanded in web evidence; may relate to scope of generated Vue core skill or overlap).

## Install Prerequisites

`npx skills add antfu/skills --skill vite -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`. status=install-now-after-trust-gate; selector=named (or source-spec for some).

## Upstream Maintainer

antfu (Anthony Fu, github.com/antfu/skills). 5.3k stars. MIT (skills/scripts); vendored retain upstream licenses. Proof-of-concept using git submodules + sync from official docs (vuejs, vitejs, vitest-dev, slidevjs etc.) for reliable/up-to-date context. Primarily Vite/Nuxt ecosystem focus. POC; author welcomes feedback on real-world performance.

## Comparable Alternatives

vitest, nuxt, pnpm (same source); other build-tool skills.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.
