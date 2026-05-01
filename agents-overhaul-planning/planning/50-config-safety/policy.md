---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Policy-as-Code

## Objective

Define controls for policy-as-code in the agents control plane.

## Required controls

- explicit support tier
- explicit trust tier
- generated docs warnings
- CI validation
- rollback plan
- no secret material in committed files

## OpenSpec requirement

All changes to this control area must update or reference an OpenSpec requirement under `openspec/specs/config-safety/`.

## Acceptance criteria

- Policy is represented in registry metadata.
- CI validates the relevant metadata.
- Docs render user-facing warnings.
- Failure behavior is documented.
