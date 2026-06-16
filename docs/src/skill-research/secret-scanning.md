---
skill: secret-scanning
source_type: curated-external
researched_at: '2026-06-16T08:38:00Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

awesome-copilot skill for GitHub secret scanning: configuring push protection, custom patterns, secret alert remediation, pre-commit scanning in agent workflows. Helps agents avoid leaking creds in code and PRs.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; GitHub curated (leverages official GH secret scanning features); low conceptual risk; inspect for custom pattern sensitivity and alert routing.

## Install Prerequisites

Install: `npx skills add github/awesome-copilot --skill secret-scanning`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[github/awesome-copilot](https://github.com/github/awesome-copilot) (GitHub curated)

## Comparable Alternatives

Other secret detection (gitleaks, trufflehog) skills; `gha-security-review`; pre-commit security skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.
