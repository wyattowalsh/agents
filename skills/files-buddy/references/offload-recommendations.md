# Offload Recommendations

Offload planning frees local Mac storage while keeping data recoverable elsewhere.
Offload is not deletion. Any action that removes the only copy is cleanup/archive, not offload.

## Scoring Model

Score each candidate 0-5 for:

| Factor | Higher score means |
|--------|--------------------|
| Local bytes saved | More local disk reclaimed |
| Coldness | Older and less accessed |
| Regeneration cost | Lower re-download/rebuild burden |
| Cloud quota fit | Enough remote quota and no duplicate billing surprise |
| Importance risk | Less likely to be critical or app-managed |
| Restore friction | Easy to re-download/materialize/mount |
| Verification confidence | Provider state and checks are machine-readable |

Recommend offload only when local savings are meaningful and restore confidence is medium or high.

## Provider Handling

### iCloud Drive

- Detect `~/Library/Mobile Documents/com~apple~CloudDocs`.
- Use `brctl status` and `fileproviderctl` where available; commands are macOS-version sensitive.
- `brctl evict <path>` or `fileproviderctl evict <path>` frees local bytes only when the file is fully synced.
- Never evict files with unsynced changes, package bundles, or app libraries without explicit path-level approval.

### Google Drive Desktop

- Detect `~/Library/CloudStorage/GoogleDrive-*`.
- Distinguish **Stream files** (on-demand, local bytes can be freed) from **Mirror files** (full local copy by design).
- Use Drive UI/provider state for final action when CLI state is ambiguous.
- Google Drive allows duplicate names; use `rclone dedupe --dry-run` only for duplicate-name review.

### rclone Remotes

- Use `rclone lsjson remote:path --recursive --hash` for inventory.
- Use `rclone copy --dry-run`, `rclone check`, and then approved copy/move flows.
- Prefer copy + verify + local trash staging over direct move for important data.

## Required Output

```json
{
  "action": "offload",
  "provider": "icloud|gdrive|rclone:<remote>",
  "path": "/absolute/path",
  "local_bytes_saved": 123,
  "cloud_bytes_added": 0,
  "prerequisites": ["provider reports synced"],
  "verification": ["brctl status shows no pending upload"],
  "repercussions": ["first open will re-download the file"],
  "restore_path": "open file or fileproviderctl materialize <path>",
  "approval_tier": "High"
}
```

## Hard Stops

- Provider reports unsynced files.
- User wants deletion from cloud rather than local eviction but asks for offload.
- Offload target is app-managed or a package bundle with unclear provider behavior.
- Local disk lacks space to materialize files required for verification.
