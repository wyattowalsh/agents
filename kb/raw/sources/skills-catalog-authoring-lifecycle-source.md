---
title: Skills Catalog Authoring Lifecycle
tags:
  - kb
  - source
  - skills
  - catalog
aliases:
  - Bucket A authoring lifecycle
kind: source-summary
status: active
updated: 2026-06-23
source_count: 1
---

# Skills Catalog Authoring Lifecycle

## Source Record

| Field | Value |
|-------|-------|
| source_id | `skills-catalog-authoring-lifecycle` |
| original_location | `AGENTS.md` §2.7; `docs/src/authoring/skills/*.mdx`; `wagents/authoring_sync.py`; `wagents/docs.py`; `wagents/skill_index.py`; `wagents/external_skills.py`; `docs/public/generated-registries/skills-catalog-index.json`; `config/external-skills.md` |
| raw_path | `kb/raw/sources/skills-catalog-authoring-lifecycle-source.md` |
| capture_method | repo-local pointer summary from read-only research and code inspection |
| captured_at | 2026-06-23 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical material |
| intended_wiki_coverage | [[curated-catalog-authoring]], [[skill-authoring-and-validation]], [[docs-generation-and-site]], [[harness-and-platform-sync]] |

## Summary

Bucket A catalog semantics use a phased SSOT invert. Human authoring lives in flat `docs/src/authoring/skills/*.mdx` (one file per skill). `wagents docs generate` (default `--no-installed`) syncs repo-owned customs from `skills/*/SKILL.md`, builds `docs/public/generated-registries/skills-catalog-index.json`, and derives catalog MDX under `docs/src/content/docs/skills/catalog/`. Curated externals are authored directly in MDX with `source_kind: curated-external` and structured frontmatter; they are not vendored into `skills/`.

`wagents skills sync --dry-run/--apply` consumes the catalog index (or legacy dual-read of `config/external-skills.md`) to emit additive `npx skills add` commands per harness. `wagents validate` and `wagents catalog index --check` gate structure and index freshness.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Authoring MDX is human SSOT for Bucket A. | `AGENTS.md`; `wagents/external_skills.py` | canonical material | Legacy MD is dual-read fallback only. |
| Customs project from `skills/*/SKILL.md` via authoring sync. | `wagents/authoring_sync.py` | canonical material | Uses `GENERATED-AUTHORING` marker. |
| Index is runtime SSOT for catalog consumers. | `wagents/skill_index.py`; `config/schemas/skills-catalog-index.schema.json` | canonical material | Committed generated bundle. |
| Skills sync uses install-now-after-trust-gate curated rows. | `wagents/installed_inventory.py`; `wagents/cli.py` | canonical material | Grok mirrors via Claude adapter. |

## Planned wiki coverage

| Topic | Status |
|-------|--------|
| [[curated-catalog-authoring]] | primary synthesis |
| [[skill-authoring-and-validation]] | cross-link lifecycle |
| [[docs-generation-and-site]] | generate pipeline |