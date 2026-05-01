---
status: planning
tier: primary
owner: skills-ecosystem-team
last_updated: 2026-05-01
---

# Agent Skills and CLI-First Sources

## Objective

Prioritize skills/plugins over MCP wherever the capability can be represented as reusable instructions, references, assets, and optional scripts.

## Authoritative foundations

| Source | Use in plan | Notes |
|---|---|---|
| Agent Skills specification | Canonical package model | `SKILL.md` with required `name` and `description`; optional `scripts/`, `references/`, `assets/`, compatibility metadata, and progressive disclosure constraints. |
| `skills` CLI / `npx skills` | Preferred lifecycle surface | Use for install, remove, update, validation, and multi-agent projection wherever supported. |
| `skills.sh` | Discovery, registry, trust-signal source | Discovery is not support; promotion requires upstream repo review and local conformance fixtures. |
| GitHub Copilot skill docs | Vendor-aligned skill target | Copilot CLI recognizes project/personal skill paths and slash commands for skill lifecycle. |
| Claude Code skills docs | Vendor-aligned skill target | Claude Code supports skills, plugin skills, and `allowed-tools` in skill frontmatter. |
| OpenCode skills docs | Vendor-aligned skill target | OpenCode searches `.opencode/skills`, `.claude/skills`, `.agents/skills`, and global locations. |

## Skill candidate classes

| Class | Preferred implementation | Example planning use |
|---|---|---|
| Repo audit and cartography | Internal Agent Skill | Map repository, dependency graph, generated docs, and control-plane paths. |
| Security review | External curated skill + internal policy | Integrate Trail of Bits-style secure review patterns after provenance validation. |
| OpenSpec planning | Internal Agent Skill | Create proposal/design/tasks/spec deltas from task graph nodes. |
| Documentation generation | Internal Agent Skill | README, AGENTS.md, harness setup docs, and compatibility matrices. |
| Eval authoring | Internal skill + promptfoo/deepeval adapters | Generate golden fixtures, scenario tests, replay cases. |
| Harness projection | Internal skill | Produce per-harness instructions, snippets, and config previews. |
| Dependency/API current-doc lookup | Skill wrapper over live docs MCP when needed | Skill controls workflow; MCP supplies dynamic docs. |

## CLI robustness rubric

Each candidate skill or CLI plugin must be scored on:

- deterministic output mode, preferably JSON
- stable exit codes
- idempotent commands
- dry-run support
- no secret leakage in logs
- version pinning support
- reproducible install through `npx`, `uvx`, or equivalent
- ability to run in CI without interactive prompts
- documented permissions and file writes

## Packaging requirements for internal skills

- `SKILL.md` under 500 lines where practical.
- `scripts/` only for deterministic, reviewable helper commands.
- `references/` for extended guidance, not initial activation text.
- `assets/` for templates, JSON schemas, Mermaid diagrams, and fixtures.
- `compatibility` field should declare harness targets and support tiers.
- `metadata.provenance` should identify repo, version, and source evidence.

## Promotion task hooks

- `SKILL-001` validates package structure.
- `SKILL-002` adds CLI install fixture.
- `SKILL-003` adds harness projection fixture.
- `SKILL-004` adds docs page and generated snippet.
- `SEC-004` signs/checksums promoted packages.
