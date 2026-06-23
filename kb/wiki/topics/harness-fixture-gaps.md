---
title: Harness Fixture Gaps
tags:
  - kb
  - harness-sync
  - gaps
aliases:
  - Fixture gaps
kind: concept
status: partial
updated: 2026-06-23
source_count: 4
---

# Harness Fixture Gaps

## Scope

This page records what should not be over-claimed about harness support and where fixtures or compose checks still fail to prove end-to-end projection.

## Summary

The repo supports many harnesses, but support tiers and fixture coverage differ. `planning/manifests/harness-fixture-support.json` marks many surfaces as fixture-plan-only or docs-ledger-required, so the KB should not imply every harness projection is fully validated end to end.

**2026-06-23 snapshot:**
- Platform adapters under `wagents/platforms/` (cursor, codex, grok, opencode, copilot, gemini, vscode) coexist with the legacy `scripts/sync_agent_stack.py` monolith; both paths must be considered when claiming sync coverage.
- Rollback fixtures in the harness fixture manifest remain mostly `planned`, not executable proof.
- Docs compose manifest reports 98.2% composed (381/388); five missing pages are Cursor hooks present in `config/hook-registry.json` but without composed MDX.
- Codex plugin manifest paths (`.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`) are referenced in registry/tests but missing on disk — a publication/fixture gap distinct from portable agent files under `agents/`.
- CI enforces `wagents docs compose --check-composed --min-pct 100` in the docs job; local KB work did not rerun that gate.

Future harness work should name the exact surface being changed, the registry row or sync manifest row backing it, the fixture/test that verifies it, and the rollback path for any live config mutation.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Harness support has varied support tiers and fixture status. | `kb/raw/sources/config-registries-and-sync.md` | raw source note | Avoid over-claiming. |
| Some adapters are placeholders while legacy sync remains active. | `kb/raw/sources/config-registries-and-sync.md` | raw source note | Implementation gap. |
| Fixture support rows include fixture classes, validation commands, rollback status, and promotion blockers. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Planning manifest keeps support claims conservative. |
| Platform adapter dual-path sync and rollback fixtures mostly planned. | `kb/raw/sources/wagents-platform-adapters-source.md` | raw source note | 2026-06-23 research. |
| Compose coverage gap: five Cursor hook pages missing from composed docs. | `kb/raw/sources/docs-artifact-freshness.md` | raw source note | 98.2% compose snapshot. |
| CI docs job runs compose check at 100% minimum. | `kb/raw/sources/ci-release-workflows-source.md` | raw source note | Fixture gate exists in CI. |

## Related

- [[harness-and-platform-sync]]
- [[wagents-platform-adapters]]
- [[sync-transaction-safety]]
- [[planning-corpus-and-drift-ledgers]]
- [[docs-generation-and-site]]
- [[known-risks-and-open-gaps]]