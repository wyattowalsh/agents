<!-- Replace bracketed placeholders. Copy each packet section into the named path. -->
# KB Bootstrap Packet

## Directories
- `.obsidian/templates/`
- `.obsidian/snippets/`
- `raw/assets/`
- `raw/sources/`
- `raw/captures/`
- `raw/extracts/`
- `wiki/topics/`
- `schema/`
- `config/`
- `indexes/`
- `activity/`

---

Path: `wiki/index.md`

---
title: [KB Title]
tags:
  - kb
  - moc
  - bootstrap
aliases:
  - [KB Title] Index
kind: overview
status: bootstrap
updated: [YYYY-MM-DD]
source_count: 0
---

# [KB Title]

## Scope
- Topic: [topic]
- KB root: `[kb-root]`
- Status: bootstrap
- Non-goals:
  - [ ]

## Canonical material
| Path | Authority | Notes |
|------|-----------|-------|
| `[path]` | [authoritative / pending review] | [notes] |

## Current wiki map
- [ ] `[[topics/[overview-page]|Overview page]]`
- [ ] `[[topics/[source-summary-page]|Source summary page]]`

## First ingest queue
| Source | Planned raw path | Planned wiki target | Status |
|--------|------------------|---------------------|--------|
| `[source name]` | `raw/sources/[file]` | `wiki/topics/[page].md` | queued |

## Related indexes
- [[indexes/source-map|Source Map]]
- [[indexes/coverage|Coverage]]
- [[activity/log|Activity Log]]

## Vault conventions
- Link style: prefer `[[wikilinks]]` for vault-local notes and Markdown links for external URLs.
- Attachments: default local supporting assets to `raw/assets/`.
- Metadata: maintain `tags`, `aliases`, `kind`, `status`, `updated`, and `source_count` where useful.
- Shared surfaces: keep project-safe note templates in `.obsidian/templates/` and snippets in `.obsidian/snippets/`.

## Open questions
- [ ]

---

Path: `indexes/source-map.md`

# Source Map

| Source ID | Raw path | Capture type | Planned wiki target | Canonical material touched? | Provenance status | Status |
|-----------|----------|--------------|---------------------|-----------------------------|-------------------|--------|
| `[source-id]` | `raw/sources/[file]` | [import / capture / extract] | `wiki/topics/[page].md` | [no / yes] | [missing / partial / linked] | queued |

## Notes
- Preserve originals in `raw/`.
- Add new rows instead of overwriting import history.
- If a note move or rename touches source-summary pages, record the old and new note names in the path map before cutover.

---

Path: `indexes/coverage.md`

# Coverage

| Wiki path | Page type | Backing raw or canonical material | Coverage status | Last reviewed | Notes |
|-----------|-----------|-----------------------------------|-----------------|---------------|-------|
| `wiki/index.md` | overview | `[canonical material or source set]` | bootstrap | [YYYY-MM-DD] | initial map only |

## Gaps
- [ ]

---

Path: `config/obsidian-vault.md`

# Obsidian Vault Conventions

## Vault mode
- Mode: obsidian-native
- KB root: `[kb-root]`
- Default note link style: `[[wikilinks]]`

## Shared `.obsidian/` surfaces
- `.obsidian/templates/`
- `.obsidian/snippets/`

## Attachment path
- Local supporting assets live under `raw/assets/` unless a stronger existing convention already exists.

## Dataview metadata contract
- Recommended fields: `title`, `tags`, `aliases`, `kind`, `status`, `updated`, `source_count`, `cssclasses`

## Out-of-scope volatile state
- Workspace panes and session layout
- Recent files and UI history
- Machine-personal appearance settings

---

Path: `.obsidian/templates/wiki-note-template.md`

---
title: "{{title}}"
tags:
  - kb
aliases: []
kind: concept
status: active
updated: [YYYY-MM-DD]
source_count: 0
---

# {{title}}

## Summary

## Provenance
| Claim or section | Raw or canonical material | Notes |
|------------------|---------------------------|-------|

## Related notes
- [[wiki/index]]

## Open questions
- [ ]

---

Path: `.obsidian/templates/source-note-template.md`

---
title: "{{title}}"
tags:
  - kb
  - source
aliases: []
kind: source-summary
status: active
updated: [YYYY-MM-DD]
source_count: 1
---

# {{title}}

## Source record
| Field | Value |
|-------|-------|
| Raw source | `raw/sources/[file]` |
| Capture or extract | `raw/extracts/[file]` |

## Summary

## Planned wiki coverage
- [[wiki/index]]

---

Path: `activity/log.md`

# Activity Log

## Operating rules
- Append-only.
- Record one entry per mutating batch.
- Name the `raw`, `wiki`, `indexes`, `schema`, and `config` surfaces touched in each batch.
- Call out `canonical material`, `provenance`, and `derived output` decisions explicitly.
- Record vault-impact details whenever frontmatter, aliases, embeds, or shared `.obsidian/` surfaces change.

### [YYYY-MM-DD HH:MM] Bootstrap
- Mode: create
- Summary: Initialized the layered KB structure.
- `raw`: seeded directories only
- `wiki`: added `wiki/index.md`
- `indexes`: added `indexes/source-map.md` and `indexes/coverage.md`
- `schema`: [added / not yet needed]
- `config`: [added / not yet needed]
- `canonical material`: [none yet / listed in `wiki/index.md`]
- `provenance`: initial placeholders only
- `derived output`: none
- `vault`: initialized `.obsidian/` shared surfaces and note metadata defaults
- `path map`: none
- `link/backlink impact`: root indexes now provide the first stable navigation surface
- Risks / rollback: remove only the new scaffold if the KB root was created in error
- Follow-up:
  - [ ] Add the first source to `raw/`
