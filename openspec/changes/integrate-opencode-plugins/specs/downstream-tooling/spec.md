# Downstream Tooling Delta

## MODIFIED Requirements

### Requirement: OpenCode Plugin Surfaces Stay Separated

The repository SHALL keep repo-managed OpenCode runtime plugin specs in `opencode.json` while treating TUI-only plugin specs as `~/.config/opencode/tui.json` live-user configuration unless a repo-managed TUI source file is explicitly introduced.

#### Scenario: Adding runtime OpenCode plugins

- **WHEN** a runtime OpenCode npm plugin is added to the repo-managed inventory
- **THEN** `opencode.json` SHALL list the plugin spec with the `@latest` dist-tag
- **AND** validation SHALL assert required runtime plugin specs are present when they are part of a tracked integration.

#### Scenario: Adding TUI-only OpenCode plugins

- **WHEN** a plugin is only used by the OpenCode TUI surface
- **THEN** the plugin SHALL be added to `~/.config/opencode/tui.json` instead of repo `opencode.json`
- **AND** validation SHALL assert known TUI-only plugin specs are absent from repo `opencode.json`.

#### Scenario: Adding OpenCode telemetry plugins

- **WHEN** an OpenCode telemetry plugin needs credential values
- **THEN** repo-managed configuration SHALL document the required environment variable names without committing credential values
- **AND** startup validation SHALL distinguish missing user credentials from plugin load failures.

#### Scenario: Configuring OpenCode plan-review plugins

- **WHEN** the repo-managed OpenCode config includes a plugin that exposes a `submit_plan` tool
- **THEN** the plugin SHALL be configured so only the built-in `plan` agent sees the tool by default
- **AND** validation SHALL assert deprecated broader plan-review plugins are absent from repo `opencode.json`.
