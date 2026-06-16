---
skill: plannotator-review
source_type: curated-external
researched_at: '2026-06-16T08:45:57Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Plannotator-review launches a browser-based code-review UI (PR-style diff viewer) over the current worktree or an optional PR URL. The skill runs `plannotator review [optional-pr-url]`, waits for annotations or approval feedback, and acts on the returned comments. Intended for visual review of agent-written code changes using familiar diff tooling instead of raw terminal output.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. `disable-model-invocation: true`; delegates review surface to the external tool.

## Trust And Risks

Curated-trust-gated under install-now-after-trust-gate. Thin launcher for the plannotator binary; risks are CLI execution, local filesystem access for the worktree diff, and browser UI. Supports optional public PR URLs. Project is open source, locally runnable, and promoted for agent workflows. Companion hooks exist for Grok. Perform binary and hook inspection consistent with other plannotator skills.

## Install Prerequisites

Requires the plannotator CLI binary plus the core skill install:
`npx skills add backnotprop/plannotator/apps/skills/core --skill plannotator-review ...`
Pair with the CLI install script and optional grok hooks.

## Upstream Maintainer

backnotprop (https://github.com/backnotprop/plannotator). Project site and install: https://plannotator.ai/

## Comparable Alternatives

Terminal diff review inside agent; GitHub PR review flows; other visual diff or diagram skills for high-level views.

> Evidence gathered from public GitHub sources, raw SKILL.md, and project site (plannotator.ai). Not an endorsement or authority; inspect the CLI binary, hooks, and network behavior before use.
