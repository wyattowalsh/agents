---
skill: codeql
source_type: curated-external
researched_at: '2026-06-16T20:01:00Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Deep security vulnerability scanning using CodeQL's interprocedural data flow and taint tracking. Supports Python, JS/TS, Go, Java/Kotlin, C/C++, C#, etc. Builds databases, creates custom data extension models for project APIs, selects/runs query packs (security-extended + Trail of Bits + community), outputs SARIF. Workflows for quality assessment, build fixes, and result processing. From Trail of Bits static-analysis plugin (Testing Handbook based).

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. Employs Bash/Read/Write/Edit/Glob/Grep + task tools for multi-phase DB build/extensions/analysis. Integrated with semgrep/sarif agents in plugin.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Heavy resource use (full DB builds can take time/memory); build quality critical (LoC/extractor errors); macOS Apple Silicon arm64e mismatches (exit 137, needs Rosetta/Homebrew); noisy/false-neg without data extensions; requires external `codeql` binary. Zero findings must be investigated. policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated trailofbits/skills inspect-then-install group in config/external-skills.md + https://github.com/trailofbits/skills (static-analysis plugin).

## Install Prerequisites

Install: `npx skills add trailofbits/skills --skill codeql --skill semgrep --skill property-based-testing -y -g -a ...` (grouped); pre-install CodeQL CLI. status=inspect-then-install; selector=named. Use after auditor for build/CLI surface.

## Upstream Maintainer

[trailofbits/skills](https://github.com/trailofbits/skills) (static-analysis by Axel Mierczuk & Paweł Płatek). References Testing Handbook (appsec.guide).

## Comparable Alternatives

`semgrep` for fast pattern/triage scans; `variant-analysis` to hunt similar bugs from findings; `insecure-defaults` for config issues. General SAST or `static-analysis` instruction.

> Web evidence from github raw SKILL.md (plugins/static-analysis/skills/codeql/SKILL.md), plugin README, repo main README (2026). + config. Evidence only.
