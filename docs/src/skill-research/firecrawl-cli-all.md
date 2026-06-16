---
skill: firecrawl-cli-all
source_type: curated-external
researched_at: '2026-06-16T08:36:15Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

Firecrawl CLI skill bundle for live web capabilities inside agents: search, scrape single URLs, map site structure, crawl for bulk content, browser automation, structured extraction to LLM-friendly markdown/JSON. Enables agents to fetch fresh external data without leaving the editor/terminal.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection (global-only/avoid per catalog); status=global-only or avoid; provenance=verified-install-command; source=firecrawl (web scraping startup); provides live internet access to agents (cost, rate limits, ToS, potential data exfil or untrusted content injection risks). Rationale for global-only/avoid likely: broad web surface can be abused or incur unexpected usage; prefer scoped per-project install or explicit opt-in. Evidence: firecrawl.dev blog posts, GitHub firecrawl/cli, skill registry listings, CLI docs.

## Install Prerequisites

Install (per listings): `npx skills add firecrawl/cli --skill firecrawl-cli-all` (or named selectors); may require API key / login; global-only per catalog rationale summary; policy=Inspect for usage policy, auth, and cost exposure before global or broad install.

## Upstream Maintainer

[firecrawl/cli](https://github.com/firecrawl/cli) (Firecrawl team)

## Comparable Alternatives

Other web-scrape/fetch skills (e.g. browserless, puppeteer skills); built-in search tools in some agents; tavily or similar search MCP/tools.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.
