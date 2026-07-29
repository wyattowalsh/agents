# Design

## Frozen Contracts

These contracts are frozen for Wave 1a/1b. Do not weaken without a new change.

### Presence model (`wagents.skill_coverage`)

| Flag | Meaning |
| --- | --- |
| `store_present` | Readable `SKILL.md` under Skills CLI store (`~/.agents/skills/<name>` by default) |
| `projection_present` | Readable skill under harness global projection root |
| Cursor projection | Only `~/.cursor/skills/<name>` — never repo `.cursor/skills/**`, never store-only |

Tiers: `absent`, `store_only`, `projection_only`, `covered`.

### Cursor ensure (`ensure_cursor_authoritative_links`)

| Situation | Outcome |
| --- | --- |
| Missing projection + valid store body | create symlink → store realpath |
| Broken/wrong symlink | replace symlink only |
| Real dir, identical `SKILL.md` body | `already_correct` |
| Real dir, divergent body | `blocked` |
| No store body | `skipped_missing_store` |

Defaults to dry-run. Never removes real skill trees. Leaves repo
`_sync_skill_symlinks` unchanged.

### Sync planner buckets (`wagents skills sync`)

| Bucket | Cursor rule |
| --- | --- |
| `already_present` | preferred non-CLI owner **or** (`store_present` **and** `projection_present`) |
| `projection_ensure` | store present; projection missing/broken and ensure can create/repair |
| `projection_blocked` | store present; divergent real projection tree |
| `store_missing` | store absent → Skills CLI install planned |
| `internal_projection` | projection present without store (preserve; do not CLI overwrite) |
| `skipped` | not syncable / not targeted / optional excluded |

Apply: Skills CLI for `store_missing` only; after CLI batches call
`ensure_cursor_authoritative_links(..., dry_run=False)` for Cursor
`projection_ensure` (+ newly installed store names). Preserve Codex plugin /
OpenCode `skills.paths` non-CLI owner skips.

Compact default JSON: counts + samples. `--verbose` for full lists.

### Reconciliation

Summary MUST include `store_missing_by_agent` and `projection_missing_by_agent`.
Cursor MUST NOT false-zero when store is present and home projection is missing.

## Safety

- No live `--apply` against user home in Wave 1b cloud acceptance.
- Unit tests use temp `HOME` only.
- Generator remains read-only except writing the repo reconciliation packet.
