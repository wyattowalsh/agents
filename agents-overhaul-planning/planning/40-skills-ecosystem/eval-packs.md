---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Skill Eval Packs

## Objective

Turn important skills into testable behaviors.

## Eval pack structure

```text
skills/<skill>/evals/
  cases.yaml
  fixtures/
  expected/
```

## Case schema

```yaml
id: string
prompt: string
required_skill: string
fixtures: []
expected_artifacts: []
scoring:
  type: rubric|exact|schema|command
  pass_threshold: number
```

## OpenSpec integration

Every new first-class skill should include OpenSpec requirements for when it should activate and what it must produce.
