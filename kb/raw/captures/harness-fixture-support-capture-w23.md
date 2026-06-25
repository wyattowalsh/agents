---
title: Harness Fixture Support Capture W23
tags:
  - kb
  - raw
  - harness
aliases:
  - Harness fixture support 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave23-pass4-2026-06-25
---

# Harness Fixture Support Capture W23

Snapshot of `planning/manifests/harness-fixture-support.json` on 2026-06-25.

## Summary

- **records**: 19 harness surfaces
- **refs**: `config/harness-surface-registry.json`, `config/support-tier-registry.json`

## Support tiers

| Tier | Count |
|------|-------|
| repo-present-validation-required | 15 |
| validated | 2 |
| experimental | 2 |

## Fixture status

| Status | Count |
|--------|-------|
| fixture-executable | 12 |
| fixture-plan-only | 4 |
| docs-ledger-required | 3 |

## Harness IDs (19)

antigravity, chatgpt, cherry-studio, claude-code, claude-desktop, codex, crush, cursor-acp, cursor-bugbot, cursor-cli, cursor-cloud-agent, cursor-cloud-subagent, cursor-editor, gemini-cli, github-copilot-cli, github-copilot-web, grok-build, opencode, perplexity-desktop

## Record shape

Each record includes `harness_id`, `owner_change`, `current_support_tier`, `fixture_status`, `fixture_classes[]`, `validation_commands[]`, `rollback_coverage`, `promotion_blocker`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Counts | JSON parse of manifest | tool output |
| Prior gap page | `kb/wiki/topics/harness-fixture-gaps.md` | wiki synthesis |