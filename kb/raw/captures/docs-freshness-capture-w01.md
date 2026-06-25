---
title: Docs Freshness Capture W01
tags:
  - kb
  - raw
  - docs
  - inventory
aliases:
  - Docs compose capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave01-partials-2026-06-25
---

# Docs Freshness Capture W01

Read-only docs freshness capture on 2026-06-25.

## Captured Facts

| Check | Result | Evidence |
|-------|--------|----------|
| Compose coverage | 397/397 (100%) | `uv run wagents docs compose --check-composed --min-pct 100` |
| Hooks composed | 22/22 | compose breakdown |
| Skills composed | 363/363 | compose breakdown |
| CI docs generate check | present | `.github/workflows/ci.yml` runs `wagents docs generate --no-installed --check` |
| CI compose gate | 100% minimum | same workflow |
| MCP index badge | **stale** — "15 configured servers" | `docs/src/content/docs/mcp/index.mdx` |
| MCP registry server count | 33 | `config/mcp-registry.json` `servers` map |

## Quoted badge text

> `<Badge text="15 configured servers" variant="note" size="large" />`

## Remaining gap

Hand-maintained MCP landing badge disagrees with MCPHub registry cardinality; update is a repo/docs fix, not a KB blocker once documented.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Compose 100% | `wagents docs compose --check-composed` | tool capture |
| Generate --check in CI | `.github/workflows/ci.yml` | canonical repo path |
| Badge vs registry drift | MCP index MDX vs mcp-registry.json | repo read |