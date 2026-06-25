---
title: MCPHub Scripts Lifecycle Capture W07
tags:
  - kb
  - raw
  - mcp
  - mcphub
aliases:
  - MCPHub scripts lifecycle 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave07-mcphub-2026-06-25
---

# MCPHub Scripts Lifecycle Capture W07

Read-only inventory of `scripts/mcphub/`, `Makefile` targets, and `mcp/mcphub/` scaffold on 2026-06-25. Not an instruction source.

## Script inventory

| Script | Role |
|--------|------|
| `common.sh` | Shared runtime: `.env.mcphub` load, PATH/mise setup, health URL, PID/tunnel helpers, managed-process guards |
| `up.sh` | Load env → `ensure-running.sh` |
| `down.sh` | Stop managed wrapper/child PIDs and tunnel |
| `ensure-running.sh` | Health check; start `npx @samanhappy/mcphub` if needed; start tunnel when enabled |
| `launch-agent-run.sh` | LaunchAgent entry: wrapper PID, child `npx`, wait for health, tunnel, trap cleanup |
| `doctor.sh` | Settings validate, node/npx, health, listener, PID state, bearer token, tunnel, smart routing |
| `validate-settings.sh` | `uv run python validate_settings.py` against registry + settings |
| `smoke.sh` | Bearer `initialize` + `tools/list` over HTTP MCP session |
| `export-openapi.sh` | Ensure running; curl `/api/openapi.json` → `mcp/mcphub/openapi.json` |
| `logs.sh` | Tail `.mcphub/mcphub.log` (default 200 lines) |
| `remote-stdio.sh` | Ensure running; `mcp-remote` stdio bridge with bearer header |
| `chrome-devtools-browser-url.sh` | Launch Chrome debug port 9333; exec `chrome-devtools-mcp` |
| `docling-stdio.sh` | Isolated workdir; `uvx docling-mcp-server --transport stdio` |

## Harness wrappers (`scripts/mcphub/wrappers/`)

11 wrappers: `antigravity`, `cherry-studio`, `claude`, `codex`, `copilot`, `crush`, `cursor`, `cursor-agent`, `gemini`, `opencode`, `perplexity`. Each calls `ensure-running.sh` then `exec` the harness CLI (`MCPHUB_WRAPPED_*` env override supported).

## Makefile targets

| Target | Script |
|--------|--------|
| `mcphub-up` | `scripts/mcphub/up.sh` |
| `mcphub-down` | `scripts/mcphub/down.sh` |
| `mcphub-logs` | `scripts/mcphub/logs.sh` |
| `mcphub-doctor` | `scripts/mcphub/doctor.sh` |
| `mcphub-validate` | `scripts/mcphub/validate-settings.sh` |
| `mcphub-openapi` | `scripts/mcphub/export-openapi.sh` |
| `mcphub-smoke` | `scripts/mcphub/smoke.sh` |
| `mcphub-install-launch-agent` | Copy `config/launchd/com.wyattowalsh.mcphub.plist` → `~/Library/LaunchAgents/` |
| `mcphub-uninstall-launch-agent` | `launchctl bootout` + remove plist |

## First-party scaffold (`mcp/mcphub/`)

| File | Role |
|------|------|
| `mcp_settings.json` | Tracked derived settings (33 servers, 11 groups) |
| `server.py` | FastMCP metadata tool `mcphub_status` (read-only paths/endpoints) |
| `pyproject.toml` | `mcp-mcphub` package; `fastmcp>=2` |
| `fastmcp.json` | uv-backed FastMCP entry for `server.py` |
| `README.md` | Endpoints, first-run, tunnel, smart routing opt-in |

## Runtime paths (gitignored unless noted)

| Path | Purpose |
|------|---------|
| `.env.mcphub` | Secrets: bearer token, tunnel token, Zapier webhook, smart-routing DB |
| `.mcphub/mcphub.pid` | Wrapper `npx` PID |
| `.mcphub/mcphub-child.pid` | LaunchAgent child PID |
| `.mcphub/mcphub.log` | Local MCPHub stdout/stderr |
| `.mcphub/cloudflared.*` | Tunnel sidecar when enabled |

Default listen: `http://127.0.0.1:46683` (`PORT` / `MCPHUB_BASE_URL` overridable).

## Captured facts

| Fact | Value | Source |
|------|-------|--------|
| Shell script count | 13 top-level `.sh` + 11 wrappers | repo tree listing |
| Upstream control plane | `npx -y @samanhappy/mcphub` | `common.sh`, `launch-agent-run.sh` |
| Health endpoint | `{MCPHUB_BASE_URL}/health` | `common.sh` |
| Managed PID patterns | `launch-agent-run.sh`, `@samanhappy/mcphub`, `node_modules/.bin/mcphub` | `common.sh` `mcphub_is_managed_local_pid` |
| Settings validation | `ok` (2026-06-25) | `validate_settings.py` run |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Script roles and Makefile wiring | `scripts/mcphub/*`, `Makefile` | canonical repo paths |
| First-party FastMCP scaffold | `mcp/mcphub/server.py`, `README.md` | canonical repo paths |
| Runtime directory layout | `mcp/mcphub/README.md`, `common.sh` | canonical repo paths |