# MCPHub Control Plane

`config/mcp-registry.json` is the MCP server and group source of truth.
`mcp/mcphub/mcp_settings.json` is its tracked, secret-free generated projection.
MCPHub owns server processes, grouping, routing, authorization, logs, and
OpenAPI export; managed clients connect to MCPHub instead of launching duplicate
servers.

Production uses a repository-owned, content-addressed downstream derived from
the audited `@samanhappy/mcphub@1.0.32` distribution. The materializer verifies
the upstream tarball, exact dependency graph, owned sources, patches, anchors,
and output inventory before publishing an immutable runtime digest. Production
launch accepts only a selected verified digest and performs no package-registry
resolution, live patching, or ESM loader injection.

## Local files

- `mcp_settings.json`: generated, tracked, secret-free MCPHub settings.
- `downstream/`: exact package lock, provenance, owned edge/auth/runtime source,
  conformance fixtures, and tests.
- `.env.mcphub.example`: copy to `.env.mcphub` and fill local secrets.
- `scripts/mcphub/`: lifecycle, materialization, validation, smoke, and client
  wrappers.
- `.mcphub/`: ignored local runtime/log/config state.

Do not commit `.env.mcphub`, tunnel credentials, OAuth state, tokens, cookies,
authorization codes, callback captures, or private Things content.

## Things++ single-group topology

All Things MCP logic is reachable only through the one `things` group:

- local bearer: `http://127.0.0.1:46683/mcp/things`;
- remote OAuth loopback: `http://127.0.0.1:46684/mcp/things`;
- ChatGPT resource: `https://mcp.w4w.dev/mcp/things`.

The normalized catalog expands to exactly 70 qualified tools: 41 from
`things-core`, 21 fixed typed Shortcuts bridges, and 8 fixed native operations.
No Things server belongs to a generic group. Individual backend, generic,
Smart Routing, historical, compatibility-alias, or alternate Things routes are
prohibited.

The two loopback listeners share the same group/path but not credentials. Port
46683 accepts only the configured local bearer. Port 46684 accepts only opaque
MCPHub OAuth access tokens for the exact public resource. Accepted-socket
identity selects the credential class; caller-controlled forwarding headers
cannot substitute it.

## Things++ OAuth and ChatGPT

Remote ingress and Things tool dispatch default disabled. Cloudflare may target
only `http://127.0.0.1:46684`, never the local bearer listener. Client ID
Metadata Documents are the primary registration mode. Dynamic Client
Registration is a strict fallback only when a current redacted ChatGPT
observed-wire run selects it.

Authorization requires PKCE `S256`, exact resource/audience
`https://mcp.w4w.dev/mcp/things`, RFC 9207 issuer binding, and three independent
scopes: `things.read`, `things.write`, and `things.admin`. Those scopes imply
none of one another and do not replace per-call approval or mutation receipts.

Do not enable durable public ingress until offline protocol/OAuth/ingress
conformance, local read-only catalog closure, a current redacted wire record,
exact callback and registration-mode approval, an unexpired digest-bound final
stamp, and explicit user approval for remote apply all pass. Failure leaves
remote ingress and tool dispatch disabled; there is no alternate group or
bearer fallback.

The secret-free registration reference, Project instructions, safety contract,
and bounded test prompts live under
`platforms/chatgpt/things-plus-plus/`. That bundle does not create a ChatGPT
app, Project, connector, or UI state. Its `capabilities.md` is generated from
the canonical Things Manager ledger and must not be edited by hand.

## General endpoints

- all managed servers: `http://127.0.0.1:46683/mcp`;
- group: `http://127.0.0.1:46683/mcp/{group}`;
- individual non-Things server: `http://127.0.0.1:46683/mcp/{server}`;
- Smart Routing, opt-in for non-Things work:
  `http://127.0.0.1:46683/mcp/$smart` and
  `http://127.0.0.1:46683/mcp/$smart/{group}`;
- OpenAPI export: `http://127.0.0.1:46683/api/openapi.json`.

The `harness` group is the default bounded local surface for general agent
work. It does not contain Things servers. Things-aware projections use one
separate `mcphub_group_things` entry pointing at exact `/mcp/things`.

## First run and source validation

Create local-only secrets:

```bash
cp .env.mcphub.example .env.mcphub
python3 - <<'PY'
import secrets
print("ADMIN_PASSWORD=" + secrets.token_urlsafe(24))
print("JWT_SECRET=" + secrets.token_urlsafe(48))
print("MCPHUB_BEARER_TOKEN=" + secrets.token_urlsafe(48))
PY
```

Replace the placeholders in `.env.mcphub`. Keep
`MCPHUB_TUNNEL_ENABLED=false` until the remote activation gate.

Generate and validate tracked settings before a local apply:

```bash
just mcphub-generate
bash scripts/mcphub/validate-settings.sh
uv run python scripts/sync_agent_stack.py --targets repo --check
```

Local runtime activation is a later, reversible gate. Once authorized and the
content-addressed runtime has been sealed, use the maintained lifecycle and
assurance commands:

```bash
just mcphub-up
just mcphub-doctor
just mcphub-smoke
```

`just mcphub-doctor` must confirm selected content/config identities and exact
listener bindings. A health response alone is not installed-client, catalog,
OAuth, public-ingress, or ChatGPT UI proof.

## Runtime state and rollback

MCPHub may write connection and OAuth state beneath ignored runtime roots.
Tracked settings remain the source baseline; runtime state is not a second
source of truth. Reconcile only after generated settings pass source checks.

Rollback restores verified binary/config targets only. It excludes OAuth and
Things receipt databases, WAL files, browser sessions, authorization state,
codes, tokens, refresh families, client records, and replay state. Rolling back
configuration must never resurrect credentials or mutation receipts.

## Smart Routing

Smart Routing is disabled by default. If separately approved for non-Things
work, it requires local PostgreSQL with pgvector plus embedding configuration.
It never owns or exposes Things tools; every Things request remains on the sole
`things` group.

## Primary references

- [MCP 2026-07-28 specification](https://modelcontextprotocol.io/specification/2026-07-28)
- [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [Connect from ChatGPT](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [Plugin authentication](https://developers.openai.com/plugins/build/auth)
