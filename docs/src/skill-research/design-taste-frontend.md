---
skill: design-taste-frontend
source_type: curated-external
researched_at: '2026-06-16T08:35:15Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Taste Skill is the Anti-Slop Frontend Framework for AI Agents. The "design-taste-frontend" skill (primary install name for the taste-skill v2) upgrades AI-generated interfaces with stronger layout, typography, motion, and spacing instead of generic boilerplate UIs. It reads the brief, infers design language, tunes dials (VARIANCE / MOTION / DENSITY), applies design-system mapping, enforces anti-repetition (hard em-dash ban), provides canonical GSAP code skeletons, redesign-audit protocols, and strict pre-flight checks. The repo also ships specialized variants and companion image-generation skills for producing reference boards (web/mobile/brand) to feed into coding agents like Codex, Cursor, or Claude Code. Framework-agnostic (React/Vue/Svelte/etc.).

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. Installed via explicit --skill selector plus -a agent list in the curated command.

## Trust And Risks

Status inspect-then-install (trust_tier=needs-inspection) because the bundle substantially overlaps local design/image-generation workflows. Repo has strong public adoption (44.8k stars), MIT license, active maintainer (Leonxlnx / @lexnlin), sponsor support, and no observed hooks in the primary skill frontmatter per prior audit. However, source exposes 12 skills including style variants, full-output-enforcement, stitch-design-taste, and multiple imagegen-* skills; config directs keeping most variants global-only unless explicitly requested. v2 is experimental with substantial rewrite; review CHANGELOG and generated recipes for currency. Popular OSS project; inspect before install to avoid duplication and confirm current behavior.

## Install Prerequisites

`npx skills add Leonxlnx/taste-skill --skill design-taste-frontend -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`

Curated status=inspect-then-install; selector=named. Re-install upgrades v1->v2 in place (install name unchanged). Pin to design-taste-frontend-v1 if exact legacy behavior required. Supports copy of SKILL.md or paste into agents.

## Upstream Maintainer

Leonxlnx (github.com/Leonxlnx/taste-skill; tasteskill.dev). X: @lexnlin, @blueemi99. MIT License (Copyright 2026 Leonxlnx). High-visibility project (44.8k stars, 3.1k forks). Disclaimer: no official token/crypto. Feedback via GitHub issues/PRs, DM, or hello@tasteskill.dev. Research notes in repo research/ dir.

## Comparable Alternatives

Same-source variants (e.g. minimalist-ui, high-end-visual-design, gpt-taste, redesign-existing-projects, image-to-code); other curated frontend/UX skills (e.g. from web-quality or design-agent skills); general agent instructions for UI/UX without scoped contract; or direct use of design systems + image reference pipelines.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.
