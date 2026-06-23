---
title: Curated Catalog Authoring
tags:
  - kb
  - skills
  - catalog
aliases:
  - Bucket A authoring
  - Catalog SSOT
kind: concept
status: active
updated: 2026-06-23
source_count: 2
---

# Curated Catalog Authoring

## Summary

Bucket A catalog semantics use authoring MDX as the human SSOT. Flat files under `docs/src/authoring/skills/*.mdx` carry structured frontmatter for both repo-owned customs (`source_kind: custom`) and curated externals (`source_kind: curated-external`). `wagents docs generate` syncs customs from `skills/*/SKILL.md`, emits `docs/public/generated-registries/skills-catalog-index.json`, and derives public catalog MDX pages. Do not hand-edit generated catalog output.

## Why it matters

- Curated externals stay out of `skills/` unless authoring a new repo-owned skill.
- The committed index is the runtime SSOT for `skill_index`, `external_skills`, catalog rows, validation quarantine, and `wagents skills sync`.
- Legacy `config/external-skills.md` remains dual-read fallback only during transition.

## Current shape

| Stage | Surface |
|-------|---------|
| Author customs | `skills/<name>/SKILL.md` |
| Project customs | `docs/src/authoring/skills/<name>.mdx` via `authoring_sync` |
| Author curated externals | `docs/src/authoring/skills/<id>.mdx` directly |
| Machine bundle | `docs/public/generated-registries/skills-catalog-index.json` |
| Public catalog | `docs/src/content/docs/skills/catalog/{custom,external}/` |
| Harness install | `wagents skills sync --dry-run` / `--apply` |

## Constraints and edge cases

- Schema enum may say `external` in authoring schema while code uses `curated-external`; treat code and live MDX as authoritative.
- Use `wagents catalog index --check` and pre-commit hook for index freshness.
- Audit curated sources with `/review source` before endorsing install-now status.

## Provenance

| Claim or section | Raw or canonical material | Notes |
|------------------|---------------------------|-------|
| Bucket A SSOT invert and maintainer loop | `kb/raw/sources/skills-catalog-authoring-lifecycle-source.md` | Primary |
| AGENTS policy | `kb/raw/sources/agents-md.md` | Canonical |

## Related wiki pages

- [[skill-authoring-and-validation]]
- [[docs-generation-and-site]]
- [[skill-catalog-risk-and-eval-coverage]]
- [[harness-and-platform-sync]]

## Open questions

- Whether to tighten runtime authoring MDX schema validation beyond tolerant load.