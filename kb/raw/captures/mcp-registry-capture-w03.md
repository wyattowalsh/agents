---
title: MCP Registry Capture W03
tags:
  - kb
  - raw
  - mcp
  - mcphub
aliases:
  - MCP registry capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave03-config-2026-06-25
---

# MCP Registry Capture W03

Read-only snapshot of `config/mcp-registry.json` on 2026-06-25.

## Registry shape

| Metric | Value |
|--------|-------|
| Managed servers | 33 |
| MCPHub enabled | yes |
| Local base URL | `http://127.0.0.1:46683` |
| Public URL | `https://mcp.w4w.dev/mcp` |
| Bearer token env | `MCPHUB_BEARER_TOKEN` |
| Groups | 11 (`all-managed`, `code`, `harness-safe`, `research`, `reasoning`, `browser`, `data`, `media`, `personal`, `local-ai`, `experimental`) |
| Client projections | 6 (`default`, `codex`, `grok`, `opencode`, `chatgpt`, `stdio_bridge`) |

## MCPHub groups (policy highlights)

| Group | Role |
|-------|------|
| `harness-safe` | Default shared surface for search, docs, browser inspection, package metadata, repo packing, fetch, Gmail |
| `all-managed` | Every enabled registry server |
| `research` / `reasoning` | Retrieval and structured-thinking server bundles |
| `personal` | Gmail, LinkedIn — treat as sensitive |
| `experimental` | Newer or less-proven servers behind explicit targeting |

## Client projection differences

| Client | Transport / auth | Exposure |
|--------|------------------|----------|
| `default` | local group endpoints | `harness-safe` only |
| `codex` | streamable-http + bearer | `harness-safe` |
| `grok` | http + authorization-header-env-template | `harness-safe` |
| `chatgpt` | remote-http + bearer; `url_source: public` | `harness-safe` |
| `opencode` | remote-http | all 11 groups + per-server endpoints (`server_endpoint_name_style: base`) |
| `stdio_bridge` | stdio via `scripts/mcphub/remote-stdio.sh` | bridges claude-desktop, cursor, gemini-cli, antigravity, github-copilot-cli, crush, chatgpt |

## Projection adapters (per-harness MCPHub shape)

| Harness key | Adapter |
|-------------|---------|
| `codex` | `remote-stdio` |
| `grok` | `http` |
| `opencode` | `http` |

## Ownership example — `chrome-devtools`

Excluded from `claude-code`, `gemini-cli`, `github-copilot-web`, `vscode`. Ownership split:

- **plugin:** claude-code, github-copilot-web, vscode
- **extension:** gemini-cli
- **repo_mcp:** claude-desktop, chatgpt, codex, github-copilot-cli, opencode, cursor, grok, antigravity, perplexity-desktop, cherry-studio

## Contributor defaults

- `tools_policy`: deny-by-default
- `wildcard_requires_explicit_opt_in`: true
- `new_server_tools_default`: `[]`

## Smart routing (optional)

Controlled by env vars (`SMART_ROUTING_ENABLED`, `DB_URL`, embedding provider/model); default disabled; base path `/mcp/$smart`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Server inventory and groups | `config/mcp-registry.json` | canonical repo path |
| Derived settings path | `mcp/mcphub/mcp_settings.json` | canonical repo path |
| Launch/validate/bridge scripts | `scripts/mcphub/` | canonical repo path |