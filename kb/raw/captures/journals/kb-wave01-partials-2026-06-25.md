---
title: "Research journal — KB wave 01"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 01 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave01-partials-2026-06-25
original_location: "~/.grok/research/kb-wave01-partials-2026-06-25.md"
---

# Research journal — KB wave 01

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 01 | Theme: partial topics refresh
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 01 — partial topics refresh`

## G0 brief

Fresh command captures for six formerly-partial wiki topics; coverage index now zero `partial` rows for those pages.

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `agent-pub-drift-capture-w01` | `kb/raw/captures/agent-pub-drift-capture-w01.md` |
| worker | `docs-freshness-capture-w01` | `kb/raw/captures/docs-freshness-capture-w01.md` |
| worker | `harness-fixture-capture-w01` | `kb/raw/captures/harness-fixture-capture-w01.md` |
| worker | `openspec-lifecycle-capture-w01` | `kb/raw/captures/openspec-lifecycle-capture-w01.md` |
| worker | `skill-eval-inventory-capture-w01` | `kb/raw/captures/skill-eval-inventory-capture-w01.md` |
| worker | `sync-rollback-capture-w01` | `kb/raw/captures/sync-rollback-capture-w01.md` |

## Ingest queue

- `raw`: added 6 captures (`skill-eval-inventory-capture-w01`, `docs-freshness-capture-w01`, `sync-rollback-capture-w01`, `openspec-lifecycle-capture-w01`, `agent-pub-drift-capture-w01`, `harness-fixture-capture-w01`).

## Capture evidence (excerpts)

### `agent-pub-drift-capture-w01`

# Agent Publication Drift Capture W01

Read-only agent publication inventory on 2026-06-25.

## Corpus counts

| Surface | Count | Path |
|---------|-------|------|
| Canonical portable agents | 9 | `agents/*.md` |
| Copilot projected agents | 14 | `platforms/copilot/agents/*.md` |
| Composed docs agent pages | 8 | `docs/src/content/docs/agents/` (per prior KB; compose 8/8) |

## Drift notes

- Copilot corpus includes canonical eight by name plus Copilot-only specialists (documented in `platforms/copilot/agents/README.md`).
- Codex plugin `plugin.json` components list empty in current read — verify against `.codex-plugin/plugin.json` and bundle metadata before claiming plugin agent projection.
- Cursor overlays from `config/cursor-agents.json` add `readonly`/`model` fields beyond portable frontmatter.

## KB posture

Document projection surfaces and dialect differences; coordinated reconciliation of bundle, tests, docs compose, and platform corpora remains a separate repo fix batch.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Agent file counts | `agents/`, `platforms/copilot/agents/` | repo read |
| Publication map | `kb/raw/sources/agent-publication-drift-coverage.md` | prior KB source |

### `docs-freshness-capture-w01`

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

### `harness-fixture-capture-w01`

# Harness Fixture Capture W01

Read-only harness fixture support snapshot on 2026-06-25.

## Manifest summary (`planning/manifests/harness-fixture-support.json`)

| Metric | Value |
|--------|-------|
| Harness records | 19 |
| `fixture-executable` | 12 |
| `rollback_coverage: present` | 8 |
| `rollback_coverage: planned` | 8 |

## Executable rollback pytest surface

`tests/test_harness_rollback_fixtures.py` — 8 collected tests (Cursor home MCP merge, Cursor CLI idempotency, Grok merge preservation, config-drop negatives, symlink `.bak` paths).

## Docs compose (related fixture gate)

397/397 composed (100%) including 22 hook pages — prior Cursor hook compose gap closed.

## Remaining plan-only harnesses (examples)

`claude-desktop`, `cherry-studio`, `chatgpt`, `github-copilot-web` — fixture-plan-only or docs-ledger-required per manifest rows.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Fixture tiers | `planning/manifests/harness-fixture-support.json` | canonical repo path |
| Rollback tests | `tests/test_harness_rollback_fixtures.py` | canonical repo path |
| Compose gate | `wagents docs compose --check-composed` | tool capture |

### `openspec-lifecycle-capture-w01`

# OpenSpec Lifecycle Capture W01

Read-only OpenSpec lifecycle snapshot on 2026-06-25.

## Validation

```
uv run wagents openspec validate
→ 33/33 items passed (8 changes, 25 specs)
```

## Directory counts

| Bucket | Count | Path |
|--------|-------|------|
| Active changes | 9 | `openspec/changes/<name>/` (non-archive) |
| Archived changes | 53 | `openspec/changes/archive/` |

## Active change IDs (validation set)

`add-new-project-skill`, `compose-harness-catalog-pages`, `consolidate-review-skill`, `enhance-skill-creator-lifecycle`, `integrate-apm-package-manager`, `integrate-mcphub-control-plane`, `public-release-prod-readiness`, `upgrade-design-skill` (plus 25 specs).

## State distinctions

Task-complete, validation-passing, archive-ready, and archived remain separate states. Bulk 2026-06-24 archives reduced active set; remaining actives include integration and release-readiness waves with open tasks.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Validate JSON summary | `wagents openspec validate` | tool capture |
| Archive dirs | filesystem under `openspec/changes/archive/` | repo read |

### `skill-eval-inventory-capture-w01`

# Skill Eval Inventory Capture W01

Read-only capture from `uv run wagents eval adequacy --format json` on 2026-06-25. Not an instruction source.

## Captured Facts

| Metric | Value | Command |
|--------|-------|---------|
| Skills with eval manifests | 56/56 | `wagents eval adequacy` |
| High-risk skills (R3/R4) | 14 | same |
| Skills flagged `needs_e4` | 0 | same |
| Structural adequacy at E4 for high-risk set | 14/14 | JSON `adequacy` field |

## Quoted CLI excerpt

> `"count": 56` — all repo skills returned in adequacy report.

> High-risk examples include `email-whiz` (R4, adequacy E4), `mcp-creator` (R4, E4), chrome-devtools family (R3, E4).

## Interpretation

Manifest presence is saturated; structural adequacy CLI reports no remaining `needs_e4` skills. Live LLM eval execution and per-skill boundary depth remain separate from this structural gate.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Adequacy counts | `wagents eval adequacy --format json` | tool capture |
| Risk tiers | `wagents/eval_adequacy.py` | canonical repo path |

### `sync-rollback-capture-w01`

# Sync Rollback Capture W01

Read-only capture of sync transaction safety posture on 2026-06-25.

## Implemented (code-backed)

| Control | Surface | Notes |
|---------|---------|-------|
| Dry/check mode | `SyncContext(apply=False)` | Preview without live writes |
| Config-drop refusal | `ConfigDropError` | Blocks merged renders that drop local keys |
| Merge preservation | platform adapters + `sync_agent_stack.py` | User-owned MCP/hook tables preserved on merge paths |
| Symlink `.bak` backup | rollback fixture tests | Backup on symlink replacement |

## Not proven end-to-end

| Gap | Why it matters |
|-----|----------------|
| Full merged-home snapshot restore | `~/.codex/config.toml`, `~/.cursor/mcp.json`, etc. lack proven one-shot rollback |
| Live home config vendoring | Out of scope per goal interview; metadata captures only |

## Executable rollback tests (pytest collect)

`tests/test_harness_rollback_fixtures.py` — 8 cases including Cursor home MCP merge preservation, Cursor CLI idempotency, Grok TOML merge preservation.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Transaction registry policy | `config/config-transaction-registry.json` | canonical repo path |
| Adapter merge behavior | `wagents/platforms/*`, `scripts/sync_agent_stack.py` | canonical repo paths |
| Rollback tests | `tests/test_harness_rollback_fixtures.py` | canonical repo path |


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 6**; pages enriched: 7; lint: pass (exit 0).

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
