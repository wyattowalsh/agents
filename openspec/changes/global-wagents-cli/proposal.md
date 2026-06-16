# Proposal

## Problem

`wagents` is wired to `ROOT = Path(__file__).parent.parent`, which works for `uv run wagents` inside a clone but breaks for `uv tool install` global binaries. Repo scripts under `scripts/` and `skills/skill-creator/scripts/` are resolved from the package parent instead of a discovered clone.

## Intent

Make `wagents` a globally installable control-plane CLI that discovers the agents repository at runtime, documents Git-based `uv tool install`, and adds plugin/telemetry hooks without changing the bundle-first distribution model.

## Scope

- Add runtime repo discovery (`WAGENTS_REPO_ROOT`, `--repo-root`, cwd walk, editable fallback).
- Add `wagents self install|upgrade|doctor|completion`.
- Normalize structured output helpers and doctor checks for install mode and repo discovery.
- Add opt-in local telemetry and entry-point plugin loading.
- Update distribution metadata and generated CLI docs.

## Out Of Scope

- PyPI publishing in the first pass.
- Bundling `skills/` or `scripts/` inside the wheel.
- Replacing `uv run wagents` for repo contributors.