---
title: Harness And Platform Sync
tags:
  - kb
  - harnesses
  - sync
aliases:
  - Platform sync
  - Harness sync
kind: concept
status: partial
updated: 2026-05-01
source_count: 6
---

# Harness And Platform Sync

## Supported Targets

The repository targets Antigravity, Claude Code, Codex, Crush, Cursor, Gemini CLI, GitHub Copilot, OpenCode, and agentskills.io-compatible agents. Distribution is handled by native plugin adapters where available and the Skills CLI fallback elsewhere.

## Canonical And Generated Surfaces

`config/sync-manifest.json` records which paths are canonical, generated, symlinked, or merged. This matters because changes should happen at the canonical source instead of at generated harness projections.

| Surface | Evidence-backed role |
|---------|----------------------|
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Claude Code plugin adapter. |
| `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` | Codex plugin and marketplace adapter. |
| `opencode.json` | Repo-managed OpenCode runtime config. |
| `config/opencode-dcp.jsonc` | Canonical OpenCode DCP source. |
| `config/sync-manifest.json` | Surface ownership and sync mode ledger. |
| `agent-bundle.json` | Cross-agent component map and adapter metadata. |

## OpenCode Notes

Repo policy keeps OpenCode config model-neutral. OpenCode npm plugin specs are intentionally `@latest` in repo-managed config. Missing plugin environment variables, such as telemetry credentials, should be treated as setup warnings unless OpenCode reports actual load failures.

## Ownership And Safety Notes

Use [[canonical-generated-surfaces]] to find the source-of-truth path before editing a harness projection. Use [[plugin-and-mcp-ownership]] for one-owner-per-harness MCP/plugin rules, [[sync-transaction-safety]] for rollback limits, and [[opencode-runtime-policy]] for OpenCode-specific plugin/runtime policy.

## Related Pages

- [[agent-asset-model]]
- [[canonical-generated-surfaces]]
- [[plugin-and-mcp-ownership]]
- [[sync-transaction-safety]]
- [[opencode-runtime-policy]]
- [[openspec-workflow]]
- [[known-risks-and-open-gaps]]
- [[repo-map]]

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Supported agents include Antigravity, Claude Code, Codex, Crush, Cursor, Gemini CLI, GitHub Copilot, and OpenCode. | `kb/raw/sources/readme.md`; `kb/raw/sources/agent-bundle-and-sync.md` | raw source notes | README and bundle. |
| Sync manifest records canonical, generated, symlink, and merged surfaces. | `kb/raw/sources/agent-bundle-and-sync.md` | raw source note | Derived from `config/sync-manifest.json`. |
| OpenCode loads `AGENTS.md`, `instructions/opencode-global.md`, and skills from `skills`. | `kb/raw/sources/agent-bundle-and-sync.md` | raw source note | Derived from `opencode.json`. |
| Repo-managed OpenCode config remains model-neutral and uses `@latest` plugin specs. | `kb/raw/sources/agents-md.md`; `kb/raw/sources/agent-bundle-and-sync.md` | raw source notes | Derived from `AGENTS.md` and `opencode.json`. |
| Config registries track canonical, generated, merged, symlinked, plugin, and MCP ownership surfaces. | `kb/raw/sources/config-registries-and-sync.md` | raw source note | Registry/source-map enrichment. |
| Instruction hierarchy controls how repo policy reaches platform bridges. | `kb/raw/sources/instructions-hierarchy.md` | raw source note | Platform bridge evidence. |
| External harness docs provide upstream context only; repo-local registry and instruction files remain authoritative. | `kb/raw/sources/external-harness-docs.md` | external source note | Context-only source. |
