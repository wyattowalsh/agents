---
title: Config Registry Crosswalk Capture W24
tags:
  - kb
  - raw
  - config
aliases:
  - Config registry crosswalk 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave24-pass4-2026-06-25
---

# Config Registry Crosswalk Capture W24

Cross-registry inventory under `config/` on 2026-06-25 (explicit paths only).

| Registry file | Primary role | Approx row count |
|---------------|--------------|------------------|
| `mcp-registry.json` | MCPHub SSOT for managed MCP servers | 33 servers |
| `hook-registry.json` | Logical hook definitions | 22 hooks |
| `harness-surface-registry.json` | Per-harness surface tiers | (see w03 capture) |
| `hook-surface-registry.json` | Hook tier projection | (see w03 capture) |
| `sync-manifest.json` | Managed sync records | 90 records (w17) |
| `support-tier-registry.json` | Tier vocabulary | 7 tiers (w23) |
| `docs-artifact-registry.json` | Generated doc ownership | 14 artifacts (w23) |
| `cursor-agents.json` | Cursor subagent registry | 8 agents |

## Planning manifests (selected)

- `planning/manifests/harness-fixture-support.json` — 19 harness fixture records
- `planning/manifests/security-quarantine-register.json` — curated skill blocklist for validate

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| MCP count | `config/mcp-registry.json` | canonical repo |
| Hook count | `config/hook-registry.json` | canonical repo |
| Sync count | `kb/raw/captures/sync-manifest-snapshot-capture-w17.md` | raw capture |