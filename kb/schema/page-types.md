---
title: KB Page Types
tags:
  - kb
  - schema
aliases:
  - Page type schema
kind: index
status: active
updated: 2026-05-01
source_count: 5
---

# KB Page Types

## Frontmatter Contract

Maintained wiki and index notes use this Dataview-safe frontmatter set:

| Field | Required | Meaning |
|-------|----------|---------|
| `title` | yes | Stable display title. |
| `tags` | yes | Classification and filtering. |
| `aliases` | yes | Search/navigation aliases. |
| `kind` | yes | `overview`, `concept`, `entity`, `comparison`, `source-summary`, `mapping`, or `index`. |
| `status` | yes | `bootstrap`, `active`, `partial`, `needs-review`, or `historical`. |
| `updated` | yes | Last meaningful review date. |
| `source_count` | yes | Count of backing sources or source notes. |

## Evidence Section Contract

Substantive wiki pages must include an `Evidence` section with this table:

| Claim | Source | Type | Notes |
|-------|--------|------|-------|

Use raw source notes, canonical repo paths, or explicit external source notes as sources. Do not cite uncaptured web claims.

## External Source Note Rule

External source notes may support upstream context and syntax semantics, but repo-local source notes or canonical material must back claims about this repository's actual behavior.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Nerdbot maintained notes should use frontmatter and provenance. | `kb/raw/sources/nerdbot-skill-contract.md` | raw source note | Derived from Nerdbot architecture and Obsidian references. |
| Shared page contracts require scope, provenance, related indexes, and open questions. | Loaded `references/page-templates.md` summarized in `kb/raw/sources/nerdbot-skill-contract.md` | canonical material | Page template guidance. |
| External source notes are accepted only as explicit context sources. | `kb/raw/sources/external-agent-skill-docs.md`; `kb/raw/sources/external-harness-docs.md`; `kb/raw/sources/external-tooling-docs.md`; `kb/raw/sources/external-obsidian-markdown-docs.md` | external source notes | Repo-local sources stay authoritative. |
