# Design

## Reconciliation Model

The reconciliation matrix has one row per observed asset:

- `skill` rows come from `collect_installed_inventory` over live supported
  harnesses merged with `collect_desired_sync_rows`.
- `plugin`, `plugin-cache`, and `extension` rows come from local repo config,
  selected home config files, and bounded native list commands.

Every row must have a terminal `action` and matching `classification`. The
allowed actions are:

- `synced` — desired asset is present in every target harness.
- `repo-source-synced` — repo source exists and no live install is required.
- `local-only-preserve` — user/local asset is accounted for and intentionally
  not promoted or synced by default.
- `curate-external` — promote only after an explicit source audit.
- `catalog-non-sync` — catalog entry is intentionally unresolved/non-syncing.
- `cache-refresh-needed` — cache is stale, but refresh needs a separate live
  action.
- `home-sync-needed` — repo/home config drift exists, but apply is not run here.
- `config-repair-needed` — local config prevents reliable validation.
- `blocked-needs-approval` — evidence is insufficient for automated action.

## Parallel Task Graph

The manifest embeds the executable task graph from the plan:

| Lane | Parallel | File ownership |
|------|----------|----------------|
| Coordinator | no | `planning/manifests/harness-reconciliation.json` |
| Skills desired | yes | catalog authoring + repo skills |
| Skills one-off | yes | installed external rows |
| Skills unprovenanced | yes | read-only discovered rows |
| Codex/Claude plugins | yes | plugin manifests and registry evidence |
| OpenCode plugins | yes | `opencode.json` + live diff evidence |
| Gemini/Grok plugins | yes | extension/config evidence |
| Validation | no | focused tests and repo gates |

## Safety

The generator is intentionally read-only except for writing the repo-local
manifest. It does not call `--apply`, install plugins, delete caches, or write
home config. Local absolute paths are recursively redacted to `~` or
`${REPO_ROOT}` before the manifest is written.

## Manual Assurance

The generated summary intentionally distinguishes:

- default desired sync missing counts,
- optional installed-external missing counts,
- query-blocked counts,
- local-only preserve rows,
- plugin cache drift,
- config repair blockers.

This makes "fully reconciled" mean every local asset has an accountable
disposition, not that every asset is installed everywhere.
