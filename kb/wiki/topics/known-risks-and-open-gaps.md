---
title: Known Risks And Open Gaps
tags:
  - kb
  - risks
  - gaps
aliases:
  - Open gaps
  - Known risks
kind: overview
status: active
updated: 2026-06-25
source_count: 28
---

# Known Risks And Open Gaps

## Current Risks

| Risk | Status | Why it matters | Next action |
|------|--------|----------------|-------------|
| Dirty worktree | Historical (2026-06-23) | Snapshot in `kb/raw/captures/local-inventory-summary.md` showed unrelated changes outside `kb/`; post-ingest sessions may be clean — re-check `git status` before non-KB work. | Inspect diffs before non-KB code changes; do not infer repo health from KB alone. |
| Local secret-looking MCP area | Gap | `mcp/secrets/` is sensitive and was not ingested. | Keep pointer-only; never capture secret values into KB. |
| Agent publication drift | Resolved (2026-06-24) | Canonical eight now present in `platforms/copilot/agents/` plus five Copilot specialists; Codex plugin `agents` path restored. | Monitor via `tests/test_copilot_agents.py` and [[agent-publication-and-drift-coverage]]. |
| Full CI status unknown for this session | Gap | KB batch ran targeted Nerdbot lint/inventory, not full CI matrix. | Run `.github/workflows/ci.yml` locally or on PR when release-blocking. |
| Docs/generated surfaces partially audited | Resolved (2026-06-24) | Compose 100%; Cursor hook pages composed; MCP badge refreshed; `wagents docs generate --check` wired in CI. | Use [[docs-generation-and-site]] for ongoing freshness discipline. |
| External standards are context-only | Observed | External docs are pointer-summary source notes. | Keep [[external-primary-source-map]] contextual. |
| OpenCode generated/canonical tension | Gap | `opencode.json` is repo-managed while some sync surfaces are generated or merged. | Use [[canonical-generated-surfaces]] and [[opencode-runtime-policy]] before edits. |
| Sync rollback completeness | Gap | Config-drop and merge preservation exist; full merged-home rollback not proven. | Use [[sync-transaction-safety]] and [[wagents-platform-adapters]]. |
| Harness fixture coverage | Documented | 12 executable / 8 rollback-present per 2026-06-25 manifest; plan-only harnesses remain. | Use [[harness-fixture-gaps]] before raising support tiers. |
| Planning manifest freshness | Observed | Planning manifests are snapshots, not live config proof. | Re-run targeted tests before promotion claims. |
| OpenSpec archive state can drift | Documented | Validate 33/33 on 2026-06-25; 9 active / 53 archived dirs. | Use [[openspec-change-archive-status]] before bulk archives. |
| Risk-adjusted skill eval adequacy | Documented | 56/56 manifests; adequacy CLI 0 `needs_e4`; live eval runs still separate. | Use [[skill-catalog-risk-and-eval-coverage]]. |
| MCP docs badge drift | Gap | Badge shows 15 servers; registry has 33. | Fix `docs/src/content/docs/mcp/index.mdx` in repo/docs batch. |
| MCPHub topology changes | Partial | Registry, tunnel, and smart-routing surfaces documented in KB but not live-verified here. | Use [[mcphub-control-plane]] before topology edits. |

## Phase 4 Fix Candidates (repo, not KB)

Shipped 2026-06-23 through 2026-06-24 (commits `d4af41f`, `69e2d6e`, `5dc7ec1`, `00d064e`, `f242a5e`):

1. ~~Refresh stale MCP count badge~~ — done.
2. ~~Restore Codex plugin `agents` component~~ — done.
3. ~~Compose five missing Cursor hook docs pages~~ — done.
4. ~~Add `wagents docs generate --check` + CI enforcement~~ — done.
5. ~~Wire portable `openspec archive` CLI handler~~ — done.
6. ~~Reconcile Copilot agent corpus with canonical eight~~ — done (plus five Copilot specialists documented).

Remaining repo follow-ups outside this batch: skill eval coverage expansion, OpenSpec archive hygiene, harness fixture promotion.

## Recommended Follow-Ups

1. Run full CI or pre-commit slice when the parent user asks for release readiness.
2. Execute Phase 4 items as separate conventional commits, not mixed with KB-only work.
3. Add eval coverage for higher-risk skills before raising confidence in risk-adjusted coverage.
4. Archive OpenSpec task-complete changes only after checklist evidence and validation pass.
5. Keep [[planning-corpus-and-drift-ledgers]] updated when sync manifests or fixture ledgers change.
6. Re-run README/docs/catalog freshness checks before public docs claims.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Worktree dirty at 2026-06-23 enrichment start. | `kb/raw/captures/local-inventory-summary.md` | raw capture | Git snapshot. |
| `mcp/secrets/` is sensitive and should not be ingested. | `kb/raw/sources/code-surface-inventory.md` | raw source note | Pointer-only treatment. |
| Agent publication drift spans bundle, plugins, docs, platform corpora. | `kb/raw/sources/agent-publication-drift-coverage.md`; `kb/raw/sources/wagents-platform-adapters-source.md` | raw source notes | 2026-06-23 refresh. |
| Nerdbot recommends pointer stubs for secret-looking sources. | `kb/raw/sources/nerdbot-skill-contract.md` | raw source note | Safety model. |
| Sync rollback and fixture gaps remain explicit. | `kb/raw/sources/wagents-platform-adapters-source.md`; `kb/raw/sources/planning-corpus-drift-source.md` | raw source notes | Conservative posture. |
| OpenSpec active/archive snapshot and incomplete actives. | `kb/raw/sources/openspec-active-lifecycle-source.md` | raw source note | Validation not rerun. |
| Skill eval manifest count vs skill tree size. | `kb/raw/captures/local-inventory-summary.md`; `kb/raw/sources/skill-catalog-risk-eval-coverage.md` | raw capture; raw source note | 29/56. |
| Docs freshness gaps including MCP badge and compose holes. | `kb/raw/sources/docs-artifact-freshness.md` | raw source note | Fix candidates. |
| CI validates docs compose at 100% on PR/push. | `kb/raw/sources/ci-release-workflows-source.md` | raw source note | External gate exists. |
| MCPHub control plane documented from registry/scripts. | `kb/raw/sources/mcphub-control-plane-source.md` | raw source note | Topology reference. |

## Related

- [[docs-generation-and-site]]
- [[agent-publication-and-drift-coverage]]
- [[ci-and-release-workflows]]
- [[mcphub-control-plane]]