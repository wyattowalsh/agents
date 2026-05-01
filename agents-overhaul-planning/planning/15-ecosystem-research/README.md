---
status: planning
owner: ecosystem-research-leads
last_updated: 2026-05-01
principle: discovery-is-not-promotion
---

# Ecosystem Research Index

## Objective

Capture external ingredients that can improve the agents repo without turning discovery artifacts into supported dependencies prematurely.

## Research lanes

1. **Agent Skills / plugins first**: portable skills, robust CLIs, npx-managed lifecycle, and harness-native extensions.
2. **MCP second**: live external state, browser/runtime automation, current docs retrieval, authenticated SaaS, observability, and research.
3. **Harness-native surfaces**: idiosyncratic settings, hooks, rules, agents, extensions, and marketplaces.
4. **Awesome lists and indexes**: discovery and watchlist inputs only.
5. **OpenSpec**: change governance and durable capability requirements.

## Promotion gates

| Gate | Required evidence |
|---|---|
| Discovery | Found in authoritative docs, registry, MCP index, or curated list |
| Candidate | Maintained repo/docs, license, clear install path, security notes |
| Curated review | Explicit value vs existing repo capabilities, conformance plan, owner |
| Validated | Clean-room install, deterministic smoke test, docs generated from registry |
| First-class | Stable support tier, rollback path, CI gate, OpenSpec requirement |

## Non-goals

- Do not install from indexes without upstream review.
- Do not prefer MCP when a skill can provide the same reusable capability.
- Do not mark experimental harness surfaces as first-class.
- Do not hide uncertainty; unsupported contracts must stay visible.

## Required outputs

- `agent-skills-sources.md`
- `mcp-indexes.md`
- `awesome-lists.md`
- `harness-extension-surfaces.md`
- `external-tool-shortlist.md`
