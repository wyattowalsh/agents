# docs-instructions Specification

## Purpose
Define documentation and instruction-sync requirements for keeping generated docs, platform bridge files, and source instructions aligned.
## Requirements
### Requirement: Generated docs and instruction truth

The docs/instructions lane SHALL consolidate README, docs, support matrices, and AI instructions from registries and fragments after schema freeze.

#### Scenario: Child lane updates a support fragment

- **GIVEN** a child lane changes a manifest or fragment
- **WHEN** docs consolidation runs
- **THEN** generated docs reflect the fragment without child teams editing global docs directly.

### Requirement: Support matrices preserve surface distinctions

Generated support matrices SHALL distinguish desktop, web/cloud, CLI, editor, and experimental harness variants instead of collapsing products into one row.

#### Scenario: Harness family has multiple variants

- **GIVEN** a registry contains related harness variants such as Claude Code and Claude Desktop
- **WHEN** C08 generates support documentation
- **THEN** each variant is rendered with its own support tier, owner lane, and validation status.

### Requirement: Blind spots are labeled

Docs SHALL label unsupported, unverified, experimental, and quarantine surfaces rather than omitting them or implying support.

#### Scenario: Surface lacks validation evidence

- **GIVEN** a harness or external asset exists in planning but lacks validation evidence
- **WHEN** docs mention that surface
- **THEN** the docs render the correct blind-spot label and next validation owner.

### Requirement: Generated outputs require scheduled consolidation

Generated docs, root README updates, and bridge instruction files SHALL only be refreshed when C08 has stable inputs and an explicitly scheduled generated-output pass.

#### Scenario: Shared docs are dirty from another lane

- **GIVEN** generated docs or root instruction files are dirty outside C08 ownership
- **WHEN** C08 defines docs truth contracts
- **THEN** C08 records the blocker and commits source fragments without overwriting shared generated outputs.
