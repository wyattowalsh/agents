# Downstream Tooling Delta

## MODIFIED Requirements

### Requirement: MCPHub endpoint projection is source-traceable

Generated downstream tool artifacts SHALL be derived from canonical repo sources and SHALL document their owning source file or command.

#### Scenario: OpenCode receives a unified MCPHub endpoint

- **GIVEN** `mcphub.enabled` is true in the MCP registry
- **WHEN** OpenCode global MCP configuration is rendered and merged
- **THEN** OpenCode SHALL receive exactly one enabled MCPHub entry named `mcphub_all`
- **AND** that entry SHALL point to the unified `/mcp` endpoint
- **AND** stale OpenCode MCPHub group, server, or smart entries SHALL be removed from the merged output
- **AND** bearer auth SHALL use an environment placeholder rather than a literal token.

#### Scenario: OpenCode TUI config uses the active keybind schema

- **GIVEN** the live OpenCode TUI config contains stale `keymap.sections` shortcut settings
- **WHEN** OpenCode home sync merges TUI-only plugin settings
- **THEN** the stale `keymap` object SHALL be removed
- **AND** known shortcut settings SHALL be migrated to current `keybinds` names
- **AND** existing `keybinds` values SHALL take precedence over migrated values.
