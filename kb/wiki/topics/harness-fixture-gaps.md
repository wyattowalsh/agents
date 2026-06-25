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
updated: 2026-06-24
source_count: 4
---

# Harness Fixture Gaps

## Scope

This page records what should not be over-claimed about harness support and where fixtures or compose checks still fail to prove end-to-end projection.

## Summary

The repo supports many harnesses, but support tiers and fixture coverage differ. `planning/manifests/harness-fixture-support.json` marks many surfaces as fixture-plan-only or docs-ledger-required, so the KB should not imply every harness projection is fully validated end to end.

**2026-06-24 snapshot:**
- Platform adapters under `wagents/platforms/` coexist with `scripts/sync_agent_stack.py`; both paths matter for sync claims.
- Executable rollback tests live in `tests/test_harness_rollback_fixtures.py`: symlink `.bak` backup/restore via `ensure_symlink`, config-drop negative tests, Cursor home MCP merge-preservation and project CLI full-replace idempotency (`cursor_rollback`), and Grok TOML merge-preservation (`grok_rollback`). `planning/manifests/harness-fixture-support.json` marks `rollback_coverage: present` for claude-code, codex, cursor-editor, cursor-cli, grok-build, github-copilot-cli, and opencode; `cursor-bugbot` and `cursor-acp` remain `planned`.
- Docs compose is 100% (397/397); Cursor hook compose gap closed in Phase 4.
- Codex plugin `agents` path restored.
- **2026-06-24 plan fixtures:** Copilot CLI (`merge_copilot_config`) and Gemini MCP (`render_gemini_mcp`) promoted to `fixture-executable` via `tests/test_harness_plan_fixtures.py`.
- **2026-06-24 grok promotion:** `grok-build` promoted to `fixture-executable` using `tests/test_grok_platform.py`, grok slices of `test_sync_agent_stack.py`, and `test_grok_rollback_merge_preserves_user_owned_tables` in `test_harness_rollback_fixtures.py`.
- **2026-06-24 Cursor lane (all surfaces):** All six Cursor harness rows are `fixture-executable`. `cursor-editor` and `cursor-cli` are **`validated`** with rollback fixtures; `cursor-bugbot` and `cursor-acp` stay **`repo-present-validation-required`** until cursor-specific rollback proof lands (`rollback: planned`). `cursor-cloud-agent` and `cursor-cloud-subagent` are **`repo-present-validation-required`** with repo-owned project surfaces and documented dashboard/OAuth/Admin API out-of-scope caveats. Manifest `notes[]` carries executable success copy; `promotion_blocker` stays gap-oriented. Adapter: `wagents/platforms/cursor.py`.
- Remaining fixture gaps are non-Cursor plan-only harnesses (claude-desktop, cherry-studio, crush, etc.).

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