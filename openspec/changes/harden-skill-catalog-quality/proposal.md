# Change: Harden Skill Catalog Quality

## Summary

Add structured audit metadata and deterministic validation hooks for repo-owned and curated external skill catalog entries. The change keeps Bucket A source-first: maintainers edit authoring MDX and regenerate derived catalog/index surfaces.

## Motivation

The skill overhaul audit found that curated external entries need stronger provenance, executable-surface, and adapter-risk evidence before promotion. Existing schemas and index plumbing preserve basic trust/status fields but do not expose enough structured evidence for validation, docs-steward review, or sync dry-run governance.

## Scope

- Extend authoring and generated catalog schemas with optional audit metadata.
- Preserve optional audit fields through `wagents.skill_index`.
- Tighten quarantine trigger validation for the security register.
- Document docs-steward as a required post-change review step for skill/catalog/public docs changes.

## Non-Goals

- No live external skill installs.
- No `wagents skills sync --apply`.
- No mass promotion or demotion of curated external entries in this change.
- No hand edits to generated catalog pages or generated registries.
