# MCPHub Control Plane

`mcp/mcphub/mcp_settings.json` is generated from `config/mcp-registry.json`.
MCPHub owns the actual server processes, groups, routing, auth, logs, and OpenAPI
export. Local AI clients connect to MCPHub endpoints instead of launching each
server directly when `mcphub.enabled` is true in the registry.

## Local Files

- `mcp_settings.json`: tracked, secret-free MCPHub settings.
- `.env.mcphub.example`: copy to `.env.mcphub` and fill local secrets.
- `scripts/mcphub/`: local lifecycle, validation, OpenAPI export, smoke, and wrappers.
- `.mcphub/`: local PID/log directory ignored by git. The Cloudflare Tunnel
  sidecar writes its runtime config and logs there when enabled.

## Endpoints

- All servers: `http://127.0.0.1:46683/mcp`
- Group: `http://127.0.0.1:46683/mcp/{group}`
- Harness-safe group: `http://127.0.0.1:46683/mcp/harness-safe`
- Server: `http://127.0.0.1:46683/mcp/{server}`
- Smart Routing, opt-in only: `http://127.0.0.1:46683/mcp/$smart` and `/$smart/{group}`
- OpenAPI export: `http://127.0.0.1:46683/api/openapi.json`

Bearer auth must remain enabled for MCP endpoints. The local bearer value lives
only in `.env.mcphub` as `MCPHUB_BEARER_TOKEN`; it is not stored in
`mcp_settings.json`.

## First Run

```bash
cp .env.mcphub.example .env.mcphub
python3 - <<'PY'
import secrets
print("ADMIN_PASSWORD=" + secrets.token_urlsafe(24))
print("JWT_SECRET=" + secrets.token_urlsafe(48))
print("MCPHUB_BEARER_TOKEN=" + secrets.token_urlsafe(48))
PY
# Replace the placeholders in .env.mcphub with those generated values.
make mcphub-up
make mcphub-doctor
make mcphub-smoke
```

## Public ChatGPT URL

ChatGPT custom MCP apps/connectors require a remote MCP server. This machine
uses the stable named Cloudflare Tunnel `mcphub`; managed harnesses use the
bounded `harness-safe` endpoint:

```text
https://mcp.w4w.dev/mcp/harness-safe
```

Managed harness configs also expose each individual MCPHub server endpoint as a
disabled entry. The only enabled projected endpoint is `harness-safe`; enable a
single server endpoint locally only when a narrower surface is needed.

Set `MCPHUB_TUNNEL_ENABLED=true` in `.env.mcphub` to have the MCPHub LaunchAgent
start that tunnel sidecar automatically after local MCPHub is healthy. Keep the
tunnel credentials path, tunnel token, and optional Zapier catch-hook URL in
`.env.mcphub`; do not commit Cloudflare credentials or webhook URLs.

When `MCPHUB_ZAPIER_WEBHOOK_URL` is set, tunnel startup posts a
`mcphub_tunnel_ready` payload containing the public MCP URL, local MCP URL,
provider, and timestamp so Zapier Central can refresh its handoff state.

## Smart Routing

Smart Routing is disabled by default and has no default database dependency.
To opt in, run a local PostgreSQL instance with pgvector, set
`SMART_ROUTING_ENABLED=true`, set embedding provider variables, and set `DB_URL`
in `.env.mcphub`. Leaving `DB_URL` unset keeps MCPHub in file-backed mode.
