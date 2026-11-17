# Agent Assets Delta

## MODIFIED Requirements

### Requirement: Asset Formats Stay Canonical

The repository SHALL keep skill, agent, MCP, instruction, hook, and bundle metadata formats documented in `AGENTS.md` and validated by `wagents` commands.

#### Scenario: Consolidating first-party review skills

- **WHEN** the repository adds `skills/review/SKILL.md`
- **THEN** `review` SHALL be the canonical first-party review skill for session, scoped, PR, range, full audit, simplification, source/provenance, specialist-lens, history, delta, learnings, SARIF, Conventional Comments, and approved fix-pass review workflows
- **AND** legacy public skill names for `honest-review`, `simplify`, and `external-skill-auditor` SHALL be absent from first-party skill directories, installable catalog rows, generated install scripts, and `/`-invocable surfaces.

#### Scenario: Preserving multi-harness portability

- **WHEN** review skill metadata is projected to Claude Code, Codex, OpenCode, Grok Build CLI, or Skills CLI-compatible targets
- **THEN** the portable `SKILL.md` SHALL avoid root model overrides and blanket skill-scoped hooks
- **AND** harness-specific model, hook, plugin, mirror, or sync behavior SHALL be validated through repo-managed config and sync dry-runs rather than assumed from one harness's frontmatter semantics.
