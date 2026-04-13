# KB Architecture

## Purpose
Use this reference to keep an Obsidian-native, markdown-first KB legible, layered, and reviewable. The default contract is simple: `raw` keeps evidence, `wiki` keeps synthesis, `schema` and `config` keep contracts and settings, `indexes` keep navigation and coverage, the `activity log` records every mutating batch, and shared `.obsidian/` surfaces keep vault ergonomics reproducible.

## Architecture promises
- [ ] `raw` is append-only and keeps originals beside normalized extracts.
- [ ] `wiki` only makes substantive claims that trace to `raw` or declared `canonical material`.
- [ ] `schema` and `config` stay separate from content.
- [ ] `indexes` are updated in the same batch as related `raw` or `wiki` changes.
- [ ] The `activity log` records what changed, why, and what still needs follow-up.
- [ ] `derived output` is rebuildable and never replaces the KB as the source of truth.
- [ ] Shared `.obsidian/` surfaces stay project-safe, documented, and separate from volatile workspace state.

## Safe default layout

```text
<kb-root>/
  .obsidian/
    templates/
    snippets/
  raw/
    assets/
    sources/
    captures/
    extracts/
  wiki/
    index.md
    topics/
  schema/
  config/
    obsidian-vault.md
  indexes/
    source-map.md
    coverage.md
  activity/
    log.md
```

### Layer semantics
| Layer | What belongs here | Common file shapes | Safe default |
|-------|-------------------|--------------------|--------------|
| `raw` | Imported originals, captures, transcripts, extracts, downloaded assets, and normalization notes | `raw/sources/...`, `raw/captures/...`, `raw/extracts/...`, `raw/assets/...` | Preserve originals and add new files instead of overwriting old ones; for sources over `50 MB`, a pointer/stub with checksum, size, and source location is acceptable when vendoring the binary is impractical |
| `wiki` | Synthesized knowledge for humans and agents, written as Obsidian-native markdown | `wiki/index.md`, `wiki/topics/...` | Back every substantive claim with `provenance`; prefer frontmatter, `[[wikilinks]]`, and stable note names |
| `schema` | Naming rules, required sections, taxonomies, and page contracts | `schema/page-types.md`, `schema/fields.md` | Change deliberately and review the blast radius first |
| `config` | Operational settings for ingest, derive, verification, and shared vault conventions | `config/ingest.md`, `config/derive.md`, `config/obsidian-vault.md` | Keep settings separate from `raw` and `wiki` |
| `indexes` | Coverage maps, source maps, inventories, and path or alias references | `indexes/source-map.md`, `indexes/coverage.md` | Refresh them in the same batch as related content |
| `activity log` | Append-only record of imports, repairs, decisions, and known gaps | `activity/log.md` | Append entries instead of rewriting history |
| `shared vault config` | Project-safe Obsidian templates, snippets, and documented shared conventions | `.obsidian/templates/...`, `.obsidian/snippets/...` | Keep reproducible surfaces here; do not treat volatile workspace state as canonical |

## Karpathy alignment

Map the default nerdbot shape onto the `llm-wiki` pattern this way:

| `llm-wiki` layer | Nerdbot surface | Notes |
|------------------|-----------------|-------|
| Raw sources | `raw/` | Immutable evidence plus normalization notes and assets |
| Wiki | `wiki/` + `indexes/` + `activity/log.md` | Persistent markdown artifact with index/log support |
| Schema | `schema/` + `config/` + shared vault rules | Human-LLM contract for structure and workflows |

Keep the wiki incremental, interlinked, and cumulative. The KB should answer more queries by maintenance, not by rediscovering the same raw evidence from scratch.

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
| `[Claim supported by vault note]` | `[[wiki/topics/origin-story#Provenance]]` | `vault note` | Stable Obsidian-native note reference |

Keep provenance reviewable:
- Prefer line anchors, section anchors, or stable file references over vague citations.
- Prefer stable note names, `aliases`, and block IDs when a claim is meant to survive Obsidian-native moves or splits.
- Mark unresolved evidence gaps instead of filling them with unsupported synthesis.
- If a claim relies on `canonical material`, say so explicitly.

## Obsidian compatibility

### Core note contract
- [ ] Maintained `wiki` pages use frontmatter for stable metadata.
- [ ] Internal navigation prefers `[[wikilinks]]` over relative Markdown links when the target is another vault note.
- [ ] Embeds use `![[...]]` when a section, block, or local asset should stay in sync with the source note.
- [ ] Important reusable fragments get stable block IDs.
- [ ] `aliases` preserve discoverability across note moves and renames.

### Minimum frontmatter contract

Use a small, Dataview-safe metadata set unless the repo already has a stronger convention.

