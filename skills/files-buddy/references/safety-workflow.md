# Safety Workflow Reference

Manifest-based safety system for auditable, reversible file operations. Every mutating action records a manifest before execution and validates it before undo.

## Manifest JSON Schema

```json
{
  "version": "1.0",
  "created": "2026-03-28T14:30:00Z",
  "mode": "organize|clean|rename|flatten|archive|sanitize|watch",
  "intent": "user's natural language description of what they wanted",
  "target_path": "/absolute/path/to/target",
  "cloud_tagged": false,
  "status": "open|closed|partial|undone",
  "tools_used": ["fclones", "gomi"],
  "operations": [
    {
      "type": "move|rename|trash|archive|sanitize",
      "status": "completed|failed",
      "source": "/absolute/source/path",
      "destination": "/absolute/dest/path",
      "timestamp": "2026-03-28T14:30:01Z",
      "blake3": "abc123...",
      "size_bytes": 12345,
      "st_mode": 33188,
      "st_ino": 67890
    }
  ],
  "summary": {
    "total_ops": 42,
    "completed_ops": 42,
    "failed_ops": 0,
    "total_bytes": 1234567,
    "duration_seconds": 12.5,
    "closed_at": "2026-03-28T14:30:12Z"
  }
}
```

`cloud_tagged` and `tools_used` are optional annotations added when the caller knows that context up front. Operation entries may use `size_bytes` or `bytes`; normalize both into `summary.total_bytes`. Manifest rows are finalized operation records: runtime code may track preview or in-progress state separately, but `manifest-manager.py append` should persist each operation once in its final `completed` or `failed` state. Completed non-`mkdir` operations must include `source`/`path`, `destination`/`target`, `timestamp`, and a recorded BLAKE3 hash.

## Atomic Write Protocol

1. Write manifest to `~/.files-buddy/manifests/{filename}.tmp`
2. `os.rename()` to `{filename}.json` (atomic on POSIX)
3. On crash, `.tmp` file is recovery signal
4. Create `~/.files-buddy/manifests/` with mode 0o700 on first use
5. Filename format: `{YYYY-MM-DDTHH-MM-SS}-{uuid8}-{mode}.json`

## Manifest Lifecycle

| State | Meaning | Transition |
|-------|---------|------------|
| open | Created, operations in progress | → closed, partial |
| closed | All operations completed successfully | → undone |
| partial | Interrupted or batch failure | Manual recovery needed |
| undone | Successfully reversed | Terminal state |

## Trash Hierarchy

### macOS

1. `gomi` (if installed) — XDG-compliant, cross-platform
2. `trash` CLI (built-in macOS 15+ / Homebrew on older)
3. `.files-buddy-trash/{manifest-id}/{relative-path}` fallback

### Linux

1. `gomi` (if installed)
2. `gio trash` (GNOME/freedesktop)
3. `.files-buddy-trash/{manifest-id}/{relative-path}` fallback

### NEVER

- `rm` — permanent deletion
- `trash-cli` npm/Python — uses wrong path on macOS (~/.local/share/Trash/ instead of ~/.Trash)

### .files-buddy-trash Structure

```
.files-buddy-trash/
  {manifest-id}/
    original/relative/path/file.txt
```

## TOCTOU Material Drift Detection

Before executing each batch:

1. Count files in target directories
2. Compare to plan counts
3. Material drift = any of:
   - File count changed >10%
   - New files appeared in directories targeted for deletion
   - Files disappeared that were planned for move
4. On drift: HALT, re-preview, require fresh confirmation
5. Minor drift within intent contract: proceed (e.g., 502 .png files instead of 500)

## Undo Validation

Before reversing operations:

1. Parse manifest, validate JSON schema
2. Check status is "closed" (not "open" or "partial")
3. For each operation (reverse order):
   - For file operations: verify file exists at destination with matching BLAKE3 hash
   - For `mkdir`: verify destination exists
   - Verify source path is available (not occupied)
4. If any check fails: ABORT, report which operations cannot be undone
5. Execute reverse operations sequentially
6. Update manifest status to "undone"

## Permission Restoration

- Manifest records st_mode for each file
- On undo: restore original permissions via `os.chmod()`
- If permission restoration fails: log warning, continue (not fatal)
- Root-owned files: skip permission restoration, warn user

## Corruption Recovery

If manifest JSON parse fails:

1. Log error to `~/.files-buddy/recovery.log`
2. Report: "Manifest corrupted: {path}. Manual inspection needed."
3. Never auto-delete corrupted manifests
4. Suggest: check `.tmp` files for partial recovery

## Disk Space Warnings

Before operations:

1. Estimate total space needed (for trash/archive: 2x file size)
2. Check free space: `os.statvfs()`
3. If free < estimated: warn user
4. If free < 10% of disk: refuse to proceed without explicit user confirmation

## Cloud Safety Extensions

For cloud-tagged manifests:

1. Record `cloud_tagged: true` in manifest
2. Use local `.files-buddy-trash/` instead of gomi or OS trash (avoid sync of trash/deletion state)
3. After all operations: suggest `brctl status` / `rclone check`
4. Rate limit: insert delays between operations for cloud paths
