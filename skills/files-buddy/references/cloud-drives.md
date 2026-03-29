# Cloud Drive Detection and Safety

## Detection

### macOS

| Provider | Path | Detection |
|----------|------|-----------|
| iCloud Drive | ~/Library/Mobile Documents/com~apple~CloudDocs/ | Check dir exists |
| Google Drive | ~/Library/CloudStorage/GoogleDrive-<email>/ | Glob GoogleDrive-* |
| Dropbox | ~/Library/CloudStorage/Dropbox-*/ | Glob Dropbox* |
| OneDrive | ~/Library/CloudStorage/OneDrive-*/ | Glob OneDrive-* |
| Box | ~/Library/CloudStorage/Box-*/ | Glob Box-* |

All File Provider providers use ~/Library/CloudStorage/ except iCloud.

Detection code:

```python
from pathlib import Path

cloud_storage = Path.home() / "Library/CloudStorage"
if cloud_storage.exists():
    for entry in cloud_storage.iterdir():
        # match provider by prefix
```

### Linux

- rclone mounts: `mount | grep "fuse.rclone"`
- GNOME Online Accounts: GVfs mounts

---

## iCloud Specifics

### brctl Commands

| Command | Purpose |
|---------|---------|
| brctl download <path> | Materialize evicted file |
| brctl evict <path> | Evict file (keep in cloud) |
| brctl status | Unsynced items |
| brctl quota | Available space |
| brctl monitor | Real-time sync |

### fileproviderctl

| Command | Purpose |
|---------|---------|
| fileproviderctl materialize <path> | Download file |
| fileproviderctl evict <path> | Evict file |

### Evicted File Detection

- macOS 14+ (Sonoma): Files keep original names ("dataless files"). Use `mdls` or NSMetadataQuery.
- Pre-Sonoma: Hidden `.filename.ext.icloud` stub files.

---

## Google Drive Specifics

- Stream mode: files fetched on demand, standard tools trigger download
- Duplicate filenames: GDrive allows identical names in same folder
- `rclone dedupe gdrive:path` modes: newest, oldest, largest, smallest, rename, list
- `rclone lsjson gdrive:path` for structured listing
- File IDs are opaque, not paths

---

## Safety Rules for Cloud Operations

1. NEVER auto-delete -- stage cloud removals into local `.files-buddy-trash/` so deletion never syncs to all devices
2. Materialize evicted files before size/hash analysis (dust/fclones report wrong sizes on placeholders)
3. Warn before bulk ops about sync implications
4. Rate-limit batch ops: `pueue parallel 2` for cloud (vs 8 for local)
5. Detect conflict copies: patterns `(1)`, `(conflict)`, ` 2.txt`
6. Cloud ops always at least Medium friction tier
7. After batch ops, suggest waiting for sync: `brctl status` / `rclone check`

---

## Gotchas

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Placeholder files | 0-byte size reports | Materialize first |
| Sync conflicts | Duplicate files created | Detect conflict patterns |
| Rate limiting | API throttle on bulk ops | pueue with delays |
| Deletion syncs | File lost on all devices | Local staging first |
| Sync lag | Changes not immediate | Wait + verify |
| xattr stripping | iCloud strips non-syncable xattrs | Don't rely on xattrs |
