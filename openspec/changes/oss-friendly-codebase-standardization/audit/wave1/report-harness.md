# Wave 1 Harness Report

Generated: 2026-06-15

## Scope
claude-code, codex, opencode, grok-build, cursor-editor, github-copilot-*, gemini-cli, antigravity, crush, chatgpt, claude-desktop (+ light probes for experimental/planned).

## Executive summary
1. **P0 path leaks** in CLAUDE.md, AGENTS.md, mcp.json, opencode.json, sync-manifest (79× /Users/ww/).
2. **Codex + Copilot + Gemini adapters are stubs**; logic lives in sync_agent_stack.py monolith.
3. **Zero validated harness tiers** — all fixture-plan-only per harness-fixture-support.json.
4. **Grok skills alias** via claude-code + mirror to ~/.grok/skills (documented but no executable fixture).
5. **Copilot inventory risk** — registry requires discovery-only; query errors on github-copilot agent id.
6. **MCP projection fragmented** across render_copilot_mcp, render_gemini_mcp, render_client_mcp.
7. **Committed .claude/settings.local.json** contains hundreds of machine-specific permissions.
8. **OpenCode** mixes machine-tuned config with managed MCP blocks and file: bearer secrets.

## Finding counts (subagents)
- W1-HARNESS-A: 16 findings (claude/codex/opencode)
- W1-HARNESS-B: 22 findings (remaining harnesses)

## Top 5 quick wins
1. Relative includes in CLAUDE.md/AGENTS.md/instructions/*
2. Path-leak CI grep gate
3. Implement codex adapter minimum (TOML merge + entrypoint)
4. Align registry tier language with fixture-plan-only reality
5. Render mcp.json from template without absolute paths
