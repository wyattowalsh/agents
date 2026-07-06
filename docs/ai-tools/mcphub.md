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
just mcphub-up
just mcphub-doctor
just mcphub-smoke
```

Do not commit `.env.mcphub`.

## Local Operation

- `just mcphub-up`: start local MCPHub with `npx -y @samanhappy/mcphub`.
- `just mcphub-down`: stop the local PID recorded in `.mcphub/mcphub.pid`.
- `just mcphub-logs`: tail `.mcphub/mcphub.log`.
- `just mcphub-doctor`: check settings, Node/npx, health, and secret presence.
- `just mcphub-smoke`: run health and authenticated `tools/list`.
- `just mcphub-openapi`: export `mcp/mcphub/openapi.json`.

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
- ChatGPT remote MCP URL: `https://mcp.w4w.dev/mcp/tunnel`

MCP endpoints keep bearer auth enabled through `Authorization`. OpenAPI
endpoints are documented by MCPHub as public, so expose the remote URL only
through an authenticated tunnel and keep local MCPHub bound to localhost.

## ChatGPT Tunnel

ChatGPT custom MCP apps/connectors require a remote server; local MCP servers are
not supported by ChatGPT developer mode. The managed public endpoint is
`https://mcp.w4w.dev/mcp/tunnel`, backed by the named Cloudflare Tunnel
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
`mcp/mcphub/mcp_settings.json`. They intentionally overlap across three layers:

- Default/workflow groups: `harness`, `tunnel`, `daily`, `coding`, `research`,
  `review`, `release`, `personal-work`, and `media-work`. For local trim/transcode/thumbnail/GIF work, prefer the repo `/ffmpeg` skill over MCP multimedia servers when the harness has shell access.
- Capability groups: `web-search`, `web-read`, `docs`, `repo`, `browser`,
  `reasoning`, `reasoning-lab`, `media`, `notebooks`, `design`,
  `productivity`, `accounts`, and `references`. The `web-search` and `research`
  groups include `open-websearch` (no API key; opt-in only, not in default
  `harness`). `jupyter-mcp-server` (Datalayer Jupyter MCP; opt-in only) is in `notebooks`,
  `coding`, `heavy`, `credentialed`, and `experimental` (full server), plus
  bounded read subsets in `research` and `review`. Requires a running JupyterLab
  and `JUPYTER_URL` / `JUPYTER_TOKEN` in `.env.mcphub`; kernel tools execute
  arbitrary code.
- Risk/exposure groups: `shared-read`, `credentialed`, `account-backed`,
  `live-browser`, `heavy`, and `experimental`.

The `harness` group is the shared default local harness-facing MCP surface. It
is not the broad daily bundle; it is the highest-value tool set meant to keep
MCP schema/context bloat bounded: Brave Search, DuckDuckGo Search, DDGS
(metasearch/news), Context7, DeepWiki, `llms-txt-explorer` limited to
`list_websites`, Fetch, `fetcher` limited to `fetch_urls`, package metadata,
Chrome DevTools, and Penpot. Use `check_website` only via opt-in workflow groups
(`daily`, `docs`, `research`, `web-read`, `coding`, `review`, `shared-read`) because it
performs agent-controlled HTTP fetches. Prefer DDGS snippet search;
use `fetch_full_content` only for bounded research (large payloads). Broader work should opt into workflow groups such
as `daily`, `coding`, `research`, `review`, or `release`. `tunnel` is the
bounded remote ChatGPT surface and intentionally excludes `llms-txt-explorer`,
personal-account, live-browser, heavy, and experimental tools.

## Adding Or Removing Servers

Edit `config/mcp-registry.json`, regenerate or update
`mcp/mcphub/mcp_settings.json`, then run:

```bash
bash scripts/mcphub/validate-settings.sh
uv run python scripts/sync_agent_stack.py --targets repo,home --check
```

Apply sync only after the preview is expected.

## Tracked Settings vs Runtime Settings

MCPHub reads the tracked baseline from `mcp/mcphub/mcp_settings.json`, which is
generated from `config/mcp-registry.json`. At runtime MCPHub may also write
server connection state, OAuth tokens, and dashboard edits under
`.mcphub/runtime/` (gitignored). Treat the tracked JSON as the repo source of
truth; treat `.mcphub/runtime/` as machine-local overlay state that can diverge
until you regenerate or reconcile from the dashboard.

After editing the registry, run `just mcphub-generate` and restart MCPHub when
upstream transport or URL fields change. Dashboard-only OAuth completion does
not need a registry edit, but you should still verify `/health` and
`just mcphub-smoke` after reconnecting upstream servers.

When replacing a stdio server slug or launch command, also reconcile machine-local
`.mcphub/runtime/mcp_settings.json` (gitignored) or restart MCPHub from the
tracked baseline so the live hub does not keep serving removed servers.

