---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Migration Plan

## Wave 0: Inspect and preserve

- Inspect existing OpenSpec assets.
- Snapshot current config registries.
- Generate current repo map.
- Establish file ownership.

## Wave 1: Registry foundations

- Add canonical schemas.
- Add support/trust tier definitions.
- Split skills/plugins/MCP catalogs.
- Add OpenSpec change for this overhaul.

## Wave 2: Skills-first refactor

- Normalize skills metadata.
- Add external skill evaluation matrix.
- Add skills CLI lifecycle docs.
- Add skill conformance tests.

## Wave 3: Harness parity

- One adapter lane per harness.
- Golden fixtures for each first-class harness.
- Docs pages generated from registry.

## Wave 4: Safety and UX

- Add `doctor`, `sync --preview`, rollback.
- Add transaction snapshots.
- Add drift detection.

## Wave 5: Expansion

- Curate external skills and MCPs.
- Add plugin catalogs.
- Add eval packs.
- Archive OpenSpec change when stable.
