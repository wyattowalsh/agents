# Delta: Document Cursor Plannotator home hooks

## ADDED Requirements

### Requirement: Cursor Plannotator hooks are documented on the instruction surfaces

Harness-config, AGENTS.md, the cursor-cli overlay, and harness-master SHALL
describe home-only Cursor Plannotator hooks (`CreatePlan` / `SwitchMode`), the
fail-open contract, `--no-plannotator-hooks`, and `wagents cursor-cli
plannotator` / doctor checks.

#### Scenario: Overlay names the home gates

- **WHEN** Agent CLI starts in this repo
- **THEN** `instructions/cursor-cli-global.md` SHALL mention home Plannotator
  hooks on `CreatePlan` and `SwitchMode`
- **AND** it SHALL state that project hooks stay fleet-only

#### Scenario: AGENTS.md matrix includes Cursor home hooks

- **WHEN** maintainers read the Plannotator cross-harness matrix
- **THEN** Cursor home hooks SHALL appear beside Grok CLI + skills + hooks and
  the OpenCode npm plugin
