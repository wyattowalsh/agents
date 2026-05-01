# OpenSpec Adapter

## Objective

Keep planning docs, task graph, and OpenSpec change files aligned.

## Responsibilities

- Map task graph P0/P1 nodes into OpenSpec task checklist items.
- Generate spec-delta skeletons for new capabilities.
- Validate no contradiction between OpenSpec requirements and planning docs.
- Emit archive readiness report when tasks complete.

## Inputs

- active OpenSpec changes.
- task graph JSON.
- registry manifests.
- planning docs inventory.

## Outputs

- updated `openspec/changes/<id>/tasks.md`.
- spec coverage report.
- stale OpenSpec detection report.
