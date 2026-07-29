# Gate G1 — Discovery inventories merged

## Ownership roster

| Lane | Owner files |
| --- | --- |
| Sync-MCP | `scripts/sync_agent_stack.py` then `config/mcp-registry.json` (serial) |
| Hooks | hook-registry, hook-surface, image-input, wagents-hook, research_hook, apm-hooks |
| Platforms | site_model, platforms/{gemini,antigravity,copilot}.py delete, agent-bundle, openspec/config, justfile, smoke matrix |
| RTK | wagents/rtk.py include globs |
| Policy-docs | AGENTS.md, instructions, hand docs, docs_catalog |
| Router | skill-router skill_index.py |

## Delete highlights

Bridges: GEMINI.md, gemini/copilot globals, platforms modules, wrappers gemini/antigravity/copilot, rules, .antigravity/, Copilot .github projections, platforms/copilot/, dedicated tests, harness-master evals.

## Keep

candidate-* wrappers, SUPPORTED_TARGET_AGENTS ids, OpenCode auth plugins, gemini-api skill, CI workflows, Crush.

## MDX shards

A–F ~510, G–M ~331, N–S ~498, T–Z ~251 (1590 hits).

## Smoke

Drop github-copilot + gemini-cli from install-smoke-phase3.yml only.
