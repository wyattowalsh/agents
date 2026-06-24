## MODIFIED Requirements

### Requirement: Docs page density

Generated skill, agent, and MCP catalog pages SHALL default to `summary` density unless `docs-density: standard` is set in source frontmatter.

Summary density SHALL:

- omit duplicated inline sections when full source disclosure exists in collapsed details
- move metadata tables into collapsed details blocks
- emit compact provenance one-liners instead of source Asides
- cap research prose sections

#### Scenario: Generated catalog page uses summary density

- **GIVEN** a generated catalog page has source disclosure in collapsed details
- **WHEN** `uv run wagents docs generate --no-installed` renders the page
- **THEN** duplicate inline source sections are omitted above the disclosure
- **AND** metadata and provenance remain available without expanding public page length unnecessarily.

### Requirement: Docs verbosity lint

The `wagents docs lint` command SHALL scan committed MDX under `docs/src/content/docs/` for forbidden boilerplate, duplicate headings above/below SKILL disclosures, and soft line caps.

CI SHALL run `wagents docs lint` in warn mode (non-blocking) after `wagents docs generate`.

A committed baseline manifest at `planning/manifests/docs-verbosity-baseline.json` SHALL record per-page line counts for regression comparison.

#### Scenario: Docs lint reports verbosity drift

- **GIVEN** committed MDX contains duplicated boilerplate or exceeds the baseline
- **WHEN** `uv run wagents docs lint` runs
- **THEN** the command reports the affected page and rule
- **AND** strict mode exits nonzero when warnings remain.
