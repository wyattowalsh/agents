---
title: MCPHub Settings Validation Capture W07
tags:
  - kb
  - raw
  - mcp
  - mcphub
aliases:
  - MCPHub settings validation 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave07-mcphub-2026-06-25
---

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

## `harness-safe` group servers (14)

`brave-search`, `chrome-devtools`, `context7`, `deepwiki`, `fetch`, `fetcher`, `package-version`, `penpot`, `repomix`, `supathings`, `tavily`, `trafilatura`, `duckduckgo-search`, `gmail`

## Special server launch patterns in settings

| Server | Launch pattern |
|--------|----------------|
| `chrome-devtools` | `bash` → `scripts/mcphub/chrome-devtools-browser-url.sh` |
| `docling` | `${REPO_ROOT}/scripts/mcphub/docling-stdio.sh` |
| Most others | `npx -y <package>` with env placeholders |

## Registry `mcphub` metadata (cross-check)

| Field | Value |
|-------|-------|
| `settings_path` | `mcp/mcphub/mcp_settings.json` |
| `openapi_export_path` | `mcp/mcphub/openapi.json` |
| `smart_routing.default_enabled` | false |
| `smart_routing.base_path` | `/mcp/$smart` |

Smart routing opt-in requires local PostgreSQL/pgvector, `SMART_ROUTING_ENABLED=true`, embedding env vars, and `DB_URL` in `.env.mcphub` per `mcp/mcphub/README.md`.

## Secrets boundary

| Location | Allowed content |
|----------|-----------------|
| `mcp/mcphub/mcp_settings.json` | `${ENV_VAR}` placeholders only |
| `.env.mcphub` | `MCPHUB_BEARER_TOKEN`, admin/JWT secrets, API keys, tunnel token, `DB_URL` |
| `.env.mcphub.example` | Documented placeholders (copy template) |

`smoke.sh` requires a non-placeholder `MCPHUB_BEARER_TOKEN` before exercising `/mcp`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Validation rules | `scripts/mcphub/validate_settings.py` | canonical repo path |
| Settings/group inventory | `mcp/mcphub/mcp_settings.json` | canonical repo path |
| Registry mcphub block | `config/mcp-registry.json` | canonical repo path |
| Validation exit status | `uv run python scripts/mcphub/validate_settings.py` | tool capture |