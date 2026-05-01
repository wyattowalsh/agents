---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# OpenSpec Adapter

## Goal

Bridge planning/task manifests with OpenSpec changes and durable specs.

## Outputs

- generated OpenSpec proposal skeletons
- task graph to `tasks.md` mapping
- capability requirements into `openspec/specs/*/spec.md`
- validation reports for incomplete tasks

## Commands

- `wagents openspec status`
- `wagents openspec new <change-id>`
- `wagents openspec validate`
- `wagents openspec graph`
- `wagents openspec sync-planning`
- `wagents openspec archive <change-id>`
