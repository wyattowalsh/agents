# Spec Workflows Specification

## Purpose

Define when OpenSpec should govern repository changes and how OpenSpec artifacts interact with this repo's existing planning, docs, and validation practices.

## Requirements

### Requirement: Non-Trivial Changes Use OpenSpec

The repository SHALL use OpenSpec for non-trivial changes that affect public workflow, asset formats, downstream tooling, docs generation, validation behavior, or multiple files.

#### Scenario: A change affects downstream AI tools

- **WHEN** a change modifies supported agent behavior, plugin manifests, sync commands, or tool-specific setup guidance
- **THEN** the change SHOULD have an OpenSpec proposal or change artifact before implementation.

#### Scenario: A change is direct and local

- **WHEN** a change is a small typo, isolated wording edit, or single local implementation fix
- **THEN** OpenSpec MAY be skipped if the user's request and repo conventions make the scope fully clear.

### Requirement: Archive Completed Changes

Completed OpenSpec changes SHALL be archived only after implementation and validation are complete.

#### Scenario: A change is ready to close

- **WHEN** tasks are complete and validation passes
- **THEN** `openspec archive <change> --yes` or `uv run wagents openspec validate` plus explicit archive guidance SHALL be used to keep specs synchronized.
