# Agent Assets Delta

## ADDED Requirements

### Requirement: APM surface is generated from canonical assets

The repository SHALL treat `agents/`, `instructions/`, and hook registry sources as SSOT and SHALL generate `.apm/` plus root `apm.yml` for APM consumers without copying `skills/` into APM includes.

#### Scenario: Bundle manifest documents APM adapter

- **GIVEN** `agent-bundle.json` describes cross-harness distribution
- **WHEN** the APM integration is active
- **THEN** `adapters.apm` SHALL document install, update, audit, compile, and materialize commands
- **AND** Skills CLI and native plugin adapters SHALL remain the portable install path for repo skills.

#### Scenario: AGENTS.md exposes managed APM section

- **GIVEN** `apm.yml` uses managed `AGENTS.md` compilation markers
- **WHEN** `apm compile` runs against the repository
- **THEN** only the delimited `<!-- apm:start -->` / `<!-- apm:end -->` region SHALL be APM-managed
- **AND** hand-authored content outside those markers SHALL remain maintainer-owned.
