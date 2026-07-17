# Delta: RV MCP remediation

## ADDED Requirements

### Requirement: RV MCP findings closure is evidence-backed

The MCP audit lane SHALL record remediation evidence for RV-scoped MCP findings
before marking the review wave closed.

#### Scenario: RV closure evidence is present

- **WHEN** an RV MCP remediation change is active
- **THEN** it SHALL include a closure matrix with finding IDs and proof commands
- **AND** the proof commands SHALL include MCPHub generation, validation, sync, and smoke coverage where applicable
