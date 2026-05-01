# session-telemetry Specification

## Purpose
Define session telemetry contracts for tracking agent orchestration health, validation evidence, and operational outcomes without exposing secrets.
## Requirements
### Requirement: Session telemetry model

The session telemetry lane SHALL define replay, run graph, token/cost telemetry, and audit-log fields with redaction and retention requirements.

#### Scenario: Session data contains sensitive content

- **GIVEN** telemetry captures prompts, tool calls, or file paths
- **WHEN** artifacts are written
- **THEN** redaction policy is applied before docs or reports expose the data.