### `package-version-check-mcp` launcher

PyPI `package-version-check-mcp` 1.2.x ships a forward-reference bug in
`version_parser.py` on Python 3.11+. The repo launches it through
`scripts/mcphub/package-version-check-mcp.sh`, which patches cached `uvx`
installs once, then execs `uvx package-version-check-mcp --mode=stdio`.

Warm the launcher before expecting a fast MCPHub connect on cold machines:

```bash
scripts/mcphub/package-version-check-mcp.sh --help
just mcphub-doctor
launchctl kickstart -k "gui/$(id -u)/com.wyattowalsh.mcphub"
```

Remove the launcher when upstream publishes a fixed wheel; until then keep the
bash wrapper as the registry `command`.

## Auth Policy (`auth_policy`)

Registry entries may declare `auth_policy` to document how MCPHub should reach
an upstream server. Prefer OAuth-first upstreams over long-lived API keys when
the provider supports MCP OAuth.

| `auth_policy` | Meaning | Registry examples |
| --- | --- | --- |
| `oauth` | Complete upstream OAuth through MCPHub; no tracked API key | `context7`, `tavily`, `exa` |
| `public-http` | Public streamable HTTP endpoint; no upstream secret | `deepwiki` |
| `account-token` | User-owned account token in env or URL placeholder | `penpot` |
| `api-key` | Provider API key via env placeholder | `brave-search` and other stdio servers |
| `none` | Local stdio or otherwise credential-free upstream | repo-owned MCP servers |

The generator copies transport shape into `mcp_settings.json`: `type` + `url`
for SSE or Streamable HTTP, `type` + `openapi` for OpenAPI-backed tools, and
`command` plus optional `args` for stdio. It does not emit OAuth secrets.
Configure upstream OAuth in MCPHub itself.

## Upstream OAuth via MCPHub Dashboard

For `auth_policy: oauth` servers:

1. Regenerate settings: `just mcphub-generate`.
2. Restart MCPHub: `just mcphub-up` (or reload the affected server from the dashboard).
3. Open the MCPHub dashboard, select the server, and complete the provider OAuth
   flow. MCPHub stores tokens in runtime state under `.mcphub/runtime/`.
4. Confirm the server shows connected in the dashboard and in `/health`.

OAuth servers include `context7`, `tavily`, and `exa` using MCPHub-managed
Streamable HTTP URLs.

## Context7 SSRF Caveat

Do **not** point Context7 at the unauthenticated base
`https://mcp.context7.com/mcp` when the registry expects OAuth. Keep Context7 on
the OAuth endpoint `https://mcp.context7.com/mcp/oauth` with
`transport: streamable-http` and `auth_policy: oauth`.

## Client Notes

Codex receives an enabled Streamable HTTP entry named
`mcphub_group_harness`. OpenCode receives an enabled remote HTTP entry with
the same name, and Grok receives the equivalent local HTTP entry. ChatGPT
receives the public `https://mcp.w4w.dev/mcp/tunnel` endpoint. Managed
harnesses also receive disabled individual server endpoint entries for each
enabled repository MCP server, so users can opt into a narrower server endpoint
without regenerating the full config. Other group and smart-routing fanout stays
inside MCPHub instead of being projected as enabled harness MCP entries.
stdio-oriented clients use
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
- Startup failure: run `just mcphub-doctor`, then inspect `.mcphub/mcphub.log`.
- Degraded `/health`: MCPHub core is up but some enabled upstream servers are
  disconnected. `just mcphub-doctor` reports `degraded (connected/total)`.
  Reconnect OAuth servers from the dashboard or fix env placeholders, then reload
  the affected server.
- Bad group: run `just mcphub-validate`.
- Stale PID with failed health: run `just mcphub-up`; the startup path clears
  managed stale wrapper and child PID state before restarting.
- OpenCode cannot connect: verify `~/.config/opencode/opencode.json` has only
  `mcphub_group_harness` for MCPHub, then run
  `opencode mcp list --pure --log-level ERROR` and expect
  `mcphub_group_harness connected`.
- Codex cannot connect:
  1. Run `just mcphub-doctor && just mcphub-smoke` (hub + harness MCP must pass)
  2. Verify `MCPHUB_BEARER_TOKEN` is set in Codex's environment (`echo $MCPHUB_BEARER_TOKEN` in the same shell, or `launchctl getenv MCPHUB_BEARER_TOKEN` for GUI)
  3. Confirm `~/.codex/config.toml` has `mcphub_group_harness` enabled at `http://127.0.0.1:46683/mcp/harness`
  4. Re-sync: `uv run python scripts/sync_agent_stack.py --apply --targets home`
  5. Optional warm-start: `just mcphub-up` before opening Codex, or use `scripts/mcphub/wrappers/codex`
- Runtime smoke: run `just mcphub-smoke` after `just mcphub-doctor` reports a
  healthy listener.
