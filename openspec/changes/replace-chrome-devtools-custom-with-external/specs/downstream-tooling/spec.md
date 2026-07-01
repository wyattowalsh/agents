# Downstream Tooling Delta

## MODIFIED Requirements

### Requirement: Imported Chrome DevTools Skills Preserve Provenance

Imported Chrome DevTools skills SHALL retain clear provenance and local adaptation notes.

#### Scenario: Chrome DevTools skills are curated-external catalog rows

- **WHEN** the Chrome DevTools skill family is integrated from `ChromeDevTools/chrome-devtools-mcp`
- **THEN** the repository SHALL NOT vend copies under `skills/chrome-devtools*`
- **AND** six curated-external catalog rows SHALL advertise upstream skills `chrome-devtools`, `chrome-devtools-cli`, `a11y-debugging`, `debug-optimize-lcp`, `memory-leak-debugging`, and `troubleshooting`
- **AND** each row SHALL record source URL, commit SHA, access date, Apache-2.0 license, upstream author `Google LLC`, and package version `0.23.0` in manifest or authoring metadata
- **AND** install commands SHALL use `npx skills add github:ChromeDevTools/chrome-devtools-mcp` with named `--skill` selectors.

#### Scenario: Downstream surfaces hand off browser debugging to upstream skills

- **WHEN** downstream install, sync, README, or docs surfaces are generated after Chrome DevTools externalization
- **THEN** they SHALL advertise curated-external install rows for the six upstream Chrome DevTools skills
- **AND** they SHALL NOT advertise active custom `skills/` rows for `chrome-devtools*`
- **AND** `/design` SHALL continue to document UI-facing Chrome proof while routing standalone browser debugging to the upstream skill IDs.