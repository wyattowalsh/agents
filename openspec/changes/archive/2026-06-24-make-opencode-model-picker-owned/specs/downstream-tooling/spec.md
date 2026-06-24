# Downstream Tooling Delta

## MODIFIED Requirements

### Requirement: OpenCode Model And TUI Surfaces Stay Current

The repository SHALL keep OpenCode build and plan model defaults repo-managed
while preserving TUI-selectable provider variants for approved alternate model
routes.

#### Scenario: Configuring OpenCode build and plan model defaults

- **WHEN** repo or global OpenCode config is generated
- **THEN** root `model` SHALL be `openai/gpt-5.5`
- **AND** root `small_model` SHALL be `openai/gpt-5.4-mini`
- **AND** `agent.build` SHALL use `openai/gpt-5.5` variant `high`
- **AND** `agent.plan` SHALL use `openai/gpt-5.5` variant `xhigh`.

#### Scenario: Configuring selectable provider variants

- **WHEN** repo or global OpenCode config defines provider behavior
- **THEN** provider options for OpenAI-compatible routes SHALL set `timeout: 600000` and `chunkTimeout: 180000`
- **AND** OpenAI and Vercel OpenAI `gpt-5.5` variants SHALL expose `high` and `xhigh`
- **AND** Vercel xAI Grok 4.3 SHALL expose `max` mapped to `reasoningEffort: "high"`
- **AND** OpenCode Go Kimi K2.6 and Moonshot Kimi for Coding SHALL expose a `max` selector
- **AND** plugin-owned provider options such as `websearch_cited` SHALL be preserved when the corresponding plugin is enabled
