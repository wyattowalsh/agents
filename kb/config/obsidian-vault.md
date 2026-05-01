---
title: Obsidian Vault Configuration
tags:
  - kb
  - config
  - obsidian
aliases:
  - Vault config
kind: index
status: active
updated: 2026-05-01
source_count: 2
---

# Obsidian Vault Configuration

## Vault Mode

`kb/` is an Obsidian-native, git-friendly vault surface embedded inside the repository. It should remain useful as plain Markdown.

## Shared `.obsidian` Surfaces

| Path | Status | Rule |
|------|--------|------|
| `.obsidian/templates/` | active | Markdown templates are shared project assets. |
| `.obsidian/snippets/` | documented | CSS snippets were not created in this Markdown-only batch. |
| Workspace/session files | out of scope | Do not add volatile local Obsidian state by default. |

## Attachment Path

Use `raw/assets/` for local supporting assets when they are safe to vendor and materially support the KB. Use pointer stubs for huge, binary, private, symlinked, or secret-looking sources.

## Template Usage

Start new wiki pages from `.obsidian/templates/wiki-page.md` and then update `indexes/source-map.md`, `indexes/coverage.md`, and `activity/log.md` in the same batch.

## Dataview Metadata Contract

Use `title`, `tags`, `aliases`, `kind`, `status`, `updated`, and `source_count` on maintained wiki and index pages.

`source_count` should be a practical count of backing source notes for the page or index, not a global KB invariant. Source and coverage indexes use the total mapped source-note count.

## External Source Notes

External source notes are allowed under `raw/sources/` as pointer summaries. They should support upstream context only and should not override repo-local canonical material.

## Out-Of-Scope Volatile State

Do not commit Obsidian workspace panes, recent files, hotkeys, machine-personal themes, or other local session state unless explicitly requested and reviewed.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Obsidian-native KBs should remain plain Markdown and use Obsidian double-bracket links. | `kb/raw/sources/nerdbot-skill-contract.md` | raw source note | Derived from Obsidian vault guidance. |
| Shared `.obsidian/templates/` and `.obsidian/snippets/` are project-safe surfaces, while volatile workspace state is out of scope. | `kb/raw/sources/nerdbot-skill-contract.md` | raw source note | Derived from Obsidian vault guidance. |
| External Obsidian and Markdown docs provide syntax context for vault conventions. | `kb/raw/sources/external-obsidian-markdown-docs.md` | external source note | Context only. |
