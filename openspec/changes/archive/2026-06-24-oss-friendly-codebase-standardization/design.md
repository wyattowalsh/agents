# Design

## Approach

Use the existing generated docs pipeline as the integration point. Add public-safe fields to the shared site model, teach generated docs and the skill catalog UI to consume those fields, and add tests that prove public output no longer confuses local installed inventory with public source metadata.

Keep `config/external-skills.md` as the curated external skill source for this pass. The parser can expose more structured data when it can be derived deterministically from headings, install commands, and adjacent notes, but the change should not require a wholesale manifest migration before the repository is OSS-friendlier.

## Public Skill Row Contract

Generated skill rows should support a comparable public contract across repo-owned, curated external, and installed external skills:

- `name`
- `title`
- `description`
- `sourceType`
- `displaySource`
- `sourceKind`
- `sourceUrl`
- `sourcePath` only when display-safe for public output
- `installSource`
- `installCommand`
- `installable`
- `localInventoryOnly`
- `trustTier`
- `status`
- `provenanceStatus`
- `reviewStatus`
- `targetAgents`
- `installedAgents`
- `riskNotes`
- `promotionPolicy`
- `provenanceEvidence`
- `knowledge`
- existing optional skill metadata such as license, version, author, model, argument hint, and invocation state

## Local Inventory Redaction

Installed inventory should keep enough internal evidence to merge rows and diagnose local state, but generated public display fields should prefer:

1. Curated public source from `config/external-skills.md` when a row matches a curated external skill.
2. A recorded Skills CLI install source when it is a public source identifier.
3. A neutral label such as `local installed inventory` when only an absolute local path is known.

Absolute home-directory paths must not be primary `sourceRoot` or `displaySource` labels in public docs or public JSON indexes.

## Contributor And Safety Documentation

Add concise public documentation that maps:

- install choices
- source-of-truth files
- generated artifacts
- validation commands
- safe external skill audit workflow
- trust boundaries for external docs, generated files, logs, tool output, and local inventory
- cleanup and production-readiness expectations

The documentation should reuse current repo commands and avoid inventing a separate contribution process.

## Catalog UI

Extend the existing operational catalog UI rather than replacing it. Add filters for provenance or review state, supported agents, installability, and local-only inventory. Keep the UI dense, scannable, responsive, accessible, and consistent with the current Starlight docs surface.

## Cleanup And Production Readiness

Treat cleanup as classification first. Safe cleanup can remove or ignore clearly generated, duplicate, stale, or machine-local artifacts only when they are in scope. Uncertain dirty files should be documented for maintainer review rather than deleted.

Production readiness means the public docs build, generated indexes, README generation, OpenSpec validation, package dry-runs, and distribution metadata tests all tell the same story about supported agents, installability, trust, and local/private data boundaries.

## Alternatives Rejected

- Replace `config/external-skills.md` with a new schema immediately: rejected for the first pass because the current file is already the repo source of truth and a staged typed projection is lower risk.
- Hand-edit generated docs pages: rejected because generator-owned surfaces would drift on the next docs generation.
- Hide installed inventory completely: rejected because local inventory is valuable for maintainer diagnostics and curated/installed merge behavior, but it must be labeled safely.
- Remove supported harnesses to simplify the catalog: rejected because preserving supported agent coverage is a goal requirement.

## Compatibility Notes

- Existing generated index consumers may still read `sourceRoot`; preserve it where practical but add safer display fields and migrate UI/docs to those fields.
- CI should continue to use `uv run wagents docs generate --no-installed` for public build parity.
- `--include-installed` remains a local diagnostic mode and must not leak local source labels into public-facing display fields.
