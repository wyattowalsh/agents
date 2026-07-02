<!--
MCP server change PR template. Delete sections that do not apply, but keep
the checklist — reviewers use it to confirm registry wiring and read-only
safety guarantees.
-->

## Summary

<!-- What MCP server(s) changed and why, in 1-3 sentences. -->

## Type of change

- [ ] New MCP server (`mcp/<name>/`)
- [ ] Existing server: tool/resource behavior change
- [ ] Existing server: dependency/config change only
- [ ] `config/mcp-registry.json` registration/update only

## Server checklist (new servers)

- [ ] `server.py` uses `FastMCP("Name")` per `AGENTS.md` §2 MCP conventions
- [ ] `fastmcp.json` points at `server.py` with a `uv` environment
- [ ] `pyproject.toml` declares `fastmcp>=2` and is added to the root `[tool.uv.workspace]` `members`
- [ ] Read-only servers use the shared path-allowlist guard (`wagents/mcp_shared/read_only_paths.py`) rather than a bespoke path check
- [ ] Registered in `config/mcp-registry.json` and `mcp/mcphub/mcp_settings.json` regenerated

## Validation run locally

- [ ] `uv run pytest tests/mcp/` (relevant subset)
- [ ] FastMCP Inspector smoke: handshake + `list_tools` succeed
- [ ] `bash scripts/mcphub/validate-settings.sh`
- [ ] `uv run wagents validate`

## Security notes

- [ ] No credential material embedded in server code or config
- [ ] File-system access is read-only and path-allowlisted, or write access is explicitly justified below

<!-- Any network egress, external API calls, or elevated permissions? -->
