# Skills Lifecycle Delta

## MODIFIED Requirements

### Requirement: Skills-first lifecycle

The skills lifecycle lane SHALL treat Agent Skills as the default portable capability model and require script conformance, provenance, and validation before promotion.

#### Scenario: Renamed script-backed design skill is reviewed

- **GIVEN** the repo-owned `design` skill contains executable scripts
- **WHEN** it is evaluated for completion
- **THEN** `uv run python skills/design/scripts/check.py` SHALL pass
- **AND** focused scanner tests SHALL validate root discovery, ignored traversal, accessibility, motion, and text/layout risk signals
- **AND** live external installs SHALL NOT be run as part of the rename.

#### Scenario: Browser proof uses available tools without setup mutation

- **GIVEN** a rendered UI target is available to `/design`
- **WHEN** Chrome DevTools MCP tools are available in the active harness
- **THEN** `/design` SHALL prefer them for page selection, accessibility snapshot, console/network checks, focus interaction, and screenshots
- **AND** `/design` SHALL NOT mutate MCP registry, harness config, browser launch config, or global installs
- **AND** if Chrome DevTools MCP proof is unavailable, `/design` SHALL state the blocker and fall back to the next available rendered proof tier.
