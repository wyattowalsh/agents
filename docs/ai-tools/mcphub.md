# MCPHub Local Control Plane

MCPHub is the preferred local MCP control plane for this repository. The repo
continues to define servers in `config/mcp-registry.json`, then MCPHub owns
process launch, grouping, bearer-auth routing, logs, OpenAPI export, optional
Smart Routing, and client endpoints.

Production launch uses the repository-owned, content-addressed downstream built
from the audited `@samanhappy/mcphub@1.0.32` distribution. Its exact lock,
upstream tarball identity, owned sources, patches, materialized outputs, and
conformance result are verified before a runtime digest can be selected. The
launcher performs no registry resolution, live patching, or module-loader
injection.

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

- `just mcphub-up`: start the selected, verified content-addressed MCPHub
  runtime without dependency resolution.
- `just mcphub-down`: stop the LaunchAgent if loaded, then the local PID in
  `.mcphub/mcphub.pid`, then reap leftover clones.
- `just mcphub-reap-strays`: kill leaked `@samanhappy/mcphub` trees and
  detached ffmpeg/package-version sidecars; keep the managed singleton.
- `just mcphub-logs`: tail `.mcphub/mcphub.log`.
- `just mcphub-doctor`: check settings, runtime/content identity, listeners,
  health, secret presence, and stray hub count.
- `just mcphub-smoke`: run health and authenticated `tools/list`.
- `just mcphub-openapi`: export `mcp/mcphub/openapi.json`.

MCPHub is a singleton. Harness wrappers (`ensure-running.sh`) wait for the
loaded LaunchAgent instead of resolving or launching another package when
`/health` is slow. `launch-agent-run.sh` reaps stray clones before start and
launches the child in a new session so cleanup can kill the process group.

The LaunchAgent template at `config/launchd/com.wyattowalsh.mcphub.plist` starts
the same local script. KeepAlive restarts only on unsuccessful exit, with a
15s throttle. Install or remove it with `just mcphub-install-launch-agent`
and `just mcphub-uninstall-launch-agent`. If
the remote-ready gates pass and `MCPHUB_TUNNEL_ENABLED=true`, that LaunchAgent
may start the named Cloudflare Tunnel sidecar after MCPHub is healthy and stop
it when MCPHub stops. The tracked default is disabled.

This file is the operator SSOT for MCPHub. The public site page `/mcp/mcphub/`
is the generated first-party **metadata** package page, not this runbook.

## Endpoints

- All managed servers: `http://127.0.0.1:46683/mcp`
- Group endpoint: `http://127.0.0.1:46683/mcp/{group}`
- Server endpoint: `http://127.0.0.1:46683/mcp/{server}`
- Smart Routing, disabled until configured: `http://127.0.0.1:46683/mcp/$smart`
- Group Smart Routing: `http://127.0.0.1:46683/mcp/$smart/{group}`
- OpenAPI: `http://127.0.0.1:46683/api/openapi.json`
- Things++ local bearer group: `http://127.0.0.1:46683/mcp/things`
- Things++ remote OAuth origin: `http://127.0.0.1:46684/mcp/things`
- Things++ ChatGPT resource: `https://mcp.w4w.dev/mcp/things`

MCP endpoints keep authorization enabled. General local endpoints use the
loopback bearer policy. Things++ separates credential classes by accepted
listener: port 46683 accepts only the local bearer; port 46684 accepts only
MCPHub OAuth access tokens for the exact public resource. Caller-controlled
forwarding headers cannot change that identity. The local bearer listener
rejects those headers with HTTP 400. The remote OAuth listener ignores them
because Cloudflare Tunnel injects `cf-connecting-ip` and `x-forwarded-*` on
every public request; origin identity stays socket-only and
`forwardedHeadersTrusted` remains false.

## Things++ ChatGPT OAuth Ingress

