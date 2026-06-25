---
title: Crush Harness Policy Capture W22
tags:
  - kb
  - raw
  - crush
aliases:
  - Crush policy 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave22-pass3-stop-2026-06-25
---

# Crush Harness Policy Capture W22

Crush harness policy pointer on 2026-06-25 (pass 3 stop wave).

## Bridge

- Home: `AGENTS.md` → `@instructions/global.md` only.
- No Crush-specific global overlay file in `instructions/`.
- Skills CLI adapter includes `crush` in supported agents list.

## Fixture tier

`harness-fixture-support.json` record `crush`: `experimental` tier, `fixture-plan-only`, promotion blocked pending fixture coverage.

## Sync

Projected via `scripts/sync_agent_stack.py` platform list; no native `wagents/platforms/crush.py` adapter (delegator/thin surface per platform-adapters fleet capture).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Supported agents | `AGENTS.md` §6 | canonical repo |
| Fixture tier | `planning/manifests/harness-fixture-support.json` | canonical repo |
| Prior pointer | `kb/raw/sources/antigravity-crush-harness-capture-w16.md` | raw source |