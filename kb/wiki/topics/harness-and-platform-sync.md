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
status: active
updated: 2026-06-25
source_count: 16
---

# Harness And Platform Sync

## Supported Targets

The repository targets Antigravity, Claude Code, Codex, Crush, Cursor, Gemini CLI, GitHub Copilot, OpenCode, Grok Build, and agentskills.io-compatible agents. Distribution is handled by native plugin adapters where available and the Skills CLI fallback elsewhere.

The harness surface registry (`config/harness-surface-registry.json`) records **19** distinct harness surfaces — desktop, web/cloud, CLI, and editor variants are separate records unless fixtures prove shared behavior.

## Harness surface registry (2026-06-25)

| Support tier | Count | Examples |
|--------------|-------|----------|
| `validated` | 2 | cursor-editor, cursor-cli |
| `repo-present-validation-required` | 15 | claude-code, codex, opencode, grok-build, cursor-cloud-agent |
| `experimental` | 2 | perplexity-desktop, cherry-studio |

Projection claims across the fleet: MCP on 15 harnesses; instructions on 10; skills on 9; hooks on 7 (see hook surface registry for discovery paths). Only `cursor-editor` and `cursor-cli` may be promoted to docs "Validated" without further fixture work per `config/support-tier-registry.json`.

## Canonical And Generated Surfaces

`config/sync-manifest.json` records which paths are canonical, generated, symlinked, or merged. `config/config-transaction-registry.json` defines the safety contract for each mode: preview, redaction, backup, validation, and rollback for merged/global writes.

| Surface | Evidence-backed role |
|---------|----------------------|
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Claude Code plugin adapter. |
| `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` | Codex plugin and marketplace adapter. |
| `opencode.json` | Repo-managed OpenCode runtime config. |
| `config/opencode-dcp.jsonc` | Canonical OpenCode DCP source. |
| `config/sync-manifest.json` | Surface ownership and sync mode ledger. |
| `config/harness-surface-registry.json` | Per-harness projection claims and support tiers. |
| `config/hook-surface-registry.json` | Per-harness hook discovery paths and blind spots. |
| `agent-bundle.json` | Cross-agent component map and adapter metadata. |

## Hook discovery surfaces

`config/hook-surface-registry.json` declares authoritative hook paths for 9 harnesses. Embedded hooks live in Claude and Gemini `settings.json`; Codex and Cursor use standalone `hooks.json`; Grok uses `~/.grok/hooks/*.json` plus repo-observed Plannotator policy. OpenCode has **no** native `hooks.json` — hooks are plugin-internal, creating a discovery gap vs the harness registry's `hooks` projection claim.

## OpenCode Notes

Repo policy keeps OpenCode config model-neutral. OpenCode npm plugin specs are intentionally `@latest` in repo-managed config. Missing plugin environment variables, such as telemetry credentials, should be treated as setup warnings unless OpenCode reports actual load failures. OpenCode receives the broadest MCPHub client exposure (all groups + per-server endpoints).

## Ownership And Safety Notes

Use [[canonical-generated-surfaces]] to find the source-of-truth path before editing a harness projection. Use [[plugin-and-mcp-ownership]] for one-owner-per-harness MCP/plugin rules, [[sync-transaction-safety]] for rollback limits and transaction fixture classes, and [[opencode-runtime-policy]] for OpenCode-specific plugin/runtime policy.

## Related Pages

- [[agent-asset-model]]
- [[canonical-generated-surfaces]]
- [[plugin-and-mcp-ownership]]
- [[sync-transaction-safety]]
- [[opencode-runtime-policy]]
- [[mcphub-control-plane]]
- [[hooks-evals-control-plane]]
- [[harness-fixture-gaps]]
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
| 19 harness records; 2 validated; tier vocabulary from support-tier registry. | `kb/raw/captures/harness-surface-registry-capture-w03.md` | raw capture | 2026-06-25 registry read. |
| Transaction modes and fixture-class vocabulary. | `kb/raw/captures/config-transaction-registry-capture-w03.md` | raw capture | Policy vs implementation gap. |
| 9 harnesses with hook discovery paths; OpenCode plugin-internal blind spot. | `kb/raw/captures/hook-surface-registry-capture-w03.md` | raw capture | Complements harness registry. |
| Instruction hierarchy controls how repo policy reaches platform bridges. | `kb/raw/sources/instructions-hierarchy.md` | raw source note | Platform bridge evidence. |
| External harness docs provide upstream context only; repo-local registry and instruction files remain authoritative. | `kb/raw/sources/external-harness-docs.md` | external source note | Context-only source. |
| 2026-06-25 OpenCode/Cursor/Copilot harness doc pointers. | `kb/raw/sources/opencode-docs-capture-w10.md`; `kb/raw/sources/cursor-docs-capture-w10.md`; `kb/raw/sources/copilot-harness-docs-capture-w10.md` | external pointers | Wave 10. |
| Grok/Codex repo policy templates and home sync targets. | `kb/raw/captures/harness-policy-templates-capture-w12.md` | raw capture | Wave 12 metadata-only. |
| Gemini CLI official repo + GEMINI.md bridge. | `kb/raw/sources/gemini-harness-docs-capture-w13.md` | external pointer | Wave 13. |
| Grok dedicated policy topic. | `kb/raw/captures/grok-harness-policy-capture-w15.md`; [[grok-harness-policy]] | raw capture + wiki | Wave 15 pass 2. |
| Codex dedicated policy topic. | `kb/raw/captures/codex-harness-policy-capture-w15.md`; [[codex-harness-policy]] | raw capture + wiki | Wave 15 pass 2. |
| Antigravity/Crush/Gemini shared GEMINI bridge. | `kb/raw/sources/antigravity-crush-harness-capture-w16.md` | external pointer | Wave 16 pass 2. |