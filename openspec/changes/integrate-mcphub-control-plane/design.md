# Design

## Control Plane

`config/mcp-registry.json` keeps every direct server definition. The new
`mcphub` section declares local endpoint settings, group taxonomy, auth env var,
client projection preferences, settings path, OpenAPI export path, and Smart
Routing defaults.

`mcp/mcphub/mcp_settings.json` is generated from the registry and contains:

- all tracked MCP servers,
- all managed groups,
- `systemConfig.routing` with global and group routes enabled,
- bearer auth enabled on the `Authorization` header,
- `jsonBodyLimit` set to `5mb`,
- `skipAuth` set to `false`,
- Smart Routing disabled by default.

## Local Launch

The default lifecycle is local Node execution:

- `scripts/mcphub/up.sh` and `ensure-running.sh` start `npx -y @samanhappy/mcphub`.
- `.env.mcphub` is loaded when present and never tracked.
- `.mcphub/mcphub.pid` and `.mcphub/mcphub.log` are ignored local state.
- `down.sh`, `logs.sh`, `doctor.sh`, `smoke.sh`, and `export-openapi.sh` operate
  against `http://127.0.0.1:46683/mcphub-f99249855f4ff7571130`.

No Docker daemon, Docker socket mount, privileged container, or home-directory
mount is required.

## Client Projection

When `mcphub.enabled` is false or absent, current direct renderers are preserved.
When enabled:

- Codex receives Streamable HTTP MCP entries with `bearer_token_env_var`.
- OpenCode receives stdio bridge entries because its remote header handling may
  pass env placeholders literally.
- Other stdio-oriented clients receive `scripts/mcphub/remote-stdio.sh`, which wraps
  `mcp-remote` and injects the bearer token at runtime.
- Cherry Studio receives managed import packs for all, group, server, and smart
  endpoints.
- Smart endpoints are rendered but disabled until Smart Routing is configured.

## Security

Tracked files contain placeholders only. `MCPHUB_BEARER_TOKEN`,
`ADMIN_PASSWORD`, `JWT_SECRET`, database credentials, OAuth secrets, and provider
API keys remain local. Doctor and smoke scripts report token presence only.

## Rollback

Set `mcphub.enabled` to `false` or remove the `mcphub` registry section, rerun
sync, and clients return to direct per-server projection. Stop local MCPHub with
`make mcphub-down` and unload the LaunchAgent if installed.
