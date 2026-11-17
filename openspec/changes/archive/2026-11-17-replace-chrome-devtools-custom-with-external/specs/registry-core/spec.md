# Registry Core Delta

## MODIFIED Requirements

### Requirement: Canonical registry vocabulary

The registry core lane SHALL define registry schemas and freeze support tiers for downstream validation, docs generation, and harness projection.

#### Scenario: Chrome DevTools family uses curated-external rows only

- **WHEN** the generated skill catalog index is refreshed after Chrome DevTools externalization
- **THEN** exactly six curated-external rows SHALL remain active for `chrome-devtools`, `chrome-devtools-cli`, `a11y-debugging`, `debug-optimize-lcp`, `memory-leak-debugging`, and `troubleshooting`
- **AND** zero active custom rows SHALL remain for `chrome-devtools`, `chrome-devtools-a11y-debugging`, `chrome-devtools-cli`, `chrome-devtools-debug-optimize-lcp`, `chrome-devtools-memory-leak-debugging`, or `chrome-devtools-troubleshooting`
- **AND** each curated-external row SHALL identify `ChromeDevTools/chrome-devtools-mcp` as install source
- **AND** each row SHALL publish `syncKind: skills-cli` so `wagents skills sync` preserves the pinned audited `github:ChromeDevTools/chrome-devtools-mcp@...` command rather than rebuilding from an unpinned source.
