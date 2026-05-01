# repo-sync Specification

## Purpose
Define repository sync inventory and drift-ledger requirements for distinguishing canonical, generated, merged, and validation-required surfaces.
## Requirements
### Requirement: Repo sync inventory

The repo sync lane SHALL produce a live inventory and drift ledger that classify requested repo paths and identify drift from planning inputs.

#### Scenario: Inventory is available to child teams

- **GIVEN** the foundation run has completed
- **WHEN** a child team reads the repo-sync artifacts
- **THEN** it can identify canonical, generated, planned, experimental, and validation-required surfaces without editing shared docs.
