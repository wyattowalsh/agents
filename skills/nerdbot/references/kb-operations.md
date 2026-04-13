# KB Operations

## Default execution order
For any mutating workflow, work in this order unless the task is audit-only:

1. `.obsidian/` shared surfaces when they need to be established or normalized
2. `raw`
3. `wiki`
4. `indexes`
5. `activity log`

This keeps `provenance` current and makes each batch easy to review.

## Shared operating rules
- [ ] Keep every batch additive-first unless the user explicitly approves `migration` work.
- [ ] Stop if the next step would move, rename, or rewrite `canonical material`.
- [ ] Update related `indexes` in the same batch as `raw` or `wiki` changes.
- [ ] Append to the `activity log` after every mutating batch.
- [ ] Treat `derived output` as rebuildable and non-canonical.
- [ ] Preserve or establish Obsidian-native frontmatter, `[[wikilinks]]`, aliases, and embed-safe note names before deeper synthesis.
- [ ] Keep shared `.obsidian/` surfaces reviewable and project-safe; do not mix them with volatile workspace state.

## Create
Use Create when the KB does not exist yet or when the safe path is to add a new layered root.

### Preflight checklist
- [ ] Confirm the KB root.
- [ ] Record topic, scope, and non-goals.
- [ ] Confirm that no existing `canonical material` will be overwritten.
- [ ] Choose the first ingest queue before writing synthesized `wiki` pages.

### Create batch
1. Make the default directories: `.obsidian/`, `raw/`, `wiki/`, `schema/`, `config/`, `indexes/`, and `activity/`.
2. Seed `wiki/index.md`, `indexes/source-map.md`, `indexes/coverage.md`, `config/obsidian-vault.md`, and `activity/log.md` from the bundled assets.
3. Create shared `.obsidian/templates/` and `.obsidian/snippets/` surfaces when they do not exist.
4. Add only the minimum `schema` and `config` stubs needed for the current KB.
5. Record scope, non-goals, and the first ingest queue in the `wiki` root.
6. Append a bootstrap entry to the `activity log`.

### Example create batch
| Path | Change |
|------|--------|
| `wiki/index.md` | Add scope, current map, and initial queue |
| `indexes/source-map.md` | Seed empty source inventory |
| `indexes/coverage.md` | Seed empty coverage inventory |
| `config/obsidian-vault.md` | Add shared vault conventions |
| `activity/log.md` | Add bootstrap entry |

## Ingest
Use Ingest when evidence already exists and the KB needs trustworthy `raw` capture.

### Ingest checklist
- [ ] Copy the original into `raw/sources/`.
- [ ] Route downloaded or clipped local assets into `raw/assets/` when they materially support the source.
- [ ] For sources over `50 MB`, prefer a `raw/` pointer/stub that records checksum, size, original location or URI, and import notes when vendoring the binary is impractical.
- [ ] Add supporting captures or extracts in `raw/captures/` or `raw/extracts/` without modifying the original.
- [ ] Create or refresh a source summary page.
- [ ] Add or update the matching row in `indexes/source-map.md`.
- [ ] Update `indexes/coverage.md` if the new evidence changes planned `wiki` coverage.
- [ ] Append an `activity log` entry with import details and gaps.

### Example ingest batch
| Path | Change |
|------|--------|
| `raw/sources/customer-call-01.mp3` | Preserve original |
| `raw/extracts/customer-call-01.md` | Add transcript or extract |
| `raw/assets/customer-call-01-slide-01.png` | Preserve local supporting asset |
| `wiki/topics/customer-call-01-source-summary.md` | Add source summary |
| `indexes/source-map.md` | Add source row and planned `wiki` targets |
| `activity/log.md` | Record import, provenance status, and follow-up |

## Enrich
Use Enrich when the KB already has evidence and the next safe step is better `wiki` synthesis.

### Enrich checklist
- [ ] Keep `references/kb-operations.md` and `references/page-templates.md` open while choosing the next page shape and batch order.
- [ ] Choose the page shape from `references/page-templates.md`.
- [ ] Keep or establish frontmatter fields that match the vault contract.
- [ ] Verify that the target page can trace to `raw` or declared `canonical material`.
- [ ] Make additive changes: add sections, annotations, or companion pages instead of blind rewrites.
- [ ] Prefer `[[wikilinks]]`, aliases, and stable note names when linking to other vault notes.
- [ ] Update embeds, attachment references, and backlinks in the same batch as note moves or splits.
- [ ] Refresh the `Provenance` section.
- [ ] Refresh affected `indexes` rows in the same batch.
- [ ] Append an `activity log` entry with open questions.

### Reviewable enrich batch
1. Update one `wiki` page.
2. Refresh one row in `indexes/source-map.md` if source use changed.
3. Refresh one row in `indexes/coverage.md`.
4. Refresh aliases, embeds, or note links if the page shape or path changed.
5. Append one `activity log` entry.

## Derive
Use Derive when the user wants a generated artifact that can be rebuilt from the KB.

### Derive checklist
- [ ] Confirm the `raw`, `wiki`, `schema`, and `config` inputs.
- [ ] Choose a non-canonical output path such as `derived/` or `exports/`.
- [ ] Record the recipe or regeneration command.
- [ ] Keep prior `derived output` available until verification passes.
- [ ] Append an `activity log` entry with inputs, output path, and rollback notes.
- [ ] If the output should stay readable in Obsidian, preserve vault-safe links and frontmatter instead of flattening everything to plain prose.

### Derived output example
| Input set | Output | Safe default |
|-----------|--------|--------------|
| `wiki/topics/vendor-landscape.md` + `indexes/source-map.md` | `derived/vendor-landscape-brief.md` | Keep the export rebuildable and do not treat it as `canonical material` |

## Verification gate
Run this check before marking a batch complete:
- [ ] Every changed `wiki` claim has `provenance`.
- [ ] `indexes/source-map.md` and `indexes/coverage.md` reflect the same batch.
- [ ] `schema` and `config` still match the new content or stayed intentionally unchanged.
- [ ] The `activity log` records what changed and what remains unresolved.
- [ ] No `canonical material` was moved, renamed, or rewritten without explicit approval.
- [ ] Any `derived output` can be regenerated from the KB.
- [ ] Obsidian-native links, aliases, embeds, and shared `.obsidian/` surfaces remain valid after the batch.

## Manual fallback when automation is missing
If `scripts/kb_inventory.py`, `scripts/kb_lint.py`, or `scripts/kb_bootstrap.py` are absent, do not invent them. Use the references and `assets/` files directly:

1. Copy the starter shapes from `assets/kb-bootstrap-template.md`, `assets/source-summary-template.md`, and the page templates.
2. Use `references/audit-checklist.md` as the verification gate.
3. Record the manual path in the `activity log` so later automation can reproduce it.
4. For vault work, preserve note metadata, aliases, and `[[wikilinks]]` manually instead of silently downgrading them to plain Markdown links.

If the repo is mixed and the lint script is present, prefer `scripts/kb_lint.py --root <path> --include-unlayered` for read-only audits that need to account for markdown outside the default KB layers.
