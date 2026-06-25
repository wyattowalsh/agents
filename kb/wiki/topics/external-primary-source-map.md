---
title: External Primary Source Map
tags:
  - kb
  - external-sources
  - provenance
aliases:
  - External sources
kind: index
status: active
updated: 2026-06-25
source_count: 16
---

# External Primary Source Map

## Scope

This page lists evergreen external primary sources used to contextualize repo-local behavior. It does not make external docs authoritative over this repository's own contracts.

## Source Groups

| Group | Raw source note | Primary URLs | Use |
|-------|-----------------|--------------|-----|
| Agent Skills | `kb/raw/sources/external-agent-skill-docs.md`; `kb/raw/sources/agentskills-spec-capture-w09.md`; `kb/raw/extracts/agentskills-llms-index-extract-w09.md` | `https://agentskills.io/llms.txt`; Anthropic llms.txt | Portable spec + ecosystem context. |
| MCP | `kb/raw/sources/mcp-surfaces.md`; `kb/raw/sources/mcp-spec-index-capture-w09.md` | `https://modelcontextprotocol.io/llms.txt`; spec 2025-11-25 | Protocol index + security tutorials. |
| Harnesses | `kb/raw/sources/external-harness-docs.md`; `kb/raw/sources/opencode-docs-capture-w10.md`; `kb/raw/sources/cursor-docs-capture-w10.md`; `kb/raw/sources/copilot-harness-docs-capture-w10.md` | OpenCode/Cursor/Copilot official docs | Platform behavior context. |
| Tooling | `kb/raw/sources/external-tooling-docs.md`; `kb/raw/extracts/uv-llms-index-extract-w11.md`; `kb/raw/captures/pyproject-tooling-capture-w11.md` | Typer, PyPA, uv llms.txt, Ruff, ty, pytest, Starlight | Upstream semantics + repo pyproject alignment. |
| Obsidian/Markdown | `kb/raw/sources/external-obsidian-markdown-docs.md`; `kb/raw/sources/obsidian-properties-capture-w11.md` | Obsidian Help properties/aliases/links, CommonMark, YAML | Vault conventions and portability floor. |

## Operating Rule

Use external sources to understand upstream defaults and terminology. Use repo-local sources to decide what this repo actually validates, generates, syncs, and expects.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| External sources were selected for official or primary-source status. | `kb/raw/sources/external-agent-skill-docs.md`; `kb/raw/sources/external-harness-docs.md`; `kb/raw/sources/external-tooling-docs.md`; `kb/raw/sources/external-obsidian-markdown-docs.md`; `kb/raw/sources/mcp-surfaces.md` | external source notes | Summaries are pointer notes, not vendored docs. |
| 2026-06-25 agentskills.io + MCP llms.txt full-capture lane. | `kb/raw/sources/agentskills-spec-capture-w09.md`; `kb/raw/sources/mcp-spec-index-capture-w09.md`; `kb/raw/extracts/agentskills-llms-index-extract-w09.md` | external fetch + extract | Wave 09. |
| 2026-06-25 harness doc pointer lane (OpenCode, Cursor, Copilot). | `kb/raw/sources/opencode-docs-capture-w10.md`; `kb/raw/sources/cursor-docs-capture-w10.md`; `kb/raw/sources/copilot-harness-docs-capture-w10.md` | external pointers | Wave 10. |
| 2026-06-25 tooling + Obsidian gap sweep. | `kb/raw/extracts/uv-llms-index-extract-w11.md`; `kb/raw/captures/pyproject-tooling-capture-w11.md`; `kb/raw/sources/obsidian-properties-capture-w11.md` | extract + capture + pointer | Wave 11. |
| Repo-local files remain authoritative for repo-specific behavior. | `kb/raw/sources/wagents-internals.md`; `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/asset-validation-coverage.md` | raw source notes | Prevents external-doc drift from overriding repo contracts. |

## Related

- [[repository-overview]]
- [[harness-and-platform-sync]]
- [[docs-generation-and-site]]
- [[nerdbot]]
