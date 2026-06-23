# Downstream Tooling Delta

## MODIFIED Requirements

### Requirement: JSON Interfaces Are Preferred For Automation

Automation SHALL consume OpenSpec JSON commands instead of scraping markdown or terminal UI output.

#### Scenario: Design rename updates downstream skill commands

- **WHEN** downstream install, sync, README, or docs surfaces are generated
- **THEN** they SHALL refer to `--skill design` and `/design`
- **AND** `uv run wagents skills sync --dry-run --format json` SHALL preview the renamed custom skill without applying live installs.

#### Scenario: Downstream surfaces do not advertise folded wrappers

- **WHEN** downstream install, sync, README, or docs surfaces are generated after the fold
- **THEN** they SHALL NOT advertise repo-owned custom skill commands for folded `chrome-devtools*` wrapper skills
- **AND** they SHALL NOT advertise active curated install rows for folded UI/design/frontend/browser-proof external rows
- **AND** they SHALL continue to preserve the underlying Chrome DevTools MCP registry/config surfaces unchanged.
