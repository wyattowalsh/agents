---
title: Nerdbot Skill Contract Source Note
tags:
  - kb
  - source
  - nerdbot
aliases:
  - Nerdbot contract source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 4
---

# Nerdbot Skill Contract Source Note

## Source Record

| Field | Value |
|-------|-------|
| source_id | `nerdbot-skill-contract` |
| original_location | `skills/nerdbot/SKILL.md`; `skills/nerdbot/README.md`; Nerdbot loaded skill references |
| raw_path | `kb/raw/sources/nerdbot-skill-contract.md` |
| capture_method | Pointer summary from local skill and loaded reference docs |
| captured_at | 2026-05-01 |
| size_bytes | not captured; sources remain in place |
| checksum | not captured; sources remain canonical in repo/installed skill |
| license_or_access_notes | Repo-local skill plus loaded local skill reference text |
| intended_wiki_coverage | [[nerdbot]], [[repository-overview]], [[known-risks-and-open-gaps]] |

## Summary

Nerdbot maintains Obsidian-native, git-friendly knowledge bases with separated `raw`, `wiki`, `schema`, `config`, `indexes`, and `activity log` layers. Its CLI supports bootstrap, inventory, lint, plan, query, modes, graph, retrieval, source capture, watch policy, and replay policy helpers while keeping query/audit read-only by default and raw/activity surfaces append-only.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `raw/` stores evidence and `wiki/` stores synthesis. | `skills/nerdbot/README.md`; loaded Nerdbot skill contract | canonical material | Core contract. |
| Nerdbot offers `inventory` and `lint` commands for KB checks. | `skills/nerdbot/README.md` | canonical material | CLI section. |
| Outside-root, symlinked, oversized, unreadable, or secret-looking files should be pointer stubs unless explicitly approved for safe copy. | `skills/nerdbot/README.md`; loaded Nerdbot skill contract | canonical material | Source safety. |
| `.obsidian/templates/` and `.obsidian/snippets/` are shared vault surfaces; volatile workspace state is out of scope by default. | loaded `references/obsidian-vaults.md` | canonical material | Shared vault guidance. |
