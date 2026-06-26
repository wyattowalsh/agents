---
title: "Research journal — KB wave 07"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 07 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave07-mcphub-2026-06-25
original_location: "~/.grok/research/kb-wave07-mcphub-2026-06-25.md"
---

# Research journal — KB wave 07

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 07 | Theme: MCPHub scripts and launch fleet
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 07 — MCPHub scripts and launch fleet`

## G0 brief

Read-only ingest of `mcp/mcphub/`, `scripts/mcphub/` (13 scripts + 11 wrappers), LaunchAgent template, and registry `mcphub` block into lifecycle, tunnel, and validation captures.

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `mcphub-launch-tunnel-capture-w07` | `kb/raw/captures/mcphub-launch-tunnel-capture-w07.md` |
| worker | `mcphub-scripts-lifecycle-capture-w07` | `kb/raw/captures/mcphub-scripts-lifecycle-capture-w07.md` |
| worker | `mcphub-settings-validation-capture-w07` | `kb/raw/captures/mcphub-settings-validation-capture-w07.md` |

## Ingest queue

- `raw`: added 3 captures (`mcphub-scripts-lifecycle-capture-w07`, `mcphub-launch-tunnel-capture-w07`, `mcphub-settings-validation-capture-w07`).

## Capture evidence (excerpts)

### `mcphub-launch-tunnel-capture-w07`

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

### `mcphub-scripts-lifecycle-capture-w07`

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

### `mcphub-settings-validation-capture-w07`

# MCPHub Settings Validation Capture W07

Read-only capture of `mcp/mcphub/mcp_settings.json` parity rules and `scripts/mcphub/validate_settings.py` on 2026-06-25.

## Validation command

```bash
make mcphub-validate
# → uv run python scripts/mcphub/validate_settings.py \
#     --settings mcp/mcphub/mcp_settings.json \
#     --registry config/mcp-registry.json
```

**Captured result (2026-06-25):** `ok`

## Enforced invariants (`validate_settings.py`)

| Check | Rule |
|-------|------|
| `mcpServers` | Non-empty object; keys must match `registry.servers` exactly (no missing/extra) |
| `groups[].servers` | Every referenced server must exist in `mcpServers` |
| `systemConfig.routing` | `enableGlobalRoute`, `enableGroupNameRoute`, `enableBearerAuth` = true; `bearerAuthHeaderName` = `Authorization`; `jsonBodyLimit` = `5mb`; `skipAuth` = false |
| Secret literals | Keys matching `(TOKEN|SECRET|PASSWORD|API_KEY|AUTH_KEY|JWT)` must use `${ENV_VAR}` placeholders only |
| `bearerAuthKey` | Must not be a tracked literal |
| Bad patterns | Rejects `changeme`, `sk-*`, `ghp_*`, and similar placeholder secrets in tracked JSON |

## Settings shape (tracked file)

| Section | Content |
|---------|---------|
| `mcpServers` | 33 server entries: `command`/`args`/`env` with `${PLACEHOLDER}` secrets and `${REPO_ROOT}` paths |
| `groups` | 11 groups mirroring registry: `all-managed`, `code`, `harness-safe`, `research`, `reasoning`, `browser`, `data`, `media`, `personal`, `local-ai`, `experimental` |
| `systemConfig.routing` | Bearer auth enabled; global and group routes enabled |
| `systemConfig.smartRouting` | `enabled: false`; embedding vars as placeholders |


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 3**; wiki pages enriched: 2; lint: pass (exit 0, 0 issues).

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
