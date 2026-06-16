---
skill: rust-mcp-server-generator
source_type: curated-external
researched_at: '2026-06-16T08:38:00Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

awesome-copilot / MCP ecosystem skill for scaffolding production-ready Rust MCP servers (tools, logging, config, transport). Generates server code that exposes capabilities to AI agents via MCP.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; GitHub curated; generates executable server code (security surface: auth, sandbox, input sanitization, resource access); generated code must be audited before running; high leverage but high responsibility.

## Install Prerequisites

Install: via github/awesome-copilot or MCP generators; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install; do not run generated servers without review.

## Upstream Maintainer

github/awesome-copilot and MCP community generators

## Comparable Alternatives

Other MCP server generators (python, TS, go); general Rust CLI / server scaffolding skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.
