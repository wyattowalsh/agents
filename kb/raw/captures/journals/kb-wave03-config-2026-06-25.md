---
title: "Research journal — KB wave 03"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 03 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave03-config-2026-06-25
original_location: "~/.grok/research/kb-wave03-config-2026-06-25.md"
---

# Research journal — KB wave 03

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 03 | Theme: config registry fleet
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 03 — config registry fleet`

## G0 brief

Read-only ingest of five `config/*-registry.json` files into four captures; enriched MCPHub, harness sync, and MCP/plugin ownership wiki pages with 2026-06-25 registry counts.

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `config-transaction-registry-capture-w03` | `kb/raw/captures/config-transaction-registry-capture-w03.md` |
| worker | `harness-surface-registry-capture-w03` | `kb/raw/captures/harness-surface-registry-capture-w03.md` |
| worker | `hook-surface-registry-capture-w03` | `kb/raw/captures/hook-surface-registry-capture-w03.md` |
| worker | `mcp-registry-capture-w03` | `kb/raw/captures/mcp-registry-capture-w03.md` |

## Ingest queue

- `raw`: added 4 captures (`mcp-registry-capture-w03`, `harness-surface-registry-capture-w03`, `config-transaction-registry-capture-w03`, `hook-surface-registry-capture-w03`).

## Capture evidence (excerpts)

### `config-transaction-registry-capture-w03`

# Config Transaction Registry Capture W03

Read-only snapshot of `config/config-transaction-registry.json` on 2026-06-25.

## Surface modes

| Mode | Meaning |
|------|---------|
| `canonical` | Repo-owned source file; edit through normal review |
| `generated` | Derived output; regenerate from canonical sources |
| `merged` | Live/global user config; preview, backup, redaction, explicit approval, apply, rollback |
| `symlink` | Pointer to canonical repo source; verify target |
| `symlinked-entries` | Directory with repo-managed symlinks; preserve unrelated user entries |

## Global config rules (merged surfaces)

1. Never mutate live global config during planning or dry-run.
2. Before apply: preview with secrets/private tokens redacted.
3. Before apply: backup snapshot outside generated repo outputs.
4. After apply: targeted validation or smoke check for touched harness.
5. Rollback restores pre-apply snapshot without touching unrelated user-owned entries.

## Redaction rules

- Never print secret values from `.env` or global app configs.
- Credential references render as env var names or deterministic fingerprints only.
- Redact auth tokens, cookies, API keys, OAuth refresh tokens, private keys, browser profile secrets.
- Treat desktop app configs as sensitive even when JSON.

## Fixture classes (test contract vocabulary)

`preview`, `idempotent-rerun`, `global-merge`, `rollback`, `redaction`, `generated-source-trace`, `no-fabricated-skill-claim`

## Implementation gap (cross-registry)

### `harness-surface-registry-capture-w03`

# Harness Surface Registry Capture W03

Read-only snapshot of `config/harness-surface-registry.json` and `config/support-tier-registry.json` on 2026-06-25.

## Fleet summary

| Metric | Value |
|--------|-------|
| Harness records | 19 |
| `validated` | 2 (`cursor-editor`, `cursor-cli`) |
| `repo-present-validation-required` | 15 |
| `experimental` | 2 (`perplexity-desktop`, `cherry-studio`) |

## Support tier vocabulary (`support-tier-registry.json`)

| Tier | Docs label | Promotion |
|------|------------|-----------|
| `validated` | Validated | allowed |
| `repo-present-validation-required` | Repo-present, validation required | blocked |
| `planned-research-backed` | Planned, research-backed | blocked |
| `experimental` | Experimental | blocked |
| `unverified` | Unverified | blocked |
| `unsupported` | Unsupported | blocked |
| `quarantine` | Quarantine | blocked (security lane) |

Rules: cannot mark `validated` without fixture + rollback; experimental/planned must not appear as supported in install commands; quarantine needs security-lane approval.

## Projection surface counts (across 19 harnesses)

| Surface | Harnesses claiming |
|---------|-------------------|
| `mcp` | 15 |
| `instructions` | 10 |
| `skills` | 9 |

### `hook-surface-registry-capture-w03`

# Hook Surface Registry Capture W03

Read-only snapshot of `config/hook-surface-registry.json` on 2026-06-25.

## Registry role

Dedicated per-harness hook discovery surfaces (file paths, embedding, authority). Complements `config/harness-surface-registry.json` (which lists `hooks` in `projection_surfaces`). Intended for `hook_scan.py`, `GapReport.hooks`, and harness discovery parity beyond file-presence checks.

## Fleet summary

| Metric | Value |
|--------|-------|
| Harnesses with hook surfaces declared | 9 |
| Harness aliases mapped | 28 alias keys → canonical ids |
| `kind` values | `hooks` \| `config` (embedded) |
| `role` values | `authoritative` \| `secondary` \| `repo-observed` \| `blind-spot` |

## Per-harness hook surfaces

| Harness | Authoritative paths | Notes |
|---------|---------------------|-------|
| `claude-code` | `.claude/settings.json`, `~/.claude/settings.json` | Embedded under `hooks` key |
| `codex` | `.codex/hooks.json`, `~/.codex/hooks.json` | Standalone hook files |
| `cursor-editor` | `.cursor/hooks.json`, `~/.cursor/hooks.json` | Project + global |
| `cursor-cloud-agent` | `.cursor/hooks.json` (secondary) | Not every local event supported in cloud |
| `gemini-cli` | `.gemini/settings.json`, `~/.gemini/settings.json` | Embedded hooks |
| `github-copilot-web` | `.github/hooks/*` (secondary) | Cloud policy on GitHub.com |
| `github-copilot-cli` | `.github/hooks/*` (secondary) | |
| `grok-build` | `~/.grok/hooks/*.json`, `config/grok-plannotator-hooks.json` (repo-observed) | Plannotator rendered on home sync |
| `opencode` | *(none)* | Plugin-internal hooks only |

## Blind spots (selected)

| Harness | Blind spot |

### `mcp-registry-capture-w03`

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


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 4**; pages enriched: 3; lint: pass (0 issues).

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
