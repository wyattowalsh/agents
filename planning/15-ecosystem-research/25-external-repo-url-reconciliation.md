# External Repo URL Reconciliation

## Result

The available source ledger reconciles to 93 contiguous records, `EXT-001` through `EXT-093`, with no duplicate IDs, repos, or URLs.

## Evidence

| check | result |
|---|---|
| declared source count | 93 |
| observed source records | 93 |
| normalized records | 93 |
| duplicate IDs | none |
| duplicate repos | none |
| duplicate URLs | none |
| missing expected IDs | none |
| unexpected IDs | none |
| additions | none recorded |
| removals | none recorded |

## Current URL Set

No separate pasted URL artifact was found in the repository during implementation. The source ledger at `planning/manifests/external-repo-evaluation-final.json` is therefore treated as the current URL set for this pass.

Future pasted URL deltas must be recorded in `planning/manifests/external-repo-url-reconciliation.json` with explicit `additions` and `removals` rather than inferred from prose.

## Quarantine IDs

The intake handoff preserves denied-by-default treatment for:

- `EXT-011` `Soju06/codex-lb`
- `EXT-015` `rynfar/meridian`
- `EXT-017` `griffinmartin/opencode-claude-auth`
- `EXT-084` `SnailSploit/Claude-Red`
