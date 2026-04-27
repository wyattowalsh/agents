---
name: Cross-Platform Gap Analysis
description: Find gaps in cross-platform coverage — compare what's synced to each platform, identify missing assets.
---

## Task
Compare the agent asset inventory across all supported platforms and identify coverage gaps.

## Platforms to Compare
- Claude Code (`~/.claude/`)
- Codex (`~/.codex/` or project-level)
- Cursor (`.cursor/`)
- Gemini CLI / Antigravity (`~/.config/gemini/`)
- GitHub Copilot (`.github/copilot-instructions.md`)
- OpenCode (`~/.config/opencode/`)

## Analysis Steps

1. **Inventory source assets**
   - List all skills in `skills/` (count, names, descriptions)
   - List all agents in `agents/` (count, names, descriptions)
   - List all MCP servers in `mcp/`
   - Note `instructions/` files and scoped rules

2. **Check platform manifests**
   - `.claude-plugin/plugin.json` — which skills/agents are declared?
   - `.codex-plugin/plugin.json` — which skills/agents are declared?
   - `agent-bundle.json` — canonical bundle manifest coverage
   - Compare to actual files in `skills/` and `agents/`

3. **Identify gaps per platform**
   - Skills present in repo but missing from platform install manifests
   - Agents present in repo but not referenced in bridge files
   - Instructions files not synced to certain platforms
   - MCP servers absent from bundle metadata
   - Version/tag mismatches between repo and plugin manifests

4. **Check cross-platform parity**
   - Is every skill available on every platform? If not, why? (e.g., `context: fork` only works on Claude)
   - Are `user-invocable: false` skills correctly hidden from menus where supported?
   - Do plugin manifests omit fixed `version` fields per repo policy?

5. **Recommend prioritization**
   - Rank gaps by user impact (e.g., Copilot missing 10 skills vs Cursor missing 1)
   - Flag internal-only skills (`metadata.internal: true`) that leaked to public manifests
   - Suggest which assets to add next based on platform-specific capabilities

## Output Format
Return a structured gap report:
- **Coverage matrix**: Rows = assets, columns = platforms, cells = present/missing/unsupported
- **Top 5 gaps**: Highest-impact missing assets per platform
- **Recommendations**: Specific actions to close gaps, with file paths and edit suggestions
