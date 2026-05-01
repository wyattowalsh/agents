# Quality Gates

## Objective

Define CI gates that make the planning and generated artifacts trustworthy.

## Required gates

| Gate | Scope | Blocking? |
|---|---|---|
| Repo inventory validation | manifests and paths | yes |
| Registry schema validation | harness/skill/MCP/plugin registries | yes |
| Skill package validation | SKILL.md + scripts/references/assets | yes |
| Skill CLI conformance | script-backed skills | yes for adopted skills |
| MCP schema validation | curated MCP records | yes |
| MCP smoke tests | promoted MCPs | yes where feasible |
| MCP security scan | promoted MCPs | yes / exception required |
| Adapter golden fixtures | generated harness configs | yes |
| Transaction rollback tests | config writes | yes |
| Docs truth test | README/docs/matrices/AI instructions | yes |
| OpenSpec validation | active changes/specs/tasks | yes |
| Evals | key skill workflows | initially advisory, later blocking |

## Acceptance criteria

- CI emits machine-readable reports.
- Docs drift fails CI.
- Preview/apply/rollback command paths are tested.
