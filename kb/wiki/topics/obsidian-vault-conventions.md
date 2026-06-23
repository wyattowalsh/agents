---
title: Obsidian Vault Conventions
tags:
  - kb
  - obsidian
  - nerdbot
aliases:
  - Obsidian vault conventions
  - Vault conventions
kind: concept
status: active
updated: 2026-06-23
source_count: 3
---

# Obsidian Vault Conventions

## Summary

`kb/` is an Obsidian-native vault embedded in the agents repository. It remains useful as plain Markdown outside Obsidian, but shared conventions (frontmatter, Obsidian wikilinks, templates, and attachment paths) keep navigation and provenance consistent for humans and agents.

## Why it matters

- Agents operating this repo need stable note names, aliases, and link targets without basename collisions between `raw/` and `wiki/`.
- Shared templates under `.obsidian/templates/` reduce frontmatter drift across new source and wiki pages.
- Volatile Obsidian workspace state must stay out of git; only project-safe shared surfaces belong in `.obsidian/`.

## Current shape

| Surface | Role |
|---------|------|
| `.obsidian/templates/` | Shared starters for wiki and source notes |
| `.obsidian/snippets/` | Documented; CSS snippets not added in Markdown-only batches |
| `config/obsidian-vault.md` | Vault policy contract (attachments, metadata, external source rules) |
| `raw/assets/` | Safe local attachments when vendoring materially supports a source |
| Frontmatter contract | `title`, `tags`, `aliases`, `kind`, `status`, `updated`, `source_count` |

## Constraints and edge cases

- Keep raw source basenames distinct from wiki topic basenames (use `*-source.md` suffix when needed) to avoid ambiguous wikilink targets.
- External Obsidian/Markdown docs are context-only; repo-local raw notes and canonical files govern behavior.
- `source_count` is a per-page practical count of distinct backing sources, not a global KB invariant.

## Provenance

| Claim or section | Raw or canonical material | Notes |
|------------------|---------------------------|-------|
| Layered KB model and vault rules | `kb/raw/sources/nerdbot-skill-contract.md` | Nerdbot contract |
| Shared vs volatile `.obsidian/` surfaces | `kb/config/obsidian-vault.md` | Config contract |
| Obsidian syntax context | `kb/raw/sources/external-obsidian-markdown-docs.md` | External pointer only |

## Related wiki pages

- [[nerdbot]]
- [[external-primary-source-map]]

## Open questions

- Whether to add shared CSS snippets in a later non-Markdown-approved batch.