---
title: Obsidian Properties Capture W11
tags:
  - kb
  - source
  - external
  - obsidian
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave11-gap-sweep-2026-06-25
---

# Obsidian Properties Capture W11

Full-capture pointer lane for Obsidian Help properties/aliases/links semantics. Context only; `kb/config/obsidian-vault.md` and Nerdbot skill contracts govern this vault.

| Field | Value |
|-------|-------|
| source_id | `obsidian-properties-capture-w11` |
| original_location | `https://obsidian.md/help/properties`; `https://help.obsidian.md/aliases`; `https://help.obsidian.md/links`; `https://help.obsidian.md/obsidian-flavored-markdown` |
| capture_method | official help URL pointer + KB contract cross-check |
| captured_at | 2026-06-25 |

## Summary

Obsidian **properties** (YAML frontmatter) carry typed metadata Obsidian indexes for search, Dataview, and graph features. **Aliases** provide alternate link targets for double-bracket wikilinks. **Links** use Obsidian wikilink syntax with optional display text and heading/block anchors. This KB uses a reduced property schema (`title`, `tags`, `aliases`, `kind`, `status`, `updated`, `source_count`) enforced by `kb_lint.py` and documented in `kb/schema/page-types.md`.

## Repo alignment

| Obsidian concept | KB convention |
|----------------|---------------|
| Properties in frontmatter | Required on wiki/index/source pages per `page-types.md` |
| Aliases | Used for human-friendly link targets (e.g., `KB coverage` → `coverage.md`) |
| Wikilinks | Double-bracket links between `wiki/`, `indexes/`, `raw/` notes |
| Volatile `.obsidian/` state | Workspace JSON excluded; shared templates/snippets tracked |

## Provenance

| Claim | Source |
|-------|--------|
| URL list | `kb/raw/sources/external-obsidian-markdown-docs.md` |
| Vault policy | `kb/config/obsidian-vault.md` |
| Lint contract | `skills/nerdbot/scripts/kb_lint.py` |