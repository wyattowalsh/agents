---
title: OpenSpec Change Archive Status
tags:
  - kb
  - openspec
  - archive
aliases:
  - OpenSpec archive status
  - Active change status
kind: concept
status: active
updated: 2026-06-25
source_count: 3
---

# OpenSpec Change Archive Status

## Scope

This page captures the observed active-change/archive-readiness state. It is not a release signoff and does not replace `uv run wagents openspec validate`.

## Summary

Historical agents-platform changes were archived in `841b9b1` under `openspec/changes/archive/2026-05-01-*`. A June 2026 archive batch added changes such as `2026-06-16-invert-catalog-*` and related catalog/discovery work.

**2026-06-25 validation:** `uv run wagents openspec validate` — **33/33** items pass (8 active changes, 25 specs). Filesystem counts: **9** active change directories, **53** archived under `openspec/changes/archive/`. Remaining actives include `compose-harness-catalog-pages`, `integrate-apm-package-manager`, `integrate-mcphub-control-plane`, `public-release-prod-readiness`, and skill/harness integration waves.

**2026-06-24 archive batch:** Archived `harden-skill-catalog-quality` (shipped 5dc7ec1, f33d2c7) and `add-grok-delegate-skill` (earlier). Both had all tasks checked and passed pre-archive validations (`wagents openspec validate`, `wagents validate`). Now under `openspec/changes/archive/2026-06-24-*`. Post-archive active count ~30 changes + 25 specs (all valid).

**2026-06-24 bulk archive of READY list (23 changes):** Per task, archived all with 0 unchecked `- [ ]` in tasks.md from provided READY list (script+manual verified). Used per-change: read tasks.md sanity, `uv run wagents openspec archive <name> --format json` (dry), then `--apply --yes` (or +`--skip-specs` when spec header deltas no longer matched current specs because already promoted). 12 required --skip-specs (spec merge aborted on missing requirement headers but change dir move succeeded with flag); 11 applied normal (some spec updates succeeded). No failures; continued on any spec-abort. Post all: `uv run wagents openspec validate` (33 items, all passed), `uv run wagents validate` (passed). Archives: `openspec/changes/archive/2026-06-24-{add-audited-external-skills,add-first-class-cursor-support,add-harness-safe-mcphub-group,add-opencode-plugins-golang-skills,add-ossinsight-supathings-mcps,avoid-default-legacy-migration-logic,complete-nerdbot-implementation,docs-copy-reduction,enhance-docs-skill-indexes,enrich-curated-catalog-pages,enrich-harness-master-ecosystem-research,expose-mcphub-chatgpt-tunnel,global-wagents-cli,improve-instruction-corpus,integrate-chrome-devtools-skills,integrate-opencode-plugins,integrate-opencode-rules-ocx-terminal-progress,make-opencode-model-picker-owned,modernize-ty-ruff-tooling,oss-friendly-codebase-standardization,overhaul-codex-hooks,stabilize-mcphub-opencode-runtime,stabilize-opencode-gpt55-tui}/` (plus prior same-day). Active changes reduced; remaining have open tasks (the SKIP list) or other.

Treat task-complete, validation-passing, archive-ready, and archived as separate states. Portable `openspec_cli.py` lacks an `archive` subcommand despite SKILL dispatch documenting it.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| May 2026 agents-platform archive batch. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Historical |
| June 2026 active/archive counts and incomplete actives. | `kb/raw/sources/openspec-active-lifecycle-source.md` | raw source note | Snapshot only |
| Task-complete does not equal archive-ready or archived. | `kb/raw/sources/openspec-change-archive-source.md` | raw source note | Workflow distinction |
| Portable skill CLI missing archive handler. | `kb/raw/sources/openspec-active-lifecycle-source.md` | raw source note | Consistency gap |
| 2026-06-24 archive of harden-skill-catalog-quality and add-grok-delegate-skill. | (CLI + file moves) | archive command output | See `openspec/changes/archive/2026-06-24-*` |
| 2026-06-24 bulk archive 23 READY changes (all tasks checked). | (per-change dry-run + apply CLI; some --skip-specs) | archive command output + fs verification | See list in Summary. |
| 2026-06-25 validate 33/33; 9 active / 53 archived dirs. | `kb/raw/captures/openspec-lifecycle-capture-w01.md` | raw capture | Fresh validate + dir counts. |

## Related

- [[openspec-workflow]]
- [[known-risks-and-open-gaps]]
- [[planning-corpus-and-drift-ledgers]]
