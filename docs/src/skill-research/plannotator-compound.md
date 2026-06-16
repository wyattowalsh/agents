---
skill: plannotator-compound
source_type: curated-external
researched_at: '2026-06-16T08:42:12Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

Optional Plannotator extra for compound planning analysis. Part of user-facing extras in apps/skills (not root). Complements core Plannotator skills for compound/structured planning workflows, goal setup, and visual explanations of plans. Installed as optional extras via the curated apps/skills subpath.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. Grouped install command bundles the three plannotator-* extras together with core prerequisites.

## Trust And Risks

Curated install-now-after-trust-gate / curated-trust-gated. Low public footprint in search (repo structure evidence only). Provenance via verified npx command with named selectors and explicit notes on subpath vs root. Extras are optional; compound planning, setup-goal, visual explainer. Must have core installed. Risks center on path selection (root vs apps/skills) to avoid internal/maintainer skills; review generated planning artifacts.

## Install Prerequisites

`npx skills add backnotprop/plannotator/apps/skills --skill plannotator-compound --skill plannotator-setup-goal --skill plannotator-visual-explainer -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`. status=install-now-after-trust-gate; selector=named (group). Notes: requires core Plannotator skills/CLI; do not use root path.

## Upstream Maintainer

backnotprop (github.com/backnotprop/plannotator/apps/skills). Skills under apps/skills/extra per structure. Config explicitly warns: do not install from repo root (exposes maintainer-only skills: pierre-guard, release-plannotator, review-renovate, update-deps). Use the apps/skills path for user-facing extras. Requires core Plannotator skills/CLI first.

## Comparable Alternatives

Core Plannotator skills (required prerequisite); other planning/roadmap or goal-setting skills (e.g. create-implementation-plan, brainstorm variants); general agent planning or visual explainer skills; native agent task decomposition without Plannotator-specific extras.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.
