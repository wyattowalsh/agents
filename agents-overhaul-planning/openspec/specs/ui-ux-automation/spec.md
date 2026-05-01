# ui-ux-automation

## Requirements

### Requirement: Ui Ux Automation

The system SHALL expose doctor, catalog, skill lifecycle, MCP inspection, sync, rollback, docs, and OpenSpec flows through streamlined CLI UX and optional dashboard abstractions.

#### Scenario: validation

- **Given** the canonical manifests and latest repo inventory
- **When** the relevant validation command runs
- **Then** generated docs/config/test fixtures match the manifests or the command fails with actionable remediation.
