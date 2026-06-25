---
title: MCPHub Control Plane
tags:
  - kb
  - mcp
  - mcphub
aliases:
  - MCPHub local control plane
kind: concept
status: active
updated: 2026-06-25
source_count: 6
---

# MCPHub Control Plane

## Summary

MCPHub is the preferred local MCP control plane when enabled in `config/mcp-registry.json`. Edit servers once in the registry, keep `mcp/mcphub/mcp_settings.json` secret-free and validated, and let clients connect to MCPHub on `http://127.0.0.1:46683` via group or server endpoints instead of launching duplicate standalone processes.

## Why it matters

- Reduces per-harness MCP process sprawl and centralizes auth, routing, and groups.
- `harness-safe` is the primary shared group for managed harness surfaces (14 servers in that group).
- One-owner-per-harness rules still apply (especially Chrome DevTools).
- Contributor defaults enforce deny-by-default tool policy with no wildcard opt-in unless explicit.

## Current shape (2026-06-25)

| Component | Role |
|-----------|------|
| `config/mcp-registry.json` | Canonical SSOT: 33 servers, 11 groups, 6 client projections |
| `mcp/mcphub/mcp_settings.json` | Tracked derived settings (placeholders only) |
| `scripts/mcphub/` | Launch, doctor, validate, remote-stdio bridge, tunnel helpers |
| `scripts/sync_agent_stack.py` | Renders per-harness MCP projections |
| `mcp/mcphub/server.py` | First-party FastMCP metadata tool (`mcphub_status`); not the running `@samanhappy/mcphub` process |
| `Makefile` `mcphub-*` | Nine developer targets wrapping `scripts/mcphub/` lifecycle |

## Lifecycle and launch (Wave 07)

| Stage | Entry | Behavior |
|-------|-------|----------|
| Start | `make mcphub-up` → `up.sh` | `ensure-running.sh`: health check, else `npx -y @samanhappy/mcphub` with logs in `.mcphub/mcphub.log` |
| Ensure | `ensure-running.sh` | Shared by smoke, OpenAPI export, `remote-stdio.sh`, and harness wrappers |
| Stop | `make mcphub-down` | Stops managed wrapper/child PIDs and tunnel; refuses unmanaged PIDs |
| Diagnose | `make mcphub-doctor` | Settings, node/npx, health, listener, PID state, bearer, tunnel, smart routing |
| Smoke | `make mcphub-smoke` | Bearer `initialize` + `tools/list` over HTTP MCP session |
| LaunchAgent | `make mcphub-install-launch-agent` | `config/launchd/com.wyattowalsh.mcphub.plist` → `launch-agent-run.sh` with KeepAlive |

Runtime state lives in gitignored `.mcphub/` (PID files, logs, optional `cloudflared` sidecar). Secrets load from `.env.mcphub` only.

### Script fleet highlights

- **13** top-level shell scripts + **11** harness wrappers under `scripts/mcphub/wrappers/` (each wrapper calls `ensure-running.sh` then execs the harness CLI).
- `remote-stdio.sh` bridges stdio clients via `mcp-remote` + bearer header (registry `stdio_bridge` client; Codex `remote-stdio` adapter).
- `chrome-devtools-browser-url.sh` and `docling-stdio.sh` are repo-local server launchers referenced from tracked settings.

### Tunnel and public surface

Opt-in Cloudflare tunnel (`MCPHUB_TUNNEL_ENABLED` in `.env.mcphub`) exposes `MCPHUB_PUBLIC_URL` (registry: `https://mcp.w4w.dev/mcp`). Managed remote harness configs enable only the **`harness-safe`** group endpoint; per-server endpoints stay disabled unless explicitly opted in locally. Optional `MCPHUB_ZAPIER_WEBHOOK_URL` posts `mcphub_tunnel_ready` on tunnel start.

## Groups and client exposure

| Group | Purpose |
|-------|---------|
| `harness-safe` | Default shared bundle for search, docs, browser, package metadata, fetch, Gmail |
| `all-managed` | Full enabled server set |
| `research` / `reasoning` | Retrieval and structured-thinking bundles |
| `personal` | Gmail, LinkedIn — sensitive |
| `experimental` | Less-proven servers behind explicit targeting |

| Client | Exposure pattern |
|--------|------------------|
| `default`, `codex`, `grok`, `chatgpt` | `harness-safe` group only |
| `opencode` | All 11 groups plus per-server endpoints |
| `stdio_bridge` | stdio bridge for claude-desktop, cursor, gemini-cli, antigravity, github-copilot-cli, crush, chatgpt |

Projection adapters: `codex` → `remote-stdio`; `grok` and `opencode` → `http`. Public tunnel URL `https://mcp.w4w.dev/mcp` when exposed; bearer via `MCPHUB_BEARER_TOKEN`.

## Constraints and edge cases

- Secrets belong only in `.env.mcphub` (gitignored); bearer token required for `/mcp`.
- `personal` and `experimental` groups are sensitive; tunnel exposure is opt-in.
- Smart routing (`/mcp/$smart`) is env-gated and off by default.
- `mcp/servers/` and `mcp/secrets/` are local-only; never ingest into KB.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| 33 servers, 11 groups, MCPHub enabled | `kb/raw/captures/mcp-registry-capture-w03.md` | raw capture | 2026-06-25 registry read |
| `harness-safe` default client group (14 servers) | `kb/raw/captures/mcp-registry-capture-w03.md`; `kb/raw/captures/mcphub-settings-validation-capture-w07.md` | raw capture | 6 client projections |
| Chrome DevTools ownership split | `kb/raw/captures/mcp-registry-capture-w03.md` | raw capture | plugin/extension/repo_mcp lanes |
| Script fleet, Makefile targets, `.mcphub` runtime | `kb/raw/captures/mcphub-scripts-lifecycle-capture-w07.md` | raw capture | Wave 07 lifecycle inventory |
| LaunchAgent, tunnel, stdio bridge | `kb/raw/captures/mcphub-launch-tunnel-capture-w07.md` | raw capture | Wave 07 launch/tunnel |
| Settings validation `ok`; routing invariants | `kb/raw/captures/mcphub-settings-validation-capture-w07.md` | raw capture | `validate_settings.py` |
| Control plane model and settings parity | `kb/raw/sources/mcphub-control-plane-source.md` | raw source note | Primary pointer summary |
| Registry split and safety | `kb/raw/sources/mcp-surfaces.md` | raw source note | Complementary |

## Related wiki pages

- [[mcp-configuration-and-safety]]
- [[plugin-and-mcp-ownership]]
- [[harness-and-platform-sync]]
- [[sync-transaction-safety]]

## Open questions

- In-tree automated registry-to-mcp_settings generator vs manual regenerate workflow.
- LaunchAgent plist still ships `/path/to/agents` placeholders — install path must be edited or templated before bootstrap.