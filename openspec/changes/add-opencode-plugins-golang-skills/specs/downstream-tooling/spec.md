# Downstream Tooling Delta

## MODIFIED Requirements

### Requirement: OpenCode Plugin Surfaces Stay Separated

The repository SHALL keep repo-managed OpenCode runtime plugin specs in `opencode.json` while treating TUI-only plugin specs as `~/.config/opencode/tui.json` live-user configuration unless a repo-managed TUI source file is explicitly introduced.

#### Scenario: Adding runtime and TUI plugins from one request

- **WHEN** one setup request includes both OpenCode runtime plugins and a TUI-only plugin
- **THEN** runtime npm plugins SHALL be added to repo-managed and live OpenCode runtime plugin config
- **AND** TUI-only plugins SHALL be registered in live TUI config instead of repo `opencode.json`
- **AND** plugin-specific required provider options SHALL be configured in the same runtime config surface that loads the plugin.
