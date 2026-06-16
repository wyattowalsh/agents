---
skill: code-review
source_type: curated-external
researched_at: '2026-06-16T08:35:46Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Expert code review skill. Part of PRB agent-skills collection (pinned commit d3f5540). Provides guidance for thorough code reviews, often paired with code-simplify and code-polish for combined simplification + review workflows. Designed primarily for Claude Code and Codex but portable.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

Curated install-now-after-trust-gate / curated-trust-gated using same pinned HEAD as cli-just audit. MIT. Repo-level warning applies: personal-optimized, do due diligence, no warranties. Per adjacent config note: TS workflow residual from the cli-just audit. Prior inspection of source indicated 26 skills exposed at that rev (slight variance in listing). Low stars (62) but from known maintainer. Inspect skill content for alignment with project review standards.

## Install Prerequisites

`npx skills add PaulRBerg/agent-skills@d3f5540ed2fc0fa07f802bd925e06b9387cbe90f --skill code-review -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` (often bundled with commit/vitest in audit). status=install-now-after-trust-gate; selector=named.

## Upstream Maintainer

PaulRBerg (github.com/PaulRBerg/agent-skills @d3f5540ed2fc0fa07f802bd925e06b9387cbe90f). MIT. Focus on personal dev workflows for Claude/Codex; references upstream skills ecosystem (vercel-labs).

## Comparable Alternatives

code-polish, code-simplify (same source); other review skills e.g. from getsentry or general differential-review; native agent review capabilities or CodeRabbit integration skill from same repo.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.
