---
title: Agent Asset Model
tags:
  - kb
  - agents-repo
  - assets
aliases:
  - Asset model
  - Skills agents MCP instructions model
kind: concept
status: active
updated: 2026-05-01
source_count: 5
---

# Agent Asset Model

## Core Model

The repo packages several asset classes as one portable bundle:

| Asset class | Canonical location | Key contract |
|-------------|--------------------|--------------|
| Skills | `skills/<name>/SKILL.md` | YAML frontmatter plus Markdown body; required `name` and `description`; directory name matches `name`. |
| Agents | `agents/<name>.md` | YAML frontmatter plus system prompt; required `name` and `description`; filename matches `name`. |
| MCP config | `mcp.json`, `config/mcp-registry.json`, first-party `mcp/<name>/` conventions | First-party MCP servers follow FastMCP-style entrypoint/package/config conventions when authored in repo. |
| Instructions | `AGENTS.md`, `instructions/` | Shared and platform-specific behavior rules. |
| Bundle metadata | `agent-bundle.json`, plugin manifests | Cross-agent component map and native plugin adapter metadata. |
| OpenSpec | `openspec/` | Change workflow for non-trivial asset and tooling changes. |

## Important Distinctions

`AGENTS.md` says plugin manifests intentionally omit fixed versions while the repo is distributed from Git, allowing update checks to follow commits rather than manifest version bumps. The same file treats OpenCode plugin specs in repo-managed `opencode.json` as `@latest` by policy.

`agent-bundle.json` currently describes `agents/` as reserved for future bundled agent definitions, while local inventory found eight agent files in `agents/`. Treat that as a documented drift/gap until reconciled.

Agent prompt frontmatter has repo-specific fields that are not identical to skill frontmatter or upstream harness docs. Use [[agent-frontmatter-dialects]] before adding or changing agent files, and use [[plugin-and-mcp-ownership]] before changing bundle/plugin ownership relationships.

## Related Pages

- [[skill-authoring-and-validation]]
- [[agent-frontmatter-dialects]]
- [[harness-and-platform-sync]]
- [[plugin-and-mcp-ownership]]
- [[openspec-workflow]]
- [[known-risks-and-open-gaps]]

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Skills require `name` and `description` frontmatter and live at `skills/<name>/SKILL.md`. | `kb/raw/sources/agents-md.md` | raw source note | Derived from `AGENTS.md`. |
| Agents require `name` and `description` frontmatter and live at `agents/<name>.md`. | `kb/raw/sources/agents-md.md` | raw source note | Derived from `AGENTS.md`. |
| Bundle components include skills, agents, MCP servers, instructions, and OpenSpec. | `kb/raw/sources/agent-bundle-and-sync.md` | raw source note | Derived from `agent-bundle.json`. |
| Current local inventory found eight files under `agents/*.md`. | `kb/raw/sources/code-surface-inventory.md` | raw source note | Captured from local glob output. |
| The enriched agent inventory maps actual local agent frontmatter fields. | `kb/raw/sources/agent-definitions-inventory.md` | raw source note | Distinguishes repo agent dialects from skill and harness formats. |
| External agent-skill docs are contextual and do not override repo-local asset contracts. | `kb/raw/sources/external-agent-skill-docs.md` | external source note | Upstream format context only. |
