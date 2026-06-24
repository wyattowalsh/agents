# Proposal

## Problem

OpenCode was synced to the MCPHub `all-managed` group endpoint while the local
MCPHub process was unhealthy. The current startup scripts can trust a live
wrapper PID even when `/health` fails and port `46683` is not listening, leaving
OpenCode with an enabled MCP entry that cannot connect.

## Intent

Restore OpenCode to a single enabled `mcphub_all` `/mcp` endpoint, make stale
MCPHub process state self-healing, and require generated OpenCode config output
checks before claiming the sync is correct.

## Scope

- Project OpenCode MCPHub through one unified `/mcp` endpoint.
- Remove stale MCPHub fanout entries from merged OpenCode home config.
- Harden MCPHub pid, child-pid, health, and doctor behavior.
- Migrate stale OpenCode TUI `keymap.sections` settings to current `keybinds`.
- Document the expected OpenCode `mcphub_all connected` acceptance check.

## Out Of Scope

- Changing OpenCode model, provider, runtime plugin, or TUI plugin behavior beyond schema-safe TUI shortcut migration.
- Enabling MCPHub Smart Routing by default.
- Removing existing MCPHub group definitions or server registry entries.
