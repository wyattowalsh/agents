---
title: OpenSpec Workflow
tags:
  - kb
  - openspec
  - workflow
aliases:
  - OpenSpec operating workflow
kind: concept
status: active
updated: 2026-05-01
source_count: 4
---

# OpenSpec Workflow

## When To Use OpenSpec

Use OpenSpec for non-trivial changes to public asset formats, downstream agent tooling, generated docs, sync behavior, validation behavior, or multiple coordinated surfaces. Direct edits may be appropriate for trivial local-only content, but public contracts and cross-harness behavior need the OpenSpec workflow.

## Operating Commands

| Need | Command |
|------|---------|
| Diagnose OpenSpec tooling | `uv run wagents openspec doctor` |
| Validate specs and changes | `uv run wagents openspec validate` |
| Get JSON status for a change | `uv run wagents openspec status --change <name> --format json` |
| Get AI-readable instructions | `uv run wagents openspec instructions <artifact> --change <name> --format json` |
| Initialize downstream artifacts | `uv run wagents openspec init --apply` |
| Update downstream artifacts | `uv run wagents openspec update --apply` |

## Rules To Preserve

- Wrapper commands set `OPENSPEC_TELEMETRY=0` unless the user opts in.
- OpenCode repo-managed config must remain model-neutral.
- Generated downstream tool artifacts should not be committed unless explicitly promoted to repo-owned source.
- Tasks should be dependency-ordered and mark independently parallelizable tasks with `[P]`.
- Use `uv run wagents openspec ... --format json` when downstream AI tools need machine-readable state.

## Active Change And Archive Readiness

Task-complete, validation-passing, and archive-ready are separate states. Read-only research found active OpenSpec change files with checked task boxes, but archive readiness still depends on validation/status evidence and the release archive checklist. Use [[openspec-change-archive-status]] before claiming active changes are ready to archive or release.

## Related Pages

- [[agent-asset-model]]
- [[wagents-cli-and-automation]]
- [[canonical-generated-surfaces]]
- [[harness-and-platform-sync]]
- [[developer-commands]]
- [[known-risks-and-open-gaps]]
- [[openspec-change-archive-status]]

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| OpenSpec is required for non-trivial changes to public asset formats, downstream tooling, generated docs, sync behavior, validation behavior, or coordinated surfaces. | `kb/raw/sources/agents-md.md`; `kb/raw/sources/openspec-config.md` | raw source notes | Repo standards and OpenSpec config. |
| `openspec/config.yaml` lists supported downstream agents and tool mappings. | `kb/raw/sources/openspec-config.md` | raw source note | Derived from OpenSpec config. |
| OpenSpec wrapper commands should use `uv run wagents openspec ...` for automation. | `kb/raw/sources/openspec-config.md` | raw source note | Derived from OpenSpec config. |
| Generated public surfaces include README and docs catalog pages. | `kb/raw/sources/openspec-config.md` | raw source note | Derived from OpenSpec config. |
| `wagents` implements OpenSpec wrapper command families alongside docs, package, hooks, and eval commands. | `kb/raw/sources/wagents-internals.md` | raw source note | CLI implementation source. |
| Active-change archive readiness is distinct from checked task boxes. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Archive status evidence. |
