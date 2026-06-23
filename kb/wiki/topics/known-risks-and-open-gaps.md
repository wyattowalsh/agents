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
updated: 2026-06-23
source_count: 22
---

# Known Risks And Open Gaps

## Current Risks

| Risk | Status | Why it matters | Next action |
|------|--------|----------------|-------------|
| Dirty worktree | Observed | Unrelated modified and untracked files outside `kb/` remain; KB enrichment must stay additive. | Inspect diffs before non-KB code changes; do not infer repo health from KB alone. |
| Local secret-looking MCP area | Gap | `mcp/secrets/` is sensitive and was not ingested. | Keep pointer-only; never capture secret values into KB. |
| Agent publication drift | Partial | Eight canonical agents under `agents/`; bundle lists `./agents/`; Codex plugin files missing; Copilot corpus has 11 files with partial overlap. | Use [[agent-publication-and-drift-coverage]]; fix in separate repo batch. |
| Full CI status unknown for this session | Gap | KB batch ran targeted Nerdbot lint/inventory, not full CI matrix. | Run `.github/workflows/ci.yml` locally or on PR when release-blocking. |
| Docs/generated surfaces partially audited | Partial | Compose 98.2%; five Cursor hook pages missing; MCP index badge stale; no `wagents docs generate --check`. | Use [[docs-generation-and-site]]; fix candidates below. |
| External standards are context-only | Observed | External docs are pointer-summary source notes. | Keep [[external-primary-source-map]] contextual. |
| OpenCode generated/canonical tension | Gap | `opencode.json` is repo-managed while some sync surfaces are generated or merged. | Use [[canonical-generated-surfaces]] and [[opencode-runtime-policy]] before edits. |
| Sync rollback completeness | Gap | Config-drop and merge preservation exist; full merged-home rollback not proven. | Use [[sync-transaction-safety]] and [[wagents-platform-adapters]]. |
| Harness fixture coverage | Gap | Rollback fixtures mostly `planned`; Codex plugin paths missing; compose hook gap. | Use [[harness-fixture-gaps]] before raising support tiers. |
| Planning manifest freshness | Partial | Planning manifests are snapshots, not live config proof. | Re-run targeted tests before promotion claims. |
| OpenSpec archive state can drift | Partial | ~32 active / ~28 archived; four actives with unchecked tasks; portable CLI lacks `archive` subcommand. | Use [[openspec-change-archive-status]]. |
| Risk-adjusted skill eval adequacy | Gap | 29/56 skills have `evals/evals.json`; many R3/R4 workflows lack E3/E4 coverage. | Use [[skill-catalog-risk-and-eval-coverage]]. |
| MCPHub topology changes | Partial | Registry, tunnel, and smart-routing surfaces documented in KB but not live-verified here. | Use [[mcphub-control-plane]] before topology edits. |

## Phase 4 Fix Candidates (repo, not KB)

Documented here for a separate atomic fix batch outside `kb/`:

1. Refresh stale MCP count badge in `docs/src/content/docs/mcp/index.mdx`.
2. Add or restore missing Codex plugin manifest files referenced by harness registry/tests.
3. Compose the five missing Cursor hook docs pages (registry rows without MDX).
4. Add `wagents docs generate --check` or extend docs artifact registry coverage.
5. Implement or wire portable `openspec archive` CLI handler if SKILL dispatch should remain truthful.
6. Reconcile Copilot agent corpus size/names with canonical eight agents (if publication parity is required).

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