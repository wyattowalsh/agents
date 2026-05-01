---
title: Agent Publication Drift Coverage
tags:
  - kb
  - source
  - agents
  - drift
aliases:
  - Agent publication source
  - Agent drift source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Agent Publication Drift Coverage

## Source Record

| Field | Value |
|-------|-------|
| source_id | `agent-publication-drift-coverage` |
| original_location | `agent-bundle.json`; `agents/*.md`; `README.md`; `docs/src/content/docs/agents/`; `wagents/docs.py`; `wagents/rendering.py`; `tests/test_distribution_metadata.py`; `.claude-plugin/plugin.json`; `.codex-plugin/plugin.json`; `platforms/copilot/agents/*.agent.md`; `config/docs-artifact-registry.json` |
| raw_path | `kb/raw/sources/agent-publication-drift-coverage.md` |
| capture_method | repo-local pointer summary from read-only research |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local source, generated docs, plugin manifests, and tests |
| intended_wiki_coverage | [[agent-publication-and-drift-coverage]], [[agent-frontmatter-dialects]], [[known-risks-and-open-gaps]], [[canonical-generated-surfaces]] |

## Summary

Agent publication has a concrete drift pattern. `agent-bundle.json` still describes `agents/` as reserved, while the repository contains active agent files and README/docs surfaces publish the current agent set. Some tests protect the stale wording, so the drift is not merely a documentation typo.

Current agent files use an OpenCode-style frontmatter dialect, while scaffolding and docs rendering emphasize cross-platform fields. Claude and Codex plugin manifests also differ on whether `agents` is a packaged component, and Copilot maintains a separate platform-specific agent corpus with different names and permissions.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Bundle metadata still contains reserved-agent wording while also mapping an `agents` component. | `agent-bundle.json`; `tests/test_distribution_metadata.py` | canonical metadata and tests | Drift is test-protected. |
| README and generated docs publish active repo agent definitions. | `README.md`; `docs/src/content/docs/agents/index.mdx`; `docs/src/generated-site-data.mjs` | generated/public surfaces | Generated surfaces are evidence, not canonical policy. |
| Current repo agents use an OpenCode-style dialect distinct from scaffolded cross-platform fields. | `agents/*.md`; `wagents/cli.py`; `wagents/rendering.py` | canonical agents and implementation | Supports dialect split. |
| Docs rendering currently under-represents some repo-specific agent fields. | `wagents/docs.py`; `wagents/rendering.py`; `docs/src/content/docs/agents/index.mdx` | implementation and generated output | Needs future docs behavior decision. |
| Plugin and platform-specific agent corpora differ across Claude, Codex, and Copilot surfaces. | `.claude-plugin/plugin.json`; `.codex-plugin/plugin.json`; `platforms/copilot/agents/*.agent.md`; `config/sync-manifest.json` | manifests and platform files | Supports publication path map. |
| Generated agent docs are not fully represented in the docs artifact registry. | `config/docs-artifact-registry.json`; `wagents/docs.py` | config and implementation | Docs freshness gap. |
