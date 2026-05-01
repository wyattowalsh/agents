# skills-first-extension-model

## Requirements

### Requirement: Skills First Extension Model

The system SHALL prefer Agent Skills for reusable static or CLI-backed capabilities and SHALL require validation, pinning, and lifecycle metadata for external skills.

#### Scenario: validation

- **Given** the canonical manifests and latest repo inventory
- **When** the relevant validation command runs
- **Then** generated docs/config/test fixtures match the manifests or the command fails with actionable remediation.