The Things++ ChatGPT app uses only
`https://mcp.w4w.dev/mcp/things`, backed by the named Cloudflare Tunnel
`mcphub` targeting OAuth-only loopback port 46684. It never exposes the local
bearer listener, an individual backend, a generic group, or a Smart Routing
endpoint.

OAuth discovery uses `https://mcp.w4w.dev/.well-known/oauth-protected-resource/mcp/things`
and both authorization-server well-knowns: the origin-root
`/.well-known/oauth-authorization-server` and the RFC 8414 issuer-path
`/.well-known/oauth-authorization-server/mcp/things`. Issuer is
`https://mcp.w4w.dev/mcp/things`, so clients that insert the well-known suffix
in front of that path must not 404. Apex `GET /` is a small HTML landing that
names the MCP resource. Trailing-slash variants stay content-free 404. Capture
mode returns `401` plus `WWW-Authenticate` on
`GET`/`POST /mcp/things` and `503` on `/oauth/authorize` until public
activation. Cloudflare HTTP→HTTPS is a zone setting; the origin metadata URLs
are HTTPS either way.

Remote ingress and Things tool dispatch default disabled. Authorization for an
implementation or incident-repair run does not replace activation evidence.
Activation first requires the complete offline and local read-only gates, a
current redacted ChatGPT observed-wire record, exact callback and
registration-mode approval, a content/config/route-manifest-bound unexpired
activation receipt, and explicit user approval for remote apply.

Tracked/local-only configuration keeps these values secret-free or in
`.env.mcphub`; the runtime refuses a public bind while readiness is false:

```bash
MCPHUB_PUBLIC_URL=https://mcp.w4w.dev/mcp/things
MCPHUB_TUNNEL_ENABLED=false
MCPHUB_TUNNEL_PROVIDER=cloudflare
MCPHUB_TUNNEL_PROTOCOL=http2
MCPHUB_TUNNEL_NAME=mcphub
MCPHUB_TUNNEL_HOSTNAME=mcp.w4w.dev
MCPHUB_TUNNEL_TARGET_URL=http://127.0.0.1:46684
MCPHUB_TUNNEL_CREDENTIALS_FILE=~/.cloudflared/<tunnel-id>.json
# Or use MCPHUB_TUNNEL_TOKEN from the Cloudflare dashboard connector command.
```

The launcher writes the effective Cloudflare config to
`.mcphub/cloudflared.yml` so the tunnel can target only the OAuth listener.
It must not target port 46683.

If `MCPHUB_ZAPIER_WEBHOOK_URL` is set, the tunnel launcher posts a
`mcphub_tunnel_ready` JSON payload to Zapier Central with the public MCP URL,
OAuth-loopback URL, provider, and timestamp. Keep the real catch-hook URL in
`.env.mcphub`. A webhook notification is not readiness evidence.

OAuth uses Client ID Metadata Documents (CIMD) as the primary registration
mode. Dynamic Client Registration is allowed only as a strict fallback when a
current observed ChatGPT flow selects it. PKCE is `S256` only; resource and
audience are exactly `https://mcp.w4w.dev/mcp/things`; RFC 9207 issuer binding
is required. `things.read`, `things.write`, and `things.admin` are independent
Things authorization scopes and imply none of one another. The durable
ChatGPT profile additionally requires `offline_access` as refresh capability
only: it permits refresh-token issuance but grants no Things permission,
implies no Things scope, and cannot satisfy a tool's minimum scope.

Capture evidence uses the closed
`platforms/chatgpt/things-plus-plus/observed-wire-record.schema.json` v1.1
contract. Only `status: observed-pass` with an unexpired RFC 3339 window,
capture-receipt/callback/internal digest binding, exact scope and refresh-only
`offline_access` facts, resource/PKCE/protocol/discovery proof, fixed capture
route statuses, verified redactions, and prohibited-data absence may feed public
activation. The record has no free-form field and must never contain a cookie,
token, code, verifier, state, account identifier, or private Things content.
The capture runtime/receipt is capped at 30 minutes. Its finalized record binds
that receipt and a capture time inside the receipt window, but has a distinct
freshness expiry of at most 24 hours so evidence may safely outlive capture.

