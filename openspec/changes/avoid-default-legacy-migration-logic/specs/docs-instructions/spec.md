# Docs Instructions Delta

## MODIFIED Requirements

### Requirement: Generated docs and instruction truth

The docs/instructions lane SHALL consolidate README, docs, support matrices, and AI instructions from registries and fragments after schema freeze.

#### Scenario: Child lane updates a support fragment

- **GIVEN** a child lane changes a manifest or fragment
- **WHEN** docs consolidation runs
- **THEN** generated docs reflect the fragment without child teams editing global docs directly.

#### Scenario: Shared instructions define compatibility discipline

- **GIVEN** `instructions/global.md` defines compatibility guidance
- **WHEN** repo or home harness sync runs
- **THEN** generated bridge files and supported local harness instruction surfaces receive the canonical guidance from `instructions/global.md`
- **AND** agents are instructed not to add migration, legacy, fallback, alias, dual-path, or compatibility code by default without explicit request or concrete evidence.
