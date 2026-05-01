# Spec Delta: skills-first-extension-model

## ADDED Requirements

### Requirement: Governed capability changes

Every stable capability introduced by the agents platform overhaul SHALL have a durable requirement in `openspec/specs/skills-first-extension-model/spec.md` or an active delta under `openspec/changes/agents-platform-overhaul/specs/skills-first-extension-model/spec.md`.

#### Scenario: New capability is proposed

- WHEN a P0/P1 work package introduces or changes behavior in this capability area
- THEN the implementation PR SHALL reference an OpenSpec task
- AND the relevant spec delta SHALL be reviewed before code is merged

### Requirement: Planning-to-spec traceability

Every task graph node that touches this capability area SHALL include produced artifacts, blocking dependencies, CI gates, and a merge-risk score.

#### Scenario: Task graph is regenerated

- WHEN `planning/99-task-graph/subagent-graph.json` changes
- THEN OpenSpec task coverage SHALL be validated
- AND docs SHALL show any uncovered P0/P1 tasks
