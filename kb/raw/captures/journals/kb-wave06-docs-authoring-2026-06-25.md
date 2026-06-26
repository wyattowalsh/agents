---
title: "Research journal — KB wave 06"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 06 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave06-docs-authoring-2026-06-25
original_location: "~/.grok/research/kb-wave06-docs-authoring-2026-06-25.md"
---

# Research journal — KB wave 06

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 06 | Theme: docs authoring and catalog index
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 06 — docs authoring and catalog index`

## G0 brief

Explicit-path inventory of Bucket A authoring MDX (363) and committed catalog index bundle (363 rows); no repo-wide globs.

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `catalog-authoring-mdx-capture-w06` | `kb/raw/captures/catalog-authoring-mdx-capture-w06.md` |
| worker | `docs-generate-check-capture-w06` | `kb/raw/captures/docs-generate-check-capture-w06.md` |
| worker | `skills-catalog-index-capture-w06` | `kb/raw/captures/skills-catalog-index-capture-w06.md` |

## Ingest queue

- `raw`: added 3 captures (`catalog-authoring-mdx-capture-w06`, `skills-catalog-index-capture-w06`, `docs-generate-check-capture-w06`).

## Capture evidence (excerpts)

### `catalog-authoring-mdx-capture-w06`

# Catalog Authoring MDX Capture W06

Flat Bucket A SSOT under `docs/src/authoring/skills/*.mdx`.

## Captured Facts

| Metric | Value | Method |
|--------|-------|--------|
| Authoring MDX files | 363 | `ls docs/src/authoring/skills \| wc -l` |
| Naming convention | kebab-case id matches skill/catalog id | directory listing sample |
| Source kinds | `custom` and `curated-external` per frontmatter | index + AGENTS §2.7 |

## Scope

Human-authored catalog rows live here; `wagents docs generate` emits machine bundle and derived catalog pages. Do not hand-edit `docs/src/content/docs/skills/catalog/**` or `skills-catalog-index.json` except via generator.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Bucket A authoring path | `AGENTS.md` §2.7 | canonical repo policy |
| MDX count | filesystem listing | tool capture |

### `docs-generate-check-capture-w06`

# Docs Generate Check Capture W06

Freshness gates for docs generation on 2026-06-25.

## Captured Facts

| Check | Result | Evidence |
|-------|--------|----------|
| `wagents docs generate --no-installed --check` | wired in CI | `.github/workflows/ci.yml` |
| Prior session check | up to date | `kb/raw/captures/wagents-docs-cli-capture-w02.md` |
| Compose gate | 100% minimum | same workflow + `docs-freshness-capture-w01` |
| Catalog index check | `wagents catalog index --check` per authoring policy | `skills-catalog-authoring-lifecycle-source` |

## Remaining hand-maintained drift

MCP landing badge (15 vs 33 servers) tracked in `docs-freshness-capture-w01`; not a generator defect.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| CI generate --check | `.github/workflows/ci.yml` | canonical repo path |
| CLI check behavior | `wagents/docs.py` | canonical repo path |

### `skills-catalog-index-capture-w06`

# Skills Catalog Index Capture W06

Committed machine bundle at `docs/public/generated-registries/skills-catalog-index.json`.

## Captured Facts

| Metric | Value | Method |
|--------|-------|--------|
| `allSkillIndex` entries | 363 | JSON parse |
| Inferred custom rows | 56 | `sourceKind` / `source_kind` == custom |
| Inferred curated-external rows | 307 | curated-external kind |
| Runtime SSOT | this JSON file | `wagents docs generate` default output |

## Quoted policy

> Prefer authoring MDX + index; dual-read legacy `config/external-skills.md` only when index missing.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Index entry count | `skills-catalog-index.json` | repo file read |
| Custom/external split | JSON field scan | tool capture |
| Generator ownership | `kb/raw/sources/skills-catalog-authoring-lifecycle-source.md` | prior KB source |


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 3**; pages enriched: 2; lint: pass.

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
