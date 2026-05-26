# Downstream Tooling Delta

## MODIFIED Requirements

### Requirement: OpenCode Model And TUI Surfaces Stay Current

The repository SHALL keep repo-managed OpenCode model configuration explicit for supported build and plan routes while keeping TUI-only shortcuts in the live user TUI config unless a repo-owned TUI source file is introduced.

#### Scenario: Configuring OpenAI GPT-5.5

- **WHEN** repo-managed OpenCode config defines `openai/gpt-5.5`
- **THEN** provider options SHALL set `timeout: 600000`, `chunkTimeout: 180000`, and `setCacheKey: true`
- **AND** `models.gpt-5.5.variants` SHALL define `high` and `xhigh`
- **AND** each OpenAI variant SHALL include `reasoning.encrypted_content`, `reasoningSummary: "auto"`, and `textVerbosity: "low"`
- **AND** build agents SHALL use `variant: "high"`
- **AND** plan agents SHALL use `variant: "xhigh"`.

#### Scenario: Customizing OpenCode TUI shortcuts

- **WHEN** OpenCode TUI shortcuts are customized on this machine
- **THEN** `~/.config/opencode/tui.json` SHALL use the current `keybinds` schema
- **AND** stale `keymap.sections` entries SHALL NOT be added.

#### Scenario: Recovering from session-local server errors

- **WHEN** one OpenCode session loops on OpenAI `server_error` while fresh pure and plugin-loaded `openai/gpt-5.5` runs succeed
- **THEN** operators SHALL treat the failure as session-local before changing model defaults
- **AND** recovery SHALL preserve request IDs, stop only affected session processes, back up `opencode.db`, inspect incomplete assistant turns and encrypted reasoning parts, and quarantine or archive the affected session.