Static, non-secret registration guidance, Project instructions, safety rules,
and test prompts live in `platforms/chatgpt/things-plus-plus/`. That bundle does
not create a ChatGPT app, Project, connector, or any live state.

## Groups

Managed groups are declared in `config/mcp-registry.json` and emitted into
`mcp/mcphub/mcp_settings.json`. They intentionally overlap across three layers:

- Things++ group: `things` is the sole group that contains `things-core`,
  `things-shortcuts`, or `things-native`. It exposes their exact qualified
  41+21+8 union and is never a member of a generic group. Local bearer and
  remote OAuth clients use the same `/mcp/things` group path and normalized
  70-tool catalog.
- Default/workflow groups for non-Things capabilities: `harness`, `daily`, `coding`, `research`,
  `review`, `release`, `personal-work`, and `media-work`. For local trim/transcode/thumbnail/GIF work, prefer the repo `/ffmpeg` skill over MCP multimedia servers when the harness has shell access.
- Candidate group: `candidate-corpus` exposes the 15 audited, activation-eligible
  candidate MCP servers to the default, Codex, Grok, and OpenCode clients.
  `langfuse-mcp` and `papersflow` stay **enabled** in the registry (do not disable
  any MCP for credential readiness). Operator-owned credentials and
  positive/negative/revoke-logout path verification are still required before
  treating either as a completed live install; missing secrets fail at runtime,
  not via registry `enabled: false`.
- Capability groups: `web-search`, `web-read`, `docs`, `repo`, `browser`,
  `reasoning`, `reasoning-lab`, `media`, `notebooks`, `data`, `design`,
  `productivity`, `accounts`, and `references`. The `web-search` and `research`
  groups include `open-websearch` (no API key; opt-in only, not in default
  `harness`). `jupyter-mcp-server` (Datalayer Jupyter MCP; opt-in only) is in `notebooks`,
  `coding`, `heavy`, `credentialed`, and `experimental` (full server), plus
  bounded read subsets in `research` and `review`. Requires a running JupyterLab
  and `JUPYTER_URL` / `JUPYTER_TOKEN` in `.env.mcphub`; kernel tools execute
  arbitrary code. `qsv` (dathere/qsv tabular wrangling MCP; opt-in only) is primary
  in capability group `data`, and is also attached to `coding` and `research`. It is
  **not** in default `harness` or the `things` group. Launch via
  `scripts/mcphub/qsv-stdio.sh` against a machine-local build at
  `mcp/servers/qsv-agent-skills` (gitignored) with local `qsv`/`qsvmcp` on PATH.
  Default filesystem allowlist is repo root + `$HOME/dev` (`QSV_MCP_ALLOWED_DIRS`).
  Treat CSV/Excel cell contents as untrusted data. `scrapling` (CSS-targeted scraping and optional browser sessions;
  opt-in only) is in `research`, `media-work`, `live-browser`, `heavy`, and
  `experimental` (full server), plus bounded `get`/`bulk_get` in `web-read` and
  bounded `get` in `shared-read`. Browser tools require maintainer `scrapling install`;
  treat scraped content as untrusted evidence.
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
as `daily`, `coding`, `research`, `review`, or `release`. Things clients do not
inherit any of those groups; they attach only to `things`.

### Progressive attach and tool subsets

Treat MCP tool schemas as a token tax (see AGENTS.md token-efficacy and
`/harness-config/token-efficacy/`). Control-plane progressive attach:

1. Connect local harnesses to **`/mcp/harness`** (or the client projection that
   enables only the `harness` group) — never attach all 69 servers by default.
2. Opt into workflow/capability groups when the task needs them.
3. Prefer **per-server `tools[]` allowlists inside group membership** when a
   server's full catalog is large or high-risk (pattern already used for
   `llms-txt-explorer` and `fetcher` in `harness`).
