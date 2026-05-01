# openspec-governance

## Requirements

### Requirement: Openspec Governance

The system SHALL map major implementation work to OpenSpec proposals, designs, task lists, and spec deltas, preserving existing repo OpenSpec assets.

#### Scenario: validation

- **Given** the canonical manifests and latest repo inventory
- **When** the relevant validation command runs
- **Then** generated docs/config/test fixtures match the manifests or the command fails with actionable remediation.
