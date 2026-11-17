# Design

## Approach

Replace the legacy `package-version` MCP registry entry with the maintained upstream `package-version-check-mcp` package while preserving the existing bounded package-version lookup capability for managed harness groups.

Keep the implementation at the registry/wrapper layer:

- `config/mcp-registry.json` owns the server slug, stdio launch shape, and group membership.
- `scripts/mcphub/package-version-check-mcp.sh` owns the `uvx` invocation and any local runtime patching needed for the audited upstream PyPI release.
- Generated MCPHub and harness outputs are refreshed from the registry rather than hand-edited.

## Data And Control Flow

1. MCP clients connect to MCPHub groups that include `package-version-check-mcp`.
2. MCPHub launches the server with `bash ${REPO_ROOT}/scripts/mcphub/package-version-check-mcp.sh`.
3. The wrapper runs the pinned upstream PyPI package through `uvx --from package-version-check-mcp==1.2.20 package-version-check-mcp --mode=stdio`.
4. Optional rate-limit credentials, such as `GITHUB_PAT`, are read only from the user-owned environment.
5. `scripts/sync_agent_stack.py` and `scripts/generate_mcphub_settings.py` project the replacement slug into repo-owned generated surfaces.

## Integration Points

- Server slug: `package-version-check-mcp`
- Transport: `stdio`
- Launcher: `scripts/mcphub/package-version-check-mcp.sh`
- Default groups: `harness`, `tunnel`, `daily`, `coding`, `review`, `release`, `repo`, `shared-read`, and `research`
- Removal accounting: legacy `package-version` may remain only in explicit removed-server or migration notes.

## Alternatives Rejected

- Keep the legacy Go `package-version` server: rejected because the replacement has broader package-manager coverage and an actively maintained PyPI distribution.
- Add the replacement under a second parallel slug: rejected because duplicate version tools create group ambiguity and stale generated docs.
- Vendor the server into `mcp/`: rejected because the audited upstream package is installable through `uvx` and does not require first-party server ownership.
- Store GitHub credentials in tracked config: rejected because rate-limit credentials must remain user-owned environment values.

## Migration Or Compatibility Notes

The active MCP endpoint slug changes from `/mcp/package-version` to `/mcp/package-version-check-mcp`. No compatibility endpoint is retained because the repository's managed generated surfaces are the supported contract, and remaining legacy references are limited to explicit removal or migration accounting.
