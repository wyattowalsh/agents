# Obsidian Vaults

## Purpose
Use this reference when `nerdbot` is creating, auditing, migrating, or enriching an Obsidian-native KB. The goal is not to turn the vault into plugin-dependent magic. The goal is to keep the wiki easy for both the LLM and Obsidian to navigate.

## Core contract
- [ ] Keep the KB as plain Markdown files under git.
- [ ] Prefer Obsidian-native syntax for vault-local navigation.
- [ ] Preserve the layered KB model: `raw` for evidence, `wiki` for synthesis, `schema` + `config` for contracts, `indexes` + `activity log` for navigation and operating history.
- [ ] Treat `.obsidian/` as a shared working surface only for project-safe templates, snippets, and documented conventions.
- [ ] Do not treat volatile workspace state as canonical material.

## Obsidian-native syntax

### Links
Use these forms for vault-local navigation:

| Syntax | Use |
|--------|-----|
| `[[Note]]` | Link to a note |
| `[[Note|Display Text]]` | Link with custom display text |
| `[[Note#Heading]]` | Link to a heading |
| `[[Note#^block-id]]` | Link to a block |
| `[[#Heading]]` | Link to a heading in the same note |

Prefer `[[wikilinks]]` for local notes. Keep standard Markdown links for external URLs.

### Embeds
Use embeds when the source material should stay live and reusable.

| Syntax | Use |
|--------|-----|
| `![[Note]]` | Embed a note |
| `![[Note#Heading]]` | Embed a section |
| `![[Note#^block-id]]` | Embed a block |
| `![[image.png]]` | Embed a local asset |

Default local supporting assets to `raw/assets/` unless the repo already has a stronger convention.

### Block IDs
Give stable fragments a block ID when other notes should link or embed them directly.

```md
This paragraph can be cited directly. ^claim-summary
```

For quotes, callouts, and lists, place the block ID on a separate line after the block.

## Frontmatter contract
Use small, machine-readable metadata. Keep it Dataview-safe.

### Recommended fields

| Field | Purpose |
|-------|---------|
| `title` | Stable display title |
| `tags` | Classification |
| `aliases` | Migration-safe alternate note names |
| `kind` | `overview`, `concept`, `entity`, `comparison`, `source-summary`, `mapping`, `index` |
| `status` | `bootstrap`, `active`, `partial`, `needs-review`, `historical` |
| `updated` | Last meaningful update date |
| `source_count` | Quick signal for source-backed density |
| `cssclasses` | Optional project-safe styling hooks |

### Example

```yaml
---
title: Vendor Landscape
tags:
  - kb
  - vendor
aliases:
  - Vendor Overview
kind: overview
status: partial
updated: 2026-04-13
source_count: 3
---
```

Use `aliases` aggressively during note moves or renames so navigation stays stable while the vault is under review.

## Shared `.obsidian/` surfaces
Treat these as safe, reviewable, project-level surfaces:

| Path | Purpose |
|------|---------|
| `.obsidian/templates/` | Shared note templates |
| `.obsidian/snippets/` | Shared CSS snippets |
| `config/obsidian-vault.md` | Human-readable vault conventions and operating contract |

Treat these as out of scope by default:
- workspace panes and session layout
- recent files and UI history
- machine-personal appearance or hotkey tweaks unless the user explicitly wants them versioned

## Dataview compatibility
Dataview is the only plugin expectation worth treating as first-class in the shared contract.

Use frontmatter that allows simple queries over:
- `kind`
- `status`
- `updated`
- `source_count`
- `tags`

Do not make the vault depend on Dataview-specific inline fields or custom plugin syntax unless the repo already does.

## Callout guidance
Callouts are useful for operator-visible epistemic states.

Recommended defaults:

| Callout | Use |
|---------|-----|
| `> [!note]` | neutral notes |
| `> [!info]` | context or background |
| `> [!tip]` | maintenance guidance |
| `> [!warning]` | migration hazard or review risk |
| `> [!quote]` | preserved source excerpt |
| `> [!example]` | reusable page-shape example |

When needed, label uncertainty explicitly in prose or callouts instead of implying certainty.

## Migration rules

### Normalize before expansion
When an existing repo is not already an Obsidian-native vault, do this first:
1. Identify canonical material and current path consumers.
2. Establish shared `.obsidian/` surfaces and `config/obsidian-vault.md`.
3. Normalize frontmatter on high-value notes.
4. Normalize note names, `aliases`, and `[[wikilinks]]`.
5. Place local supporting assets in a stable location such as `raw/assets/`.
6. Re-run lint before any large enrichment pass.

### Path safety
- [ ] Add `aliases` before deleting old names.
- [ ] Use mapping notes or path-map rows during staged moves.
- [ ] Update embeds and block refs in the same batch as note moves.
- [ ] Stop if note-name or alias collisions remain unresolved.

## Audit cues
During audit, check for:
- broken `[[wikilinks]]`
- broken `![[embeds]]`
- broken heading or block refs
- alias collisions
- missing or inconsistent frontmatter on maintained notes
- `.obsidian/` shared surfaces missing when the repo expects them
- volatile workspace files being treated as canonical requirements

## Minimalism rule
Keep the vault useful without requiring exotic tooling.

- Obsidian-native syntax: yes
- Dataview-friendly metadata: yes
- Plugin sprawl: no
- Heavy retrieval infrastructure as a default: no

The vault should still make sense as a plain Markdown repo, even when Obsidian is the primary IDE.
