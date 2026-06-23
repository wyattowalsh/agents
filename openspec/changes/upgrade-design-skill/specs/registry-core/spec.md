# Registry Core Delta

## MODIFIED Requirements

### Requirement: Canonical registry vocabulary

The registry core lane SHALL define registry schemas and freeze support tiers for downstream validation, docs generation, and harness projection.

#### Scenario: Custom skill registry uses design slug

- **WHEN** the generated skill catalog index is refreshed
- **THEN** the repo-owned custom skill row SHALL use `name: design`
- **AND** the row SHALL expose use command `/design`
- **AND** no active custom row SHALL remain for `frontend-designer`.

#### Scenario: Chrome DevTools operational skill rows remain active

- **WHEN** the generated skill catalog index is refreshed after integrating Chrome proof into `/design`
- **THEN** exactly one repo-owned custom row SHALL remain for `design`
- **AND** active custom rows SHALL remain for `chrome-devtools`, `chrome-devtools-a11y-debugging`, `chrome-devtools-cli`, `chrome-devtools-debug-optimize-lcp`, `chrome-devtools-memory-leak-debugging`, and `chrome-devtools-troubleshooting`
- **AND** no active curated external rows SHALL remain for folded UI/design/frontend/browser-proof entries after their synthesis is documented under `design`.
