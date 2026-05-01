# documentation-truth

## Requirements

### Requirement: Documentation Truth

The system SHALL generate or validate README, docs, AI instructions, and support matrices from canonical manifests.

#### Scenario: validation

- **Given** the canonical manifests and latest repo inventory
- **When** the relevant validation command runs
- **Then** generated docs/config/test fixtures match the manifests or the command fails with actionable remediation.
