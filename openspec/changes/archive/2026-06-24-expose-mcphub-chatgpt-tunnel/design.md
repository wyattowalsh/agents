# Design

## Lifecycle

`scripts/mcphub/ensure-running.sh` remains the entry point for `make mcphub-up`.
It starts MCPHub when needed, waits for `/health`, then starts the tunnel sidecar
only when `MCPHUB_TUNNEL_ENABLED=true`.

The LaunchAgent runner follows the same order: start MCPHub, wait for health,
then start the tunnel sidecar. Shutdown traps stop the sidecar before removing
local PID state.

## Tunnel Configuration

The managed provider is Cloudflare Tunnel through `cloudflared`. Stable tunnels
can be started with either:

- `MCPHUB_TUNNEL_TOKEN`, matching the Cloudflare dashboard connector command.
- `MCPHUB_TUNNEL_NAME` plus local credentials/config outside the repo.

The public URL is declared with `MCPHUB_PUBLIC_URL`; the launcher accepts either
the origin hostname or the full `/mcp` URL and normalizes it for reporting.

## Zapier Handoff

If `MCPHUB_ZAPIER_WEBHOOK_URL` is set in `.env.mcphub`, tunnel startup posts a
small JSON payload:

```json
{
  "event": "mcphub_tunnel_ready",
  "service": "mcphub",
  "public_url": "https://mcp.w4w.dev/mcp",
  "local_url": "http://127.0.0.1:46683/mcp",
  "provider": "cloudflare",
  "timestamp": "2026-05-14T00:00:00Z"
}
```

Webhook delivery is best-effort and must not prevent local MCPHub startup.
