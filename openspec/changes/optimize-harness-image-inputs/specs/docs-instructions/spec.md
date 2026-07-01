## ADDED Requirements

### Requirement: Instructions distinguish enforced image optimization from manual guidance

Shared instructions SHALL tell agents to optimize local image inputs before consumption while distinguishing hard hook/native assurance from manual instruction-only posture.

#### Scenario: Instruction-only harness handles a local image

- **GIVEN** a harness has no repo-managed local pre-consumption image hook
- **WHEN** the shared instructions are followed
- **THEN** the agent SHALL prefer `wagents media optimize-image` or equivalent manual optimization before consuming the image
- **AND** it SHALL NOT claim that the harness enforced pre-consumption resizing.
