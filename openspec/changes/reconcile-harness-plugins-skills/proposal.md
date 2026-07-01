# Proposal

## Why

Local harness state now spans Skills CLI installs, repo-owned custom skills,
curated external authoring rows, Codex native plugin caches, OpenCode runtime
plugins, Gemini extensions, Grok skill roots, and harness-specific config
projections. A normal `wagents skills sync --dry-run` proves the default desired
skill set, but it does not account for one-off installed externals,
unprovenanced local skills, native plugin caches, or extension-only surfaces.

This change adds a durable reconciliation evidence packet so every locally
accessible skill/plugin surface has a terminal disposition: synced, repo-source
synced, local-only preserve, catalog non-sync, cache refresh needed, home sync
needed, config repair needed, or blocked pending approval.

## What Changes

- Add `scripts/generate_harness_reconciliation.py`, a read-only local evidence
  generator that builds a redacted matrix from installed skill inventory,
  desired catalog rows, and local plugin/extension config.
- Add `planning/manifests/harness-reconciliation.json`, the current
  reconciliation snapshot for local harnesses and plugin/skill surfaces.
- Add tests that enforce matrix coverage, terminal actions, default sync
  coverage, redaction, and the known plugin/config follow-up buckets.
- Add OpenSpec artifacts for the reconciliation workflow and task graph.

## Impact

- Maintainers can inspect the reconciliation matrix before deciding whether to
  run any live install, home sync, or cache refresh.
- Curated external promotion stays source-first: third-party skills remain out
  of `skills/` unless explicitly authored as repo-owned skills.
- The default desired sync set remains unchanged; this change does not perform
  live installs or mutate home harness configs.

## Scope

- Evidence generator, static manifest, OpenSpec docs, and focused tests.

## Out Of Scope

- Running `wagents skills sync --apply`, live `npx skills add`, plugin installs,
  cache deletion, or home config rewrites.
- Promoting any one-off installed external skill without a separate audit row.
- Editing generated public docs beyond whatever a future docs regeneration
  requires.

## Risks

- Local CLI inventory can time out. Mitigate by recording query failures
  separately from proven missing installs, increasing timeout for the generator,
  and preserving fallback warnings in the manifest.
- Plugin names can contain file URIs or absolute paths. Mitigate by recursively
  redacting every string before writing the manifest and testing for local path
  leakage.
