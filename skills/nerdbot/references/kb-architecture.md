# KB Architecture

## Purpose
Use this reference to keep a markdown-first KB legible, layered, and reviewable. The default contract is simple: `raw` keeps evidence, `wiki` keeps synthesis, `schema` and `config` keep contracts and settings, `indexes` keep navigation and coverage, and the `activity log` records every mutating batch.

## Architecture promises
- [ ] `raw` is append-only and keeps originals beside normalized extracts.
- [ ] `wiki` only makes substantive claims that trace to `raw` or declared `canonical material`.
- [ ] `schema` and `config` stay separate from content.
- [ ] `indexes` are updated in the same batch as related `raw` or `wiki` changes.
- [ ] The `activity log` records what changed, why, and what still needs follow-up.
- [ ] `derived output` is rebuildable and never replaces the KB as the source of truth.

## Safe default layout

```text
<kb-root>/
  raw/
    sources/
    captures/
    extracts/
  wiki/
    index.md
    topics/
  schema/
  config/
  indexes/
    source-map.md
    coverage.md
  activity/
    log.md
```

### Layer semantics
| Layer | What belongs here | Common file shapes | Safe default |
|-------|-------------------|--------------------|--------------|
| `raw` | Imported originals, captures, transcripts, extracts, and normalization notes | `raw/sources/...`, `raw/captures/...`, `raw/extracts/...` | Preserve originals and add new files instead of overwriting old ones |
| `wiki` | Synthesized knowledge for humans and agents | `wiki/index.md`, `wiki/topics/...` | Back every substantive claim with `provenance` |
| `schema` | Naming rules, required sections, taxonomies, and page contracts | `schema/page-types.md`, `schema/fields.md` | Change deliberately and review the blast radius first |
| `config` | Operational settings for ingest, derive, and verification flows | `config/ingest.md`, `config/derive.md` | Keep settings separate from `raw` and `wiki` |
| `indexes` | Coverage maps, source maps, inventories, and aliases | `indexes/source-map.md`, `indexes/coverage.md` | Refresh them in the same batch as related content |
| `activity log` | Append-only record of imports, repairs, decisions, and known gaps | `activity/log.md` | Append entries instead of rewriting history |

## Provenance contract

### Minimum provenance by surface
| Surface | Minimum provenance |
|---------|--------------------|
| `wiki/index.md` or another overview page | Links to the current `wiki` map plus `indexes/source-map.md`, `indexes/coverage.md`, and the `activity log` |
| Concept, entity, or comparison page | A `Provenance` section with one row per key claim linking to `raw` or `canonical material` |
| Source summary page | Raw path, import context, intended `wiki` coverage, and unresolved gaps |
| `derived output` note | Inputs, recipe, timestamp, regeneration path, and the linked `activity log` entry |

### Provenance example
| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `[Claim backed by evidence]` | `raw/extracts/interview-01.md#L24-L31` | `raw` | Confirmed in transcript |
| `[Claim preserved from existing guide]` | `wiki/topics/origin-story.md` | `canonical material` | Existing authoritative phrasing |

Keep provenance reviewable:
- Prefer line anchors, section anchors, or stable file references over vague citations.
- Mark unresolved evidence gaps instead of filling them with unsupported synthesis.
- If a claim relies on `canonical material`, say so explicitly.

## Canonical material boundary
- [ ] List current `canonical material` before structural work starts.
- [ ] Keep authoritative paths stable unless a `migration` is explicitly approved.
- [ ] Prefer companion `wiki` pages, mapping pages, or aliases over moving files.
- [ ] Extend or annotate user-authored pages before considering a rewrite.
- [ ] Record approvals and exceptions in `activity/log.md`.

### Decision rules
| Situation | Safe default |
|-----------|--------------|
| Existing user-authored guide must stay in place | Treat it as `canonical material`, add index links around it, and leave the path alone |
| Evidence exists but no `wiki` page exists yet | Add the `raw` evidence first, then create a new `wiki` page and update `indexes` |
| The repo mixes notes, summaries, and source captures | Classify it as an `imperfect repo`, map the current state, then add missing layers before considering `migration` |

## Core file shapes

### `wiki/index.md`
Keep the root `wiki` page small, navigational, and explicit about scope.

Suggested sections:
- `Scope`
- `Canonical material`
- `Current wiki map`
- `First ingest queue` or `Current priorities`
- Links to `indexes/source-map.md`, `indexes/coverage.md`, and `activity/log.md`

### `indexes/source-map.md`
Use a table that makes `raw` coverage easy to audit.

| Source ID | Raw path | Capture type | Planned wiki target | Provenance status | Status |
|-----------|----------|--------------|---------------------|-------------------|--------|
| `vendor-brief-2026` | `raw/sources/vendor-brief-2026.pdf` | import | `wiki/topics/vendor-landscape.md` | linked | summarized |

### `indexes/coverage.md`
Track maintained `wiki` pages against backing evidence.

| Wiki path | Page type | Backing raw or canonical material | Coverage status | Last reviewed | Next action |
|-----------|-----------|-----------------------------------|-----------------|---------------|-------------|
| `wiki/topics/vendor-landscape.md` | overview | `raw/sources/vendor-brief-2026.pdf` | partial | `2026-04-06` | backfill provenance for pricing notes |

### `activity/log.md`
Record one append-only entry per mutating batch.

```md
### [YYYY-MM-DD HH:MM] [Batch label]
- Summary: [what changed]
- `raw`: [files added or updated]
- `wiki`: [files added or updated]
- `indexes`: [files added or updated]
- `canonical material`: [unchanged, annotated, or approved exception]
- `provenance`: [what is now linked or what remains missing]
- `derived output`: [none or output path]
- Follow-up:
  - [next safe batch]
```

## Adapting an imperfect repo
Use additive-first repair when the existing layout is mixed or incomplete.

1. Add `indexes/source-map.md`, `indexes/coverage.md`, and `activity/log.md` before moving anything.
2. Create a safe `raw/` intake area and begin preserving evidence there.
3. Map existing notes into the `wiki` layer with links, companion pages, or summaries.
4. Backfill `provenance` on the most important pages.
5. Escalate to `migration` only when additive repair cannot meet the goal.

## Architecture exit checklist
- [ ] Layer boundaries are clear.
- [ ] `canonical material` is identified.
- [ ] A minimal `provenance` pattern is chosen.
- [ ] `indexes/source-map.md`, `indexes/coverage.md`, and `activity/log.md` have owners.
- [ ] The first batch is additive, reviewable, and non-destructive.
