# MCPHub Local Control Plane

MCPHub is the preferred local MCP control plane for this repository. The repo
continues to define servers in `config/mcp-registry.json`, then MCPHub owns
process launch, grouping, bearer-auth routing, logs, OpenAPI export, optional
Smart Routing, and client endpoints.

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

Do not commit `.env.mcphub`.

## Local Operation

- `make mcphub-up`: start local MCPHub with `npx -y @samanhappy/mcphub`.
- `make mcphub-down`: stop the local PID recorded in `.mcphub/mcphub.pid`.
- `make mcphub-logs`: tail `.mcphub/mcphub.log`.
- `make mcphub-doctor`: check settings, Node/npx, health, and secret presence.
- `make mcphub-smoke`: run health and authenticated `tools/list`.
- `make mcphub-openapi`: export `mcp/mcphub/openapi.json`.

The LaunchAgent template at `config/launchd/com.wyattowalsh.mcphub.plist` starts
the same local script. Install or remove it with the Make targets. If
`MCPHUB_TUNNEL_ENABLED=true`, that LaunchAgent also starts the named
Cloudflare Tunnel sidecar after MCPHub is healthy and stops it when MCPHub
stops.

## Endpoints

- All managed servers: `http://127.0.0.1:46683/mcp`
- Group endpoint: `http://127.0.0.1:46683/mcp/{group}`
- Server endpoint: `http://127.0.0.1:46683/mcp/{server}`
- Smart Routing, disabled until configured: `http://127.0.0.1:46683/mcp/$smart`
- Group Smart Routing: `http://127.0.0.1:46683/mcp/$smart/{group}`
- OpenAPI: `http://127.0.0.1:46683/api/openapi.json`
- ChatGPT remote MCP URL: `https://mcp.w4w.dev/mcp/harness-safe`

MCP endpoints keep bearer auth enabled through `Authorization`. OpenAPI
endpoints are documented by MCPHub as public, so expose the remote URL only
through an authenticated tunnel and keep local MCPHub bound to localhost.

## ChatGPT Tunnel

ChatGPT custom MCP apps/connectors require a remote server; local MCP servers are
not supported by ChatGPT developer mode. The managed public endpoint is
`https://mcp.w4w.dev/mcp/harness-safe`, backed by the named Cloudflare Tunnel
`mcphub`.

Set these values only in `.env.mcphub`:

```bash
MCPHUB_PUBLIC_URL=https://mcp.w4w.dev/mcp
MCPHUB_TUNNEL_ENABLED=true
MCPHUB_TUNNEL_PROVIDER=cloudflare
MCPHUB_TUNNEL_PROTOCOL=http2
MCPHUB_TUNNEL_NAME=mcphub
MCPHUB_TUNNEL_HOSTNAME=mcp.w4w.dev
MCPHUB_TUNNEL_TARGET_URL=http://127.0.0.1:46683
MCPHUB_TUNNEL_CREDENTIALS_FILE=~/.cloudflared/<tunnel-id>.json
# Or use MCPHUB_TUNNEL_TOKEN from the Cloudflare dashboard connector command.
```

The launcher writes the effective Cloudflare config to
`.mcphub/cloudflared.yml` so the tunnel always targets the same local MCPHub URL
used by repo clients.

If `MCPHUB_ZAPIER_WEBHOOK_URL` is set, the tunnel launcher posts a
`mcphub_tunnel_ready` JSON payload to Zapier Central with the public MCP URL,
local MCP URL, provider, and timestamp. Keep the real catch-hook URL in
`.env.mcphub`.

## Groups

Managed groups are declared in `config/mcp-registry.json` and emitted into
`mcp/mcphub/mcp_settings.json`:

- `all-managed`
- `code`
- `harness-safe`
- `research`
- `reasoning`
- `browser`
- `data`
- `media`
- `personal`
- `local-ai`
- `experimental`

The `harness-safe` group is the shared harness-facing MCP surface and includes
the approved search, browser, docs, fetch, package metadata, repository
packing, Supabase, Tavily, Trafilatura, DuckDuckGo, and Gmail servers. The
`personal` group can expose account-backed tools and should be treated as
sensitive even on localhost.

## Adding Or Removing Servers

Edit `config/mcp-registry.json`, regenerate or update
`mcp/mcphub/mcp_settings.json`, then run:

```bash
bash scripts/mcphub/validate-settings.sh
uv run python scripts/sync_agent_stack.py --targets repo,home --check
```

Apply sync only after the preview is expected.

## Client Notes

Codex receives an enabled Streamable HTTP entry named
`mcphub_group_harness-safe`. OpenCode receives an enabled remote HTTP entry with
the same name. ChatGPT receives the public
`https://mcp.w4w.dev/mcp/harness-safe` endpoint. Managed harnesses also receive
disabled individual server endpoint entries for each enabled repository MCP
server, so users can opt into a narrower server endpoint without regenerating
the full config. Other group and smart-routing fanout stays inside MCPHub
instead of being projected as enabled harness MCP entries. stdio-oriented
clients use
`scripts/mcphub/remote-stdio.sh`, which calls `mcp-remote` with the bearer token
from `MCPHUB_BEARER_TOKEN`.

Cherry Studio gets managed import packs for all/group/server/smart endpoints.
Perplexity Desktop and Cursor Agent surfaces are documented and wrapper-backed
only unless a verified local MCP config path exists.

ChatGPT Web should use the remote MCP URL above through developer mode or an
OAuth-backed connector flow rather than a fabricated local install state.
GitHub Copilot Web remains plugin/VS Code dependent; GitHub Copilot CLI receives
the managed MCP config through sync.

## Smart Routing

Smart Routing is off by default. To opt in, run a local PostgreSQL database with
pgvector, set `SMART_ROUTING_ENABLED=true`, configure embedding variables, and
set `DB_URL` in `.env.mcphub`. Leaving `DB_URL` unset keeps file-backed mode.

## Troubleshooting

- Missing token: set `MCPHUB_BEARER_TOKEN` in `.env.mcphub`.
- Startup failure: run `make mcphub-doctor`, then inspect `.mcphub/mcphub.log`.
- Bad group: run `make mcphub-validate`.
- Stale PID with failed health: run `make mcphub-up`; the startup path clears
  managed stale wrapper and child PID state before restarting.
- OpenCode cannot connect: verify `~/.config/opencode/opencode.json` has only
  `mcphub_group_harness-safe` for MCPHub, then run
  `opencode mcp list --pure --log-level ERROR` and expect
  `mcphub_group_harness-safe connected`.
- Runtime smoke: run `make mcphub-smoke` after `make mcphub-doctor` reports a
  healthy listener.
