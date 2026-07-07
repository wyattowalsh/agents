## ADDED Requirements

### Requirement: Docs Starlight plugin stack is owner-scoped

The docs site SHALL enable Astro and Starlight plugins only when their package peers, route behavior, content-source needs, and Starlight component override ownership are compatible with the current docs runtime owners.

#### Scenario: Requested plugin is additive

- **GIVEN** a requested plugin adds Markdown processing, a direct MDX component, or a non-conflicting Starlight UI affordance
- **WHEN** the docs site enables the plugin
- **THEN** `docs/astro.config.mjs` SHALL configure the plugin explicitly
- **AND** the plugin SHALL be covered by peer, check, and build validation.

#### Scenario: Requested plugin conflicts with an existing owner

- **GIVEN** a requested plugin would replace an existing theme, sidebar, table-of-contents, search, route, output, or generated-docs owner
- **WHEN** the plugin is not enabled
- **THEN** the docs site SHALL record the exact blocked owner, package status, and evidence in a hand-maintained compatibility ledger.

#### Scenario: Requested plugin needs a content or service source

- **GIVEN** a requested plugin needs changelog entries, OpenAPI specs, versioned docs, blog posts, videos, Obsidian vault data, contributor data, or search service credentials
- **WHEN** that source is not present
- **THEN** the plugin package SHALL still be promoted into direct dependencies when a published package exists
- **AND** runtime activation SHALL remain blocked until the ledger-identified source or service configuration exists.
