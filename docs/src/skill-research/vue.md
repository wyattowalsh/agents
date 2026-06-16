---
skill: vue
source_type: curated-external
researched_at: '2026-06-16T08:36:25Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

Vue.js core skill covering reactivity, components, Composition API. Generated from vuejs/docs. Unopinionated with focus on modern (TS, ESM, Composition). Part of comprehensive Vue/Vite one-stop in antfu/skills. Marked inspect-then-install in catalog.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

Curated mostly install-now-after-trust-gate / curated-trust-gated (except vue which is inspect-then-install). MIT. High-quality maintainer (Anthony Fu, core contributor to Vite/Vitest/Vue ecosystem). 5.3k stars. Skills generated/synced from official upstream docs where possible (except hand-maintained antfu and vendored slidev). Config provenance verified-install-command for listed. For vue specifically: needs-inspection per catalog (reason not expanded in web evidence; may relate to scope of generated Vue core skill or overlap).

## Install Prerequisites

`npx skills add antfu/skills --skill vue -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`. status=inspect-then-install; selector=named (or source-spec for some).

## Upstream Maintainer

antfu (Anthony Fu, github.com/antfu/skills). 5.3k stars. MIT (skills/scripts); vendored retain upstream licenses. Proof-of-concept using git submodules + sync from official docs (vuejs, vitejs, vitest-dev, slidevjs etc.) for reliable/up-to-date context. Primarily Vite/Nuxt ecosystem focus. POC; author welcomes feedback on real-world performance.

## Comparable Alternatives

nuxt, pinia, vueuse-functions, vue-best-practices (same source); other framework core skills.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.
