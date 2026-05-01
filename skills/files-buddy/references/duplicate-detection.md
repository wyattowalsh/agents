# Duplicate Detection Reference

Rules for `dedupe`, `clean`, and `cleanup-plan` modes. Combine `fclones` for true duplicate groups, `rmlint` for filesystem lint, `czkawka_cli` for broad media/similarity detection, and `rclone dedupe --dry-run` for cloud remotes that allow duplicate names.

## Engine Policy

| Engine | Use For | Safe Default | Never Do |
|--------|---------|--------------|----------|
| `fclones` | Fast exact duplicates by content hash | `fclones group --format json <path>` | Run remove/link/dedupe without approved plan |
| `rmlint` | Exact duplicates plus empty files/dirs, broken links, bad IDs | `rmlint -o json:<file> <path>` | Execute generated shell script blindly |
| `czkawka_cli dup` | Exact duplicates when user wants Czkawka reports/cache | `czkawka_cli dup -d <path> --json-pretty` | Use delete methods before approval |
| `czkawka_cli image/video/music` | Similar images, videos, and music | report file only | Treat perceptual matches as safe duplicates |
| `rclone dedupe` | Duplicate names and remote hash checks | `--dry-run --dedupe-mode list` | Let default interactive/delete behavior run unattended |
| dupeGuru / Video Duplicate Finder | GUI or specialist review queue | export/report only | Automate deletions from fuzzy groups |
| `imagededup` | Advanced image near-duplicate analysis | report hashes/clusters | Auto-trash similar images |
| `jdupes` / `rdfind` / `duff` | Fallback exact duplicate tools | report/list only | `jdupes --quick`, partial-only checks, or shell piping to delete |

## Local Duplicate Workflow

1. Run `fclones group --format json <path>` to discover content-identical files.
2. Run `rmlint -o json:<file> <path>` to find empty files, empty dirs, broken links, and duplicate metadata.
3. Optionally run `czkawka_cli dup` when Czkawka is installed and the user wants a second exact engine.
4. Normalize outputs into one report grouped by issue type.
5. Present reclaimable bytes, keeper rationale, dependency impact, and restore path before any trash action.
6. Only trash after confirmation. Never pipe directly into a delete command.

## Similar Media Workflow

1. Use `czkawka_cli image`, `czkawka_cli video`, or `czkawka_cli music` for perceptual candidate groups.
2. Treat every group as **review only**. Similar does not mean duplicate.
3. Preserve originals by default. Suggested keepers may consider resolution, bitrate, duration, path intent, and edit metadata.
4. Produce contact-sheet paths or report files when practical; ask the user to choose keepers.
5. Never mix similar-media reclaimable bytes into exact-duplicate savings without a separate label.

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
rclone dedupe --dry-run --dedupe-mode list remote:path
```

Recommended modes:

- `list` / dry-run first for inspection
- `rename` when the user wants to preserve all variants
- `newest`, `oldest`, `largest`, `smallest` only after explicit confirmation
- `--by-hash` only when the backend supports reliable hashes and the user approved hash-based remote review

## Edge Cases

| Issue | Why It Matters | Mitigation |
|-------|----------------|------------|
| Zero-byte files | Fast to detect but often intentional placeholders | Report separately from hash-based duplicates |
| NFC / NFD paths | Visually identical names can compare differently | Normalize paths before presenting groups |
| Case-insensitive volumes | `Photo.jpg` vs `photo.jpg` may collide on move | Check rename plan before execution |
| Evicted cloud files | Placeholder size/hash data can be wrong | Materialize before hash-based comparison |
| Hardlinks | Look like duplicates by path count | Compare inode and link count before trashing |
| Similar media | Looks redundant but may differ in quality or edits | Review queue only, no auto-trash |
| Package bundles | Directory looks like a file in Finder | Treat as app-managed until dependency owner is clear |

## Presentation Shape

Show duplicate groups as:

- keeper candidate
- duplicate count
- total reclaimable bytes
- paths in the group

Then show lint issues (`emptydir`, `badlink`, `emptyfile`) in a separate section so the user can confirm them independently.

Exact duplicate groups and similar-media groups must be rendered in separate dashboard sections and require separate approvals.
