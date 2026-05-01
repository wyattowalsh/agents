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
updated: 2026-05-01
source_count: 16
---

# Known Risks And Open Gaps

## Current Risks

| Risk | Status | Why it matters | Next action |
|------|--------|----------------|-------------|
| Dirty worktree | Observed | There were many modified and untracked files before KB creation; unrelated user work must be preserved. | Do not infer repo health from this KB; inspect diffs before future code changes. |
| Local secret-looking MCP area | Gap | `mcp/secrets/` was identified as a sensitive local area and was not ingested. | Keep pointer-only; never capture secret values into KB. |
| `agent-bundle.json` description drift | Gap | Bundle description says `agents/` is reserved, while inventory found eight agent definitions and public generated docs publish agents. | Reconcile source text, tests, docs rendering, and plugin manifests in a future batch. |
| Full CI status unknown | Gap | This KB batch only runs targeted Nerdbot checks, not full CI. | Run full validation matrix separately when requested. |
| Docs/generated surfaces not exhaustively audited | Partial | README has a check path, but docs generation lacks a non-mutating check mode and at least one hand-maintained MCP docs count appears stale. | Use [[docs-generation-and-site]] and add a docs check/freshness gate before making public docs claims. |
| External standards are context-only | Observed | External docs were fetched as pointer-summary source notes; repo-local files still govern repo behavior. | Keep [[external-primary-source-map]] marked contextual and avoid treating upstream docs as local authority. |
| Non-Markdown vault assets skipped | Intentional | Current session allowed Markdown mutations only. | Add CSS snippets or other non-Markdown assets only in a later approved execution context. |
| OpenCode generated/canonical tension | Gap | `opencode.json` is repo-managed canonical config while some sync surfaces are generated or merged; ownership must be checked before edits. | Use [[canonical-generated-surfaces]] and [[opencode-runtime-policy]] before touching OpenCode config. |
| Sync rollback completeness | Gap | Sync transaction safety is documented but full rollback coverage is not proven for every path. | Use [[sync-transaction-safety]] and run targeted tests before claiming rollback guarantees. |
| Harness fixture coverage | Gap | Fixture/support-tier coverage is not proven for every harness projection. | Use [[harness-fixture-gaps]] before changing sync support tiers. |
| Planning ledger freshness | Partial | Planning manifests record drift and fixture requirements, but they are snapshots and do not prove the current worktree or live config still matches. | Re-run targeted distribution metadata tests before promoting planning claims into support guarantees. |
| OpenSpec archive state can drift from task state | Gap | Active change tasks may be checked before archive readiness evidence and archive execution are complete. | Use [[openspec-change-archive-status]] before any archive or release-readiness claim. |
| Risk-adjusted skill eval adequacy | Gap | Eval presence is uneven, and some higher-risk integration skills lack eval coverage by current research. | Use [[skill-catalog-risk-and-eval-coverage]] before treating eval counts as sufficient. |
| Agent publication drift | Gap | Bundle metadata, generated docs, plugin manifests, docs artifact registry, and platform-specific agent corpora do not fully agree. | Use [[agent-publication-and-drift-coverage]] before changing agent publication behavior. |

## Recommended Follow-Ups

1. Reconcile `agent-bundle.json` wording about `agents/` with actual tracked agent definitions.
2. Run full repo health commands only if the parent user asks for CI/quality status.
3. Add deeper source notes for concrete `wagents/platforms/*.py` implementations if a future sync change targets those files.
4. Expand harness fixtures/support-tier validation before changing projection ownership or generated config behavior.
5. Re-run README/docs freshness checks before making public docs claims, and add a docs generation check mode if docs freshness becomes release-blocking.
6. Keep [[planning-corpus-and-drift-ledgers]] updated when sync manifests, harness fixtures, or drift ledgers change.
7. Archive OpenSpec task-complete changes only after checklist evidence and validation/status commands pass.
8. Add eval coverage for higher-risk skills before raising confidence in risk-adjusted coverage.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Worktree was dirty and branch was ahead by one at inventory time. | `kb/raw/captures/local-inventory-summary.md` | raw capture | Derived from git status tool output. |
| `mcp/secrets/` is sensitive and should not be ingested. | `kb/raw/sources/code-surface-inventory.md`; local inventory result | raw source note | Pointer-only treatment. |
| `agent-bundle.json` currently describes `agents/` as reserved while local inventory found agent files. | `kb/raw/sources/agent-bundle-and-sync.md`; `kb/raw/sources/code-surface-inventory.md` | raw source notes | Drift candidate. |
| Nerdbot recommends pointer stubs for secret-looking or unsafe sources. | `kb/raw/sources/nerdbot-skill-contract.md` | raw source note | Safety model. |
| External upstream docs are captured as contextual source notes, not authoritative repo policy. | `kb/raw/sources/external-agent-skill-docs.md`; `kb/raw/sources/external-harness-docs.md`; `kb/raw/sources/external-tooling-docs.md`; `kb/raw/sources/external-obsidian-markdown-docs.md` | external source notes | Context-only. |
| Sync rollback, generated-surface ownership, and harness fixture coverage remain explicit gaps. | `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/tests-and-validation.md`; `kb/raw/sources/opencode-policy-and-runtime-plugins.md` | raw source notes | Follow-up queue. |
| Planning manifests capture sync inventory, drift state, fixture blockers, and support promotion constraints. | `kb/raw/sources/planning-corpus-drift-source.md` | raw source note | Snapshot evidence, not a live support guarantee. |
| Active OpenSpec changes require archive-readiness evidence beyond checked task boxes before archive execution. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Agents-platform archive completed later in `841b9b1`. |
| Agent publication drift spans bundle metadata, generated docs, plugin manifests, and platform-specific agent corpora. | `kb/raw/sources/agent-publication-drift-coverage.md` | raw source note | Drift map. |
| Skill eval coverage should be interpreted relative to skill risk. | `kb/raw/sources/skill-catalog-risk-eval-coverage.md` | raw source note | Eval adequacy gap. |
| Docs artifact freshness includes registry coverage gaps and stale hand-maintained derived counts. | `kb/raw/sources/docs-artifact-freshness.md` | raw source note | Docs health remains partial. |