| Field | Use |
|-------|-----|
| `title` | Stable display title when the note name alone is not enough |
| `tags` | Classification and filtering |
| `aliases` | Migration-safe alternate note names |
| `kind` | Page type such as `overview`, `concept`, `entity`, `comparison`, `source-summary`, `mapping`, `index` |
| `status` | `bootstrap`, `active`, `partial`, `needs-review`, `historical` |
| `updated` | Last review or meaningful update date |
| `source_count` | Quick signal for source-backed density |
| `cssclasses` | Optional project-safe styling hooks |

### Path-stability rules for vaults
- [ ] Prefer stable note names before moving folders.
- [ ] When a note moves or splits, add `aliases` or mapping notes before cutting over links.
- [ ] Keep attachment placement stable; default new local assets to `raw/assets/`.
- [ ] Treat `.obsidian/templates/` and `.obsidian/snippets/` as shared surfaces that should evolve with the vault.
- [ ] Treat workspace panes, session history, and other user-local `.obsidian` files as non-canonical by default.

## Canonical material boundary
- [ ] List current `canonical material` before structural work starts.
- [ ] Keep authoritative paths stable unless a `migration` is explicitly approved.
- [ ] Prefer companion `wiki` pages, mapping pages, or `aliases` over moving files.
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
- Frontmatter with `title`, `tags`, `aliases`, `kind`, `status`, `updated`, and `source_count`
- `Scope`
- `Canonical material`
- `Current wiki map`
- `First ingest queue` or `Current priorities`
- Links to `indexes/source-map.md`, `indexes/coverage.md`, and `activity/log.md`

### `indexes/source-map.md`
Use a table that makes `raw` coverage easy to audit.

| Source ID | Raw path | Capture type | Planned wiki target | Canonical material touched? | Provenance status | Status |
|-----------|----------|--------------|---------------------|-----------------------------|-------------------|--------|
| `vendor-brief-2026` | `raw/sources/vendor-brief-2026.pdf` | import | `wiki/topics/vendor-landscape.md` | no | linked | summarized |

### `indexes/coverage.md`
Track maintained `wiki` pages against backing evidence.

| Wiki path | Page type | Backing raw or canonical material | Coverage status | Last reviewed | Notes |
|-----------|-----------|-----------------------------------|-----------------|---------------|-------|
| `wiki/topics/vendor-landscape.md` | overview | `raw/sources/vendor-brief-2026.pdf` | partial | `2026-04-06` | backfill provenance for pricing notes |

### `config/obsidian-vault.md`
Keep shared vault rules explicit here.

Suggested sections:
- `Vault mode`
- `Shared .obsidian surfaces`
- `Attachment path`
- `Template usage`
- `Dataview metadata contract`
- `Out-of-scope volatile state`

### `activity/log.md`
Record one append-only entry per mutating batch.

```md
### [YYYY-MM-DD HH:MM] [Batch label]
- Mode: [create|ingest|enrich|derive|improve|migration]
- Summary: [what changed]
- `raw`: [files added or updated]
- `wiki`: [files added or updated]
- `indexes`: [files added or updated]
- `schema`: [files added or updated / unchanged]
- `config`: [files added or updated / unchanged]
- `canonical material`: [unchanged, annotated, or approved exception]
- `provenance`: [what is now linked or what remains missing]
- `derived output`: [none or output path]
- `vault`: [frontmatter, aliases, embeds, or shared `.obsidian/` surfaces changed / unchanged]
- `path map`: [old -> new note names or paths if migration work occurred / none]
- `link/backlink impact`: [what navigation changed and what stayed stable]
- Risks / rollback: [if relevant]
- Follow-up:
  - [next safe batch]
```

## Adapting an imperfect repo
Use additive-first repair when the existing layout is mixed or incomplete.

1. Add `indexes/source-map.md`, `indexes/coverage.md`, and `activity/log.md` before moving anything.
2. Create a safe `raw/` intake area for future evidence.
3. Add or normalize shared `.obsidian/` surfaces that belong to the project, not the user session.
4. Map existing notes into the `wiki` layer with links, companion pages, or summaries.
5. Normalize note metadata, stable note names, and `[[wikilinks]]` before broad enrichment.
6. Backfill `provenance` on the most important pages.
7. Use `scripts/kb_lint.py --root <path> --include-unlayered` when important repo markdown still sits outside the default layers.
8. Escalate to `migration` only when additive repair plus vault normalization cannot meet the goal.

## Architecture exit checklist
- [ ] Layer boundaries are clear.
- [ ] `canonical material` is identified.
- [ ] A minimal `provenance` pattern is chosen.
- [ ] `indexes/source-map.md`, `indexes/coverage.md`, and `activity/log.md` have owners.
- [ ] Shared `.obsidian/` surfaces and `config/obsidian-vault.md` have owners if the repo is a vault.
- [ ] The first batch is additive, reviewable, and non-destructive.
