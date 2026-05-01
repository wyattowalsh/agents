# harness-registry

## Requirements

### Requirement: Harness Registry

The system SHALL maintain a canonical harness registry with support tiers, repo artifacts, extension surfaces, config scopes, validation gates, and docs generation metadata.

#### Scenario: validation

- **Given** the canonical manifests and latest repo inventory
- **When** the relevant validation command runs
- **Then** generated docs/config/test fixtures match the manifests or the command fails with actionable remediation.
