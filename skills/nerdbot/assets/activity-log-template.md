<!-- Suggested path: activity/log.md -->
# Activity Log

## Operating rules
- Append-only.
- Record one entry per mutating batch.
- Name the `raw`, `wiki`, and `indexes` touched in each batch.
- Call out `canonical material`, `provenance`, and `derived output` decisions explicitly.

## Entry template

### [YYYY-MM-DD HH:MM] [Batch label]
- Mode: [create|ingest|enrich|derive|improve|migration]
- Summary: [one sentence]
- `raw`: [files added or updated]
- `wiki`: [files added or updated]
- `indexes`: [files added or updated]
- `schema`: [files added or updated / unchanged]
- `config`: [files added or updated / unchanged]
- `canonical material`: [unchanged / annotated / approved exception]
- `provenance`: [what is now linked or what remains missing]
- `derived output`: [none / path / regeneration note]
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
- `config`: unchanged
- `canonical material`: none yet
- `provenance`: placeholder sections only
- `derived output`: none
- Risks / rollback: remove only the new scaffold if the KB root was created in error
- Follow-up:
  - [ ] Add the first source to `raw/`
