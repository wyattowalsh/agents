## Summary

Add a new `new-project` skill that plans and safely bootstraps modern software projects from typed presets and capabilities.

## Why OpenSpec

This change affects tracked skill assets, evals, helper scripts, generated README/catalog surfaces, and downstream agent installs. It is non-trivial because it introduces a reusable project-initialization skill with safety boundaries for file mutation, package generators, cloud providers, and generated AI instructions.

## Problem

Starting a new repository currently requires manually combining multiple conventions: Python `uv`, Node `pnpm`, docs frameworks, AI assistant instruction files, quality gates, GitHub Actions, releases, design guidance, and optional cloud/data/AI stacks. Existing specialist skills cover pieces of this, but there is no single preference-driven initializer that can produce a safe blueprint before mutating files.

## Proposed Change

Create `skills/new-project/` as a concise router backed by:

- typed capability and preset catalogs under `data/`
- focused references for project setup domains
- deterministic JSON-emitting scripts for preflight, blueprint, catalog validation, plan validation, doctor, and reports
- self-contained HTML templates for blueprints, preferences, and scaffold audits
- eval coverage for dispatch, implicit triggers, negative controls, preference extension, docs profiles, cloud opt-in, and safety gates

## Generated Surfaces To Refresh

- `README.md` from `uv run wagents readme` if the skill index changes
- generated docs catalog pages via `docs-steward` if needed
- skill package dry-run output from `uv run wagents package new-project --dry-run`

## Non-Goals

- Do not create AI agents or MCP servers.
- Do not provision cloud resources by default.
- Do not run destructive migrations or overwrite existing files without explicit file-by-file approval.
- Do not commit generated downstream OpenSpec artifacts.
