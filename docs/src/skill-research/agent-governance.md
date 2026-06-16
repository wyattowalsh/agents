---
skill: agent-governance
source_type: curated-external
researched_at: '2026-06-16T08:37:12Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

GitHub awesome-copilot skill: patterns and techniques for adding governance, safety, and trust controls to AI agent systems. Covers policy-based access, semantic intent classification for dangerous prompts, trust scoring, audit trails for tool-using agents.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; source=github/awesome-copilot (GitHub-curated collection of community + patterns); guidance for building safer agents; high conceptual value but abstract policies may need customization; no direct exec surface.

## Install Prerequisites

Install: `npx skills add github/awesome-copilot --skill agent-governance --skill agent-owasp-compliance --skill agent-supply-chain --skill agentic-eval --skill arize-evaluator --skill arize-instrumentation --skill arize-prompt-optimization --skill create-implementation-plan -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` (or subset); status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[github/awesome-copilot](https://github.com/github/awesome-copilot) (GitHub curated)

## Comparable Alternatives

Other safety/governance or OWASP-for-LLM skills; mcp-security-audit; general agent policy skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.
