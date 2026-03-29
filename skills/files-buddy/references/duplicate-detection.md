# Duplicate Detection Reference

Rules for `clean` mode. Combine `fclones` for true duplicate groups, `rmlint` for filesystem lint, and `rclone dedupe --dry-run` for cloud remotes that allow duplicate names.

## Local Duplicate Workflow

1. Run `fclones group --format json <path>` to discover content-identical files.
2. Run `rmlint -o json:<file> <path>` to find empty files, empty dirs, broken links, and duplicate metadata.
3. Normalize both outputs into one report grouped by issue type.
4. Present reclaimable bytes and suggested keepers before any trash action.
5. Only trash after confirmation. Never pipe directly into a delete command.

## fclones Group Parsing

Use the JSON shape documented in `references/tool-integrations.md`.

| Field | Meaning | How to Use |
|-------|---------|------------|
| `stats.groups` | Duplicate groups found | High-level summary |
| `stats.redundant_bytes` | Reclaimable bytes | Blast-radius summary |
| `groups[].file_len` | Size of each duplicate set | Table sorting |
| `groups[].hash` | Content hash | Stable group identifier |
| `groups[].files[].path` | Candidate file path | Keeper / trash selection |

## Keeper Heuristics

Keep heuristics conservative. If a group is ambiguous, present the options instead of guessing.

1. Ignore hardlink clusters: same `st_ino` + `st_nlink > 1` means one file with multiple names, not multiple copies.
2. Prefer a non-conflict filename over obvious sync-conflict copies like `file (1).txt` or `copy of file.txt`.
3. Prefer files already inside the user's intended canonical folder over temporary inbox folders.
4. Prefer local, materialized files over cloud placeholders when hashes or sizes are uncertain.
5. If no clear keeper emerges, ask the user which copy to retain.

## rmlint Lint Types

| Lint Type | Meaning | Safe Default |
|-----------|---------|--------------|
| `duplicate_file` | Same content, one original + duplicates | Keep original, preview duplicates |
| `emptyfile` | Zero-byte file | Show separately; often safe to trash |
| `emptydir` | Empty directory | Remove only after parent operations finish |
| `badlink` | Broken symlink | Show as lint, do not auto-fix |

Use `rmlint` for lint reporting, not blind execution. Review the JSON output rather than relying on generated shell scripts.

## Cloud Duplicate Handling

Google Drive-style remotes can contain files with the same name in one directory. Use:

```bash
rclone dedupe --dry-run remote:path
```

Recommended modes:

- `list` / dry-run first for inspection
- `rename` when the user wants to preserve all variants
- `newest`, `oldest`, `largest`, `smallest` only after explicit confirmation

## Edge Cases

| Issue | Why It Matters | Mitigation |
|-------|----------------|------------|
| Zero-byte files | Fast to detect but often intentional placeholders | Report separately from hash-based duplicates |
| NFC / NFD paths | Visually identical names can compare differently | Normalize paths before presenting groups |
| Case-insensitive volumes | `Photo.jpg` vs `photo.jpg` may collide on move | Check rename plan before execution |
| Evicted cloud files | Placeholder size/hash data can be wrong | Materialize before hash-based comparison |
| Hardlinks | Look like duplicates by path count | Compare inode and link count before trashing |

## Presentation Shape

Show duplicate groups as:

- keeper candidate
- duplicate count
- total reclaimable bytes
- paths in the group

Then show lint issues (`emptydir`, `badlink`, `emptyfile`) in a separate section so the user can confirm them independently.
