---
skill: agentic-actions-auditor
source_type: curated-external
researched_at: '2026-06-16T20:00:00Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Audits GitHub Actions workflows for AI agent security vulnerabilities specific to integrations like Claude Code Action, Gemini CLI, OpenAI Codex, and GitHub AI Inference. Detects 9 attack vectors (env var intermediary, direct ${{}} injection, gh CLI data fetch at runtime, pull_request_target+checkout, error log injection, subshell bypass, eval of AI output, dangerous sandboxes like --yolo, wildcard allowlists). From Trail of Bits skills marketplace.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode (per install). Activates automatically on detection of relevant .github/workflows YAML containing AI agent actions; also direct invocation.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=High impact CI context abuse and injection if workflows integrate AI agents with write perms; focus is detection not exploitation. Review triggers, allowed tools, and env flows before trusting in prod repos. policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `inspect-then-install` batch for trailofbits/skills in config/external-skills.md; live repo https://github.com/trailofbits/skills (5.7k stars, CC-BY-SA-4.0, security research org).

## Install Prerequisites

Install: `npx skills add trailofbits/skills --skill agentic-actions-auditor -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named. Best with .github/ workflows present. Run external-skill-auditor first per policy.

## Upstream Maintainer

[trailofbits/skills](https://github.com/trailofbits/skills) — security-focused plugin marketplace and skills for Claude Code / agent harnesses. See also related static-analysis, variant-analysis, differential-review plugins.

## Comparable Alternatives

`differential-review` for security PR/diff analysis with history; `static-analysis` (codeql/semgrep) or `insecure-defaults` for other vuln classes; general `honest-review`. A general-purpose agent instruction without a scoped skill contract for GitHub Actions AI agent security audits.

> Web evidence from github.com/trailofbits/skills README + plugin/agentic-actions-auditor/README.md + SKILL structure (fetched 2026-06); cross-ref config/external-skills.md. Evidence only; not an endorsement.
