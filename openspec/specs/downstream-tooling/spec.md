# Downstream Tooling Specification

## Purpose

Define how this repository exposes the same asset bundle and OpenSpec workflows to supported downstream AI tools.

## Requirements

### Requirement: Supported Agent Mapping Is Stable

The repository SHALL maintain a deterministic mapping from repo-supported agent IDs to OpenSpec tool IDs.

#### Scenario: Generating OpenSpec artifacts for repo-supported tools

- **WHEN** a user runs `uv run wagents openspec init --apply`
- **THEN** the command SHALL configure OpenSpec tools for the supported repo agents by default
- **AND** the command SHALL expose an option to pass raw OpenSpec tool IDs for tools outside the repo support matrix.

### Requirement: JSON Interfaces Are Preferred For Automation

Automation SHALL consume OpenSpec JSON commands instead of scraping markdown or terminal UI output.

#### Scenario: An AI tool needs current change status

- **WHEN** the tool needs artifact completion state for a change
- **THEN** it SHALL use `uv run wagents openspec status --change <name> --format json` or the equivalent `openspec status --json` command.

#### Scenario: An AI tool needs next-step instructions

- **WHEN** the tool needs instructions for a planning or implementation artifact
- **THEN** it SHALL use `uv run wagents openspec instructions <artifact> --change <name> --format json` or the equivalent `openspec instructions --json` command.
