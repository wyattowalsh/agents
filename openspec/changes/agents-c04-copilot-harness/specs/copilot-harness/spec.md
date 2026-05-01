## ADDED Requirements

### Requirement: Copilot support claims

The Copilot harness lane SHALL distinguish generated instruction/config support from Skills CLI installed-skill inventory.

#### Scenario: Copilot reports zero installed skills

- **GIVEN** the Skills CLI discovers no Copilot-installed skills
- **WHEN** support docs are generated
- **THEN** they do not fabricate skill rows from instruction or config files.
