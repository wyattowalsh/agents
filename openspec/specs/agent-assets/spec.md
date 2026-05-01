# Agent Assets Specification

## Purpose

Define repository-owned assets that can be consumed by multiple AI coding tools without duplicating source-of-truth instructions.

## Requirements

### Requirement: Asset Formats Stay Canonical

The repository SHALL keep skill, agent, MCP, instruction, hook, and bundle metadata formats documented in `AGENTS.md` and validated by `wagents` commands.

#### Scenario: Creating a skill

- **WHEN** a repository skill is added under `skills/<name>/SKILL.md`
- **THEN** its frontmatter `name` SHALL match the directory name
- **AND** `uv run wagents validate` SHALL validate the new skill before completion.

#### Scenario: Updating generated docs

- **WHEN** skill, agent, MCP, or docs-generation behavior changes
- **THEN** generated README and docs outputs SHALL be refreshed or checked with the documented `wagents` commands.

### Requirement: Generated Surfaces Are Explicit

The repository SHALL distinguish tracked source-of-truth assets from generated or local-only downstream tool artifacts.

#### Scenario: Tool-specific OpenSpec artifacts are generated

- **WHEN** `openspec init` or `openspec update` creates `.claude`, `.cursor`, `.opencode`, `.github`, `.agent`, `.crush`, `.codex`, or `.gemini` OpenSpec artifacts
- **THEN** those artifacts SHALL be treated as generated unless explicitly promoted to repo-owned source.
