---
skill: playwright-cli
source_type: curated-external
researched_at: '2026-06-16T08:42:44Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Official microsoft/playwright-cli. CLI (with SKILL) for common Playwright browser actions: open/goto/type/click/fill/screenshot/pdf/eval, tabs, storage, network route, tracing, video, sessions, dashboard. Token-efficient (avoids full a11y trees). For coding agents (better than MCP for some high-throughput cases per README). Node 18+. Headed/persistent options.

## Harness Coverage

curated agents.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; official Microsoft/Playwright team; browser automation surface (file upload, net, js eval on page); requires node; use for test/automation only in scoped contexts.

## Install Prerequisites

npx skills add microsoft/playwright-cli --skill playwright-cli -y -g -a [agents]; npm global or npx; status=inspect-then-install.

## Upstream Maintainer

[microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) (official).

## Comparable Alternatives

playwright-best-practices (curated internal); puppeteer/selenium skills.

> Evidence from GitHub (mcp-use, microsoft, neondatabase 2026) + catalog; research evidence only - not authority or endorsement.
