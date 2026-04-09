<!-- Replace bracketed placeholders. Copy each packet section into the named path. -->
# KB Bootstrap Packet

## Directories
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
- [ ] `[Overview page](topics/[overview-page].md)`
- [ ] `[Source summary page](topics/[source-summary-page].md)`

## First ingest queue
| Source | Planned raw path | Planned wiki target | Status |
|--------|------------------|---------------------|--------|
| `[source name]` | `raw/sources/[file]` | `wiki/topics/[page].md` | queued |

## Related indexes
- [Source Map](../indexes/source-map.md)
- [Coverage](../indexes/coverage.md)
- [Activity Log](../activity/log.md)

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

---

Path: `indexes/coverage.md`

# Coverage

| Wiki path | Page type | Backing raw or canonical material | Coverage status | Last reviewed | Notes |
|-----------|-----------|-----------------------------------|-----------------|---------------|-------|
| `wiki/index.md` | overview | `[canonical material or source set]` | bootstrap | [YYYY-MM-DD] | initial map only |

## Gaps
- [ ]

---

Path: `activity/log.md`

# Activity Log

## Operating rules
- Append-only.
- Record one entry per mutating batch.
- Name the `raw`, `wiki`, `indexes`, `schema`, and `config` surfaces touched in each batch.
- Call out `canonical material`, `provenance`, and `derived output` decisions explicitly.

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
- Risks / rollback: remove only the new scaffold if the KB root was created in error
- Follow-up:
  - [ ] Add the first source to `raw/`
