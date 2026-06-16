# Design

## Audit corrections

1. `wagents skills sync -a grok` works; only `wagents install -a grok` is broken.
2. Inventory already scans `~/.grok/skills`; gap is repo-local `.grok/skills` + dedupe.
3. `merge_grok_config` bypasses adapter — delegate to `sync_platform_*("grok")`.
4. JSON `assert_no_config_drops` does not apply to TOML — use `GROK_OWNED_*` preservation.
5. `--platforms grok` is mandatory for isolated home apply.
6. Sanitized repo template must not ship machine-local `plugins.paths`.

## TOML ownership

Two merge modes for owned tables:

| Mode | Prefixes | Semantics |
|------|----------|-----------|
| **Replace** | `models`, `mcp_servers`, `plugins`, `compat`, `telemetry` | Repo policy is source of truth; user tables dropped from preserve path |
| **Blend** | `ui`, `features`, `session`, `tools`, `toolset`, `subagents`, `memory` | Repo keys override; user-only keys in the same table header survive |

`GROK_OWNED_TABLE_PREFIXES` is the union of replace + blend prefixes.

Home merge: strip managed blocks and registry-projected `mcp_servers.*` (even when markers absent), preserve non-owned user tables, render blended policy block, append MCP, assert non-owned tables are not dropped.

Marker-less MCP: before append, remove any `[mcp_servers.<name>]` where `<name>` is in the current registry projection set.

## Policy defaults

- models.default = grok-composer-2.5-fast
- models.web_search = grok-4.20-multi-agent
- ui.yolo = true; permission_mode = always-approve
- features: lsp_tools, codebase_indexing on; telemetry off
- memory + subagents enabled (depth 1 documented only)
- compat.cursor + compat.claude discovery on

## Skills path

SKILLS_CLI_AGENT_ALIASES grok -> claude-code; mirror to ~/.grok/skills after install/sync.

## Env (not in config.toml)

GROK_WEB_FETCH, GROK_MEMORY, GROK_SUBAGENTS, GROK_LSP_TOOLS — document in grok-global.md; check via wagents grok doctor.
