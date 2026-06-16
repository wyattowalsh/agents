---
skill: web-quality-audit
source_type: curated-external
researched_at: '2026-06-16T08:36:02Z'
research_tier: standard
mean_confidence: 0.77
---

## Purpose

Comprehensive quality review orchestrator across Performance, Accessibility, SEO, Best Practices, and Core Web Vitals. Uses Lighthouse guidelines. Triggered by phrases like "audit my site", "lighthouse audit". Checks 50+ perf patterns, 40+ a11y rules, 30+ SEO reqs, 20+ security/best-practice patterns + all CWV. Recommended when unsure which sub-area to target or for full-site audits.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

Curated install-now-after-trust-gate / curated-trust-gated. MIT licensed. Source by addyosmani (Chrome DevTools / web performance expert) with 2.4k GitHub stars. Unofficial collection encoding wisdom from 150+ Lighthouse audits, real-world perf engineering, WCAG 2.2, modern SEO. Stack-agnostic (React/Vue/Svelte/Next/Nuxt/Astro/plain). Skills activate on matching prompts. No specific per-skill hooks noted in config; provenance via verified npx command. Popular, reputable maintainer reduces baseline risk; still follow general audit-before-promotion guidance.

## Install Prerequisites

`npx skills add addyosmani/web-quality-skills --skill web-quality-audit --skill accessibility --skill seo --skill performance --skill core-web-vitals --skill best-practices -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode. status=install-now-after-trust-gate; selector=named (group install supports multiple). Supports Claude plugin, Codex marketplace, Gemini extensions, manual copy.`

## Upstream Maintainer

addyosmani (github.com/addyosmani/web-quality-skills). MIT License. Insights from Chrome DevTools team, web perf experts, a11y advocates. 2.4k stars, 216 forks. Resources link to Lighthouse, web.dev, WCAG, Agent Skills spec.

## Comparable Alternatives

Other skills in same bundle (e.g. performance, core-web-vitals, accessibility, seo, best-practices); general Lighthouse/web.dev guidance; framework-specific perf/a11y plugins; other curated quality skills like chrome-devtools-*.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.
