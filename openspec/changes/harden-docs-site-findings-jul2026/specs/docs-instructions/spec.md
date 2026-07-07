# docs-instructions Delta

## ADDED Requirements

### Requirement: Docs site hardening uses source-owned generation and latest working package proof

The repository SHALL close public docs-site hardening changes through source-owned edits, generated-surface regeneration, latest-working package version proof, and production build validation.

#### Scenario: Generated docs pages are refreshed from source

- **GIVEN** a docs hardening change edits `wagents/docs.py`, catalog rendering, report rendering, or generated site data inputs
- **WHEN** public docs pages, registries, reports, indexes, sidebars, or README output are affected
- **THEN** maintainers SHALL regenerate those outputs with the repo docs/readme generators
- **AND** SHALL NOT hand-edit generated docs pages or generated registries as the source of truth.

#### Scenario: Latest docs package versions remain build-proven

- **GIVEN** the docs app dependency set changes for Astro, Vite, Starlight, or related build tooling
- **WHEN** maintainers claim the dependency set is current and working
- **THEN** they SHALL capture package-version evidence with `npm-check-updates` or equivalent package-version tooling
- **AND** SHALL run Astro type checking and a production docs build with the declared package-manager version.

#### Scenario: Docs production builds do not preserve stale output

- **GIVEN** a docs build output directory contains files from a prior build
- **WHEN** maintainers run the normal docs production build command
- **THEN** the build SHALL remove stale `dist`, `.astro`, and Vercel output artifacts before emitting the new site
- **AND** SHALL preserve expected on-demand Vercel routes after the clean build.

#### Scenario: No-JS install surfaces stay useful

- **GIVEN** the skill install page renders generated install commands
- **WHEN** JavaScript is disabled or JSON hydration fails
- **THEN** the page SHALL still expose pre-rendered command blocks from generated site data
- **AND** SHALL retain a link to the generated JSON source for inspection.

#### Scenario: Catalog browser uses bounded public index data

- **GIVEN** generated external skill catalog rows include audit metadata and install commands
- **WHEN** the public catalog browser hydrates external skill rows
- **THEN** it SHALL consume a generated browser-specific index containing only display-safe row fields
- **AND** the browser index SHALL remain bounded relative to the full catalog index.

#### Scenario: Starlight override placement preserves valid accessible HTML

- **GIVEN** the docs app overrides Starlight `Head` and `SkipLink`
- **WHEN** pages are built
- **THEN** the skip link SHALL render as body content rather than inside `<head>`
- **AND** the custom `Head` override SHALL only emit head-valid metadata, links, and scripts.
