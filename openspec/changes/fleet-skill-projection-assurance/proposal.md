# Proposal

## Why

Skills CLI installs into the universal store (`~/.agents/skills`) do not equal
durable Cursor global coverage. Cursor reads `~/.cursor/skills` as the
authoritative home projection. Treating store/secondary presence as synced
false-zeros Cursor in dry-run and reconciliation packets.

## What Changes

- Wave 1a CUR: `ensure_cursor_authoritative_links` conflict matrix for home
  projection symlinks (create/repair symlink only; never `rm -r` real trees).
- Wave 1a INV: `wagents.skill_coverage` store/projection presence tiers; Cursor
  global projection is only `~/.cursor/skills` (repo `.cursor/skills/**` never
  counts); lazy cleanup hashing.
- Wave 1b SYNC: `wagents skills sync` planner buckets and apply wiring that uses
  presence APIs for Cursor and calls ensure after Skills CLI store batches.
- Wave 1b RECON: reconciliation summary fields
  `store_missing_by_agent` / `projection_missing_by_agent`.
- Wave 1b DOCS/TEST: ownership docs + focused sync/recon tests.

## Impact

- Cursor dry-run no longer reports already-present for store-only skills.
- Apply plans Skills CLI for `store_missing` only, then ensures Cursor
  projections for `projection_ensure` names.
- Codex plugin and OpenCode `skills.paths` non-CLI owner skips stay preserved.

## Out Of Scope

- Live `wagents skills sync --apply` against maintainer home in Wave 1b CI/cloud
  runs (wiring + temp-HOME unit tests only).
- Mass home symlink mutation outside temp test dirs.
- Changing Skills CLI itself.

## Risks

- Large fleets can OOM on full JSON lists — mitigated by compact default JSON
  (counts + samples) with `--verbose` for full lists.
- Divergent real directories under `~/.cursor/skills` stay blocked for manual
  review.
