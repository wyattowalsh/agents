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
updated: 2026-05-01
source_count: 8
---

# External Primary Source Map

## Scope

This page lists evergreen external primary sources used to contextualize repo-local behavior. It does not make external docs authoritative over this repository's own contracts.

## Source Groups

| Group | Raw source note | Primary URLs | Use |
|-------|-----------------|--------------|-----|
| Agent Skills | `kb/raw/sources/external-agent-skill-docs.md` | `https://docs.anthropic.com/llms.txt`; linked Anthropic Agent Skills pages | Broader skills ecosystem context. |
| MCP | `kb/raw/sources/mcp-surfaces.md` | `https://modelcontextprotocol.io/specification/latest`; Anthropic MCP docs; OpenCode MCP docs | Protocol and trust/safety context. |
| Harnesses | `kb/raw/sources/external-harness-docs.md` | OpenCode docs; Cursor docs index; GitHub Copilot docs; Gemini CLI repo | Platform behavior context. |
| Tooling | `kb/raw/sources/external-tooling-docs.md` | Typer, PyPA, uv, Ruff, ty, pytest, Starlight, JSON Schema, python-jsonschema | Upstream tooling semantics. |
| Obsidian/Markdown | `kb/raw/sources/external-obsidian-markdown-docs.md` | Obsidian Help, CommonMark, YAML, Git docs, Dataview docs | Vault and Markdown portability conventions. |

## Operating Rule

Use external sources to understand upstream defaults and terminology. Use repo-local sources to decide what this repo actually validates, generates, syncs, and expects.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| External sources were selected for official or primary-source status. | `kb/raw/sources/external-agent-skill-docs.md`; `kb/raw/sources/external-harness-docs.md`; `kb/raw/sources/external-tooling-docs.md`; `kb/raw/sources/external-obsidian-markdown-docs.md`; `kb/raw/sources/mcp-surfaces.md` | external source notes | Summaries are pointer notes, not vendored docs. |
| Repo-local files remain authoritative for repo-specific behavior. | `kb/raw/sources/wagents-internals.md`; `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/asset-validation-coverage.md` | raw source notes | Prevents external-doc drift from overriding repo contracts. |

## Related

- [[repository-overview]]
- [[harness-and-platform-sync]]
- [[docs-generation-and-site]]
- [[nerdbot]]
