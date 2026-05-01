# ux-cli Specification

## Purpose
Define CLI and UX output contracts for readable, actionable agent workflow status, validation, and error reporting.
## Requirements
### Requirement: CLI automation contracts

The UX/CLI lane SHALL define human-readable and machine-readable command output contracts for doctor, catalog, sync, rollback, audit, skill, MCP, and OpenSpec workflows.

#### Scenario: Automation consumes CLI output

- **GIVEN** an automation invokes a `wagents` command with JSON output
- **WHEN** the command succeeds or fails
- **THEN** it returns stable fields and actionable remediation hints.
