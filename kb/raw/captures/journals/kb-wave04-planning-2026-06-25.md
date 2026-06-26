---
title: "Research journal — KB wave 04"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 04 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave04-planning-2026-06-25
original_location: "~/.grok/research/kb-wave04-planning-2026-06-25.md"
---

# Research journal — KB wave 04

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 04 | Theme: planning manifests and OpenSpec active inventory
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 04 — planning manifests and OpenSpec active inventory`

## G0 brief

Read-only inventory of `openspec/changes/*` (8 actives, 53 archived) and `planning/manifests/*` (90-row sync/drift parity, harness fixture tiers, external-repo ledgers).

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `drift-ledger-capture-w04` | `kb/raw/captures/drift-ledger-capture-w04.md` |
| worker | `openspec-active-changes-capture-w04` | `kb/raw/captures/openspec-active-changes-capture-w04.md` |
| worker | `planning-sync-inventory-capture-w04` | `kb/raw/captures/planning-sync-inventory-capture-w04.md` |

## Ingest queue

- `raw`: added 3 captures (`openspec-active-changes-capture-w04`, `planning-sync-inventory-capture-w04`, `drift-ledger-capture-w04`).

## Capture evidence (excerpts)

### `drift-ledger-capture-w04`

# Drift Ledger Capture W04

Read-only `planning/manifests/repo-drift-ledger.json` snapshot on 2026-06-25 (Wave 04).

## Ledger shape

| Field | Value |
|-------|-------|
| Version | 1 |
| Records | 90 (parity with `repo-sync-inventory.json`) |
| `source_refs` | `config/sync-manifest.json`, `planning/manifests/repo-sync-inventory.json`, git-status observation note |

## `current_state` distribution

| State | Count | Interpretation |
|-------|-------|----------------|
| `external-live` | 38 | Home/app-support paths; not repo-audited |
| `tracked-dirty` | 24 | Repo paths with uncommitted drift |
| `generated-live` | 14 | Generated surfaces present but may need regen |
| `not-checked` | 11 | Awaiting explicit audit |
| `tracked-clean` | 2 | In sync with expected mode |
| `untracked` | 1 | Path exists outside expected tracking |

All 90 rows carry `location_class: repo` in the ledger schema; home/app-support semantics flow through path templates and `external-live` state.

## `drift_risk` distribution

| Risk | Count |
|------|-------|
| medium | 66 |
| high | 22 |
| low | 2 |

High-risk rows cluster on merged live config, symlink targets, and generated surfaces with credential-adjacent paths.

### `openspec-active-changes-capture-w04`

# OpenSpec Active Changes Capture W04

Read-only OpenSpec active-change inventory on 2026-06-25 (Wave 04).

## Validation

```
uv run wagents openspec validate
→ 33/33 items passed (8 changes, 25 specs)
```

## Directory counts

| Bucket | Count | Path |
|--------|-------|------|
| Active changes | 8 | `openspec/changes/<name>/` (non-archive) |
| Archived changes | 53 | `openspec/changes/archive/` |

## Active change task posture

| Change ID | Open | Done | Archive-ready |
|-----------|------|------|---------------|
| `add-new-project-skill` | 0 | 14 | yes |
| `consolidate-review-skill` | 0 | 15 | yes |
| `enhance-skill-creator-lifecycle` | 0 | 12 | yes |
| `upgrade-design-skill` | 0 | 20 | yes |
| `compose-harness-catalog-pages` | 5 | 2 | no |
| `integrate-apm-package-manager` | 8 | 27 | no |
| `integrate-mcphub-control-plane` | 5 | 11 | no |
| `public-release-prod-readiness` | 10 | 0 | no |

Task counts include both `- [ ]` / `- [x]` and numbered `N. [ ]` / `N. [x]` checklist styles.

## Wave themes (in-flight)

### `planning-sync-inventory-capture-w04`

# Planning Sync Inventory Capture W04

Read-only `planning/manifests/` inventory on 2026-06-25 (Wave 04).

## Manifest corpus layout

| Surface | Role |
|---------|------|
| `planning/README.md` | Index; prose planning corpus removed post-overhaul archive |
| `planning/manifests/repo-sync-inventory.json` | Path ownership, mode, drift policy, validation evidence |
| `planning/manifests/repo-drift-ledger.json` | Observed/assumed drift state and next actions |
| `planning/manifests/harness-fixture-support.json` | Conservative harness support and rollback posture |
| `planning/manifests/external-repo-*.json` | External repo intake/evaluation ledgers (93 rows each in final + intake) |
| `planning/manifests/*.json` (scaffold) | Compose/review/docs baselines with 0 records (placeholders) |

**Total manifest files:** 18 under `planning/manifests/` (17 JSON + 1 MD plugin install note).

## `repo-sync-inventory.json` (90 records)

| Dimension | Distribution |
|-----------|--------------|
| `mode` | canonical 31, generated 30, merged 18, symlink 7, symlinked-entries 4 |
| `location_class` | repo 52, home 34, application-support 4 |
| `drift_policy` | canonical 33, generated 31, merged 18, symlinked-entries 4, symlink 4 |
| `source_tier` | generated-output 31, canonical-source 31, merged-live-config 18, symlink-target 10 |
| `secret_handling` | not-secret-bearing 59, path-only 19, redacted 12 |

`source_ref` points at `config/sync-manifest.json`; inventory is the conservative planning mirror with per-path validation evidence and secret-handling posture.

## `harness-fixture-support.json` (19 harness rows)

| Field | Distribution |
|-------|--------------|
| `fixture_status` | fixture-executable 12, fixture-plan-only 4, docs-ledger-required 3 |


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 3**; wiki pages enriched: 2; lint: pass (exit 0).

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
