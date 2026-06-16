---
skill: multi-stage-dockerfile
source_type: curated-external
researched_at: '2026-06-16T08:38:00Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

awesome-copilot skill providing guidance and patterns for writing secure, efficient multi-stage Dockerfiles: layer caching, minimal final images, non-root users, build vs runtime separation, secret handling in builds.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; GitHub curated; common, well-understood domain; lower risk than runtime tools; still inspect for org image policy and base image sources.

## Install Prerequisites

Install: `npx skills add github/awesome-copilot --skill multi-stage-dockerfile`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[github/awesome-copilot](https://github.com/github/awesome-copilot) (GitHub curated)

## Comparable Alternatives

General Dockerfile best practices or distroless skills; container security skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.
