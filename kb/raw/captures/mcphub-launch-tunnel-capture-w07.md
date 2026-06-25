---
title: MCPHub Launch And Tunnel Capture W07
tags:
  - kb
  - raw
  - mcp
  - mcphub
aliases:
  - MCPHub launch tunnel 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave07-mcphub-2026-06-25
---

# MCPHub Launch And Tunnel Capture W07

Read-only capture of MCPHub startup, LaunchAgent, Cloudflare tunnel, and remote exposure from `scripts/mcphub/`, `config/launchd/`, and `mcp/mcphub/README.md` on 2026-06-25.

## Startup flow

```text
make mcphub-up
  → up.sh → ensure-running.sh
      → mcphub_is_healthy? → mcphub_start_tunnel (if enabled) → exit 0
      → mcphub_start_local (npx @samanhappy/mcphub → .mcphub/mcphub.pid)
      → mcphub_wait_healthy (INIT_TIMEOUT / MCPHUB_STARTUP_WAIT_SECONDS)
      → mcphub_start_tunnel (if enabled)
```

`smoke.sh` and `remote-stdio.sh` call `ensure-running.sh` (and `smoke.sh` also `mcphub_require_token`) before MCP protocol checks.

## LaunchAgent

| Field | Value |
|-------|-------|
| Plist template | `config/launchd/com.wyattowalsh.mcphub.plist` |
| Label | `com.wyattowalsh.mcphub` |
| Program | `scripts/mcphub/launch-agent-run.sh` (paths are `/path/to/agents` placeholders in template) |
| RunAtLoad / KeepAlive | both `true` |
| Install target | `~/Library/LaunchAgents/com.wyattowalsh.mcphub.plist` via `make mcphub-install-launch-agent` |

`launch-agent-run.sh` behavior:

- Writes wrapper PID to `.mcphub/mcphub.pid`, child PID to `.mcphub/mcphub-child.pid`
- `launchctl setenv` for `MCPHUB_BASE_URL`, optional `MCPHUB_PUBLIC_URL`, `MCPHUB_BEARER_TOKEN`
- Starts `npx -y @samanhappy/mcphub` as child; on health, starts tunnel
- `trap` on EXIT/INT/TERM stops child tree, tunnel, removes PID files

## Cloudflare tunnel (opt-in)

| Env var | Role |
|---------|------|
| `MCPHUB_TUNNEL_ENABLED` | Gate (`false` default) |
| `MCPHUB_TUNNEL_PROVIDER` | `cloudflare` / `cloudflared` |
| `MCPHUB_TUNNEL_TOKEN` | Token-based `cloudflared tunnel run --token` |
| `MCPHUB_TUNNEL_NAME` / `HOSTNAME` / `CREDENTIALS_FILE` | Generated runtime config when token unset |
| `MCPHUB_PUBLIC_URL` | Required when tunnel enabled; normalized to `*/mcp` |
| `MCPHUB_TUNNEL_TARGET_URL` | Defaults to local `MCPHUB_BASE_URL` |
| `MCPHUB_ZAPIER_WEBHOOK_URL` | Optional `mcphub_tunnel_ready` JSON POST on tunnel start |

Tunnel PID/log: `.mcphub/cloudflared.pid`, `.mcphub/cloudflared.log`, runtime YAML `.mcphub/cloudflared.yml`.

## Registry remote exposure

From `config/mcp-registry.json` `mcphub` block:

| Field | Value |
|-------|-------|
| `base_url` | `http://127.0.0.1:46683` |
| `public_url` | `https://mcp.w4w.dev/mcp` |
| `bearer_token_env_var` | `MCPHUB_BEARER_TOKEN` |
| `startup_timeout_sec` | 20 |
| `tool_timeout_sec` | 90 |

ChatGPT / remote harness policy (`mcp/mcphub/README.md`): enabled projection is **`harness-safe`** at `https://mcp.w4w.dev/mcp/harness-safe`; per-server endpoints exist but stay disabled in managed configs unless explicitly enabled locally.

## Stdio bridge for stdio-only clients

`remote-stdio.sh` usage: `remote-stdio.sh <mcphub-url>` → `npx mcp-remote@latest` with `--allow-http`, bearer `Authorization` header.

Registry `stdio_bridge` client bridges: claude-desktop, cursor, gemini-cli, antigravity, github-copilot-cli, crush, chatgpt.

Codex uses `projection_adapters.codex: remote-stdio` (same bridge pattern).

## Safety notes (operational)

- `mcphub_stop_managed_pid_file` refuses to stop PIDs that do not match managed command patterns
- Stale PID while health fails: `doctor.sh` reports `stale-or-wedged`; `ensure-running.sh` stops managed processes before restart
- OpenAPI export hits `/api/openapi.json` (documented public); MCPHub should remain bound to loopback
- Tunnel credentials, tokens, and Zapier URLs must not be committed (`.env.mcphub` only)

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| LaunchAgent plist fields | `config/launchd/com.wyattowalsh.mcphub.plist` | canonical repo path |
| Tunnel env and sidecar logic | `scripts/mcphub/common.sh` | canonical repo path |
| Public harness-safe URL policy | `mcp/mcphub/README.md` | canonical repo path |
| Registry URLs and timeouts | `config/mcp-registry.json` `mcphub` | canonical repo path |