4. Do not conflate host progressive discovery (MCP client best practices) with
   server-side FastMCP Tool Search transforms — use hub groups/subsets for
   third-party servers; Tool Search pilots only on multi-tool first-party
   packages we own.
5. Skills-first dual surface: prefer `/ffmpeg` and other skills over MCP when
   the skill covers the job (see `skills/mcphub-operator/references/group-picker.md`).

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

When replacing a stdio server slug or launch command, reconcile machine-local
runtime settings from the tracked baseline so the live hub does not keep serving
removed servers:

```bash
just mcphub-reconcile-runtime --warm --restart
```

This copies `mcp/mcphub/mcp_settings.json` to `.mcphub/runtime/mcp_settings.json`
with `cp -f`, warms `package-version-check-mcp`, and kickstarts the LaunchAgent.

### `package-version-check-mcp` launcher

PyPI `package-version-check-mcp==1.2.20` ships a forward-reference bug in
`version_parser.py` on Python 3.11+. The repo launches it through
`scripts/mcphub/package-version-check-mcp.sh`, which patches cached `uvx`
installs once, then execs `uvx --from package-version-check-mcp==1.2.20 ... --mode=stdio`.

Registry `startup_timeout_sec` is **240** because cold `uvx` resolve can exceed 90s.
Warm the launcher before expecting a fast MCPHub connect on cold machines:

```bash
just mcphub-reconcile-runtime --warm --restart
# or manually:
scripts/mcphub/package-version-check-mcp.sh --help
just mcphub-doctor
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
the same name, and Grok receives the equivalent local HTTP entry. Things-aware
managed harnesses receive one distinct entry named `mcphub_group_things` at
`http://127.0.0.1:46683/mcp/things`. ChatGPT receives only the public
`https://mcp.w4w.dev/mcp/things` resource through OAuth. No client receives a
direct `things-core`, `things-shortcuts`, or `things-native` route, and Things
servers are not projected through the general `harness` group. Managed
harnesses may still receive disabled individual endpoint entries for unrelated
repository MCP servers. Other non-Things group and Smart Routing fanout stays
inside MCPHub instead of being projected as enabled harness MCP entries.
stdio-oriented clients use
`scripts/mcphub/remote-stdio.sh`, which calls `mcp-remote` with the bearer token
from `MCPHUB_BEARER_TOKEN`.

Cherry Studio gets managed import packs for all/group/server/smart endpoints.
Perplexity Desktop and Cursor Agent surfaces are documented and wrapper-backed
only unless a verified local MCP config path exists.

ChatGPT Web should use the Things++ resource above through its OAuth-backed app
flow rather than a fabricated local install state. Do not claim a protocol era,
registration mode, callback, app, Project, or UI state until current redacted
observation/readback evidence exists.
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
- Things route mismatch: regenerate/check the registry and require exactly one
  `things` group with 41 core, 21 Shortcuts, and 8 native tools at exact
  `/mcp/things`; any backend, generic, historical, or alternate Things route is
  a failure.
- Remote Things unavailable: this is expected until the observed-wire,
  callback-approval, activation-receipt, and explicit remote-apply gates pass.
  Do not redirect ChatGPT to the local bearer port or another group.
- Cloudflare HTTP `530` / tunnel error `1033`: first verify whether the named
  tunnel has a connected `cloudflared` process. Before starting it, require the
  managed production listener on `127.0.0.1:46684`, regenerate the restricted
  ingress config, and verify the activation receipt. Never recover by pointing
  the tunnel at bearer-only port 46683. During shutdown or rollback, stop
  cloudflared before stopping the OAuth origin, then prove both are absent.
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

## Primary protocol and ChatGPT references

- [MCP 2026-07-28 specification](https://modelcontextprotocol.io/specification/2026-07-28)
- [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [Connect from ChatGPT](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [Plugin authentication](https://developers.openai.com/plugins/build/auth)
- [Build plugins](https://developers.openai.com/plugins/build/plugins)
