<!-- Suggested path: activity/log.md -->
# Activity Log

## Operating rules
- Append-only.
- Record one entry per mutating batch.
- Name the `raw`, `wiki`, `indexes`, `schema`, and `config` surfaces touched in each batch.
- Call out `canonical material`, `provenance`, and `derived output` decisions explicitly.
- Record vault-impact details whenever frontmatter, aliases, embeds, or shared `.obsidian/` surfaces change.

## Entry template

### [YYYY-MM-DD HH:MM] [Batch label]
- Mode: [create|ingest|enrich|derive|improve|migrate]
- Summary: [one sentence]
- `raw`: [files added or updated]
- `wiki`: [files added or updated]
- `indexes`: [files added or updated]
- `schema`: [files added or updated / unchanged]
- `config`: [files added or updated / unchanged]
- `canonical material`: [unchanged / annotated / approved exception]
- `provenance`: [what is now linked or what remains missing]
- `derived output`: [none / path / regeneration note]
- `vault`: [frontmatter, aliases, embeds, or shared `.obsidian/` surfaces changed / unchanged]
- `path map`: [old -> new note names or paths if migration work occurred / none]
- `link/backlink impact`: [what navigation changed and what stayed stable]
- Risks / rollback: [if relevant]
- Follow-up:
  - [ ]

## Initial entry example

### [YYYY-MM-DD HH:MM] Bootstrap
- Mode: create
- Summary: Initialized the layered KB structure.
- `raw`: seeded directories only
- `wiki`: added `wiki/index.md`
- `indexes`: added `indexes/source-map.md` and `indexes/coverage.md`
- `schema`: unchanged
- `config`: added `config/obsidian-vault.md`
- `canonical material`: none yet
- `provenance`: placeholder sections only
- `derived output`: none
- `vault`: initialized `.obsidian/` shared surfaces and note metadata defaults
- `path map`: none
- `link/backlink impact`: root indexes now provide the first stable navigation surface
- Risks / rollback: remove only the new scaffold if the KB root was created in error
- Follow-up:
  - [ ] Add the first source to `raw/`
