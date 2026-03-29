# Organization Strategies Reference

Rules and templates for `organize` and `watch` mode. Prefer deterministic rules, preview with `organize sim`, then execute with `organize run`.

## Workflow

1. Start from the user's intent: type buckets, date buckets, project buckets, or a custom review queue.
2. Generate YAML for a single target root. Do not let a rule move files outside the scope-pinned directory unless the user explicitly asked for that destination.
3. Run `organize sim <config>` and capture the planned moves.
4. Check collisions, case-only renames, and hidden-file handling before execution.
5. Keep unmatched files in place or route them to `Review/` — never guess destructive rules.

## Common Strategies

| Strategy | Best For | Core Rule Shape |
|----------|----------|-----------------|
| Type buckets | Messy Downloads/Desktop folders | `extension -> destination subfolder` |
| Date buckets | Photos, scans, statements | `modified date -> YYYY/YYYY-MM` |
| Project buckets | Work folders with mixed artifacts | detect project root, move by project name |
| Review queue | Unknown file sets | matched files move, everything else stays |

## Extension-to-Category Map

Use broad, predictable buckets first. Add narrower subfolders only when the user asks.

| Category | Extensions |
|----------|------------|
| Images | `jpg`, `jpeg`, `png`, `gif`, `webp`, `heic`, `svg`, `tif`, `tiff` |
| Video | `mp4`, `mov`, `mkv`, `avi`, `webm` |
| Audio | `mp3`, `m4a`, `wav`, `flac`, `aac` |
| Documents | `pdf`, `doc`, `docx`, `txt`, `rtf`, `md`, `pages` |
| Spreadsheets | `csv`, `xls`, `xlsx`, `numbers` |
| Archives | `zip`, `tar`, `gz`, `bz2`, `xz`, `zst`, `rar`, `7z` |
| Code / Projects | `py`, `js`, `ts`, `tsx`, `go`, `rs`, `java`, `c`, `cpp`, `sh` |

## YAML Templates

### Type Buckets

```yaml
rules:
  - locations:
      - ~/Downloads
    filters:
      - extension: [jpg, jpeg, png, gif, webp]
    actions:
      - move: ~/Downloads/Images/{name}.{extension}

  - locations:
      - ~/Downloads
    filters:
      - extension: [pdf, doc, docx, txt]
    actions:
      - move: ~/Downloads/Documents/{name}.{extension}
```

### Date Buckets

```yaml
rules:
  - locations:
      - ~/Scans
    filters:
      - extension: [pdf, jpg, png]
    actions:
      - move: ~/Scans/{created.year}/{created.month}/{name}.{extension}
```

### Project Buckets

Treat a directory as a project root when it contains one of:

- `pyproject.toml`, `requirements.txt`
- `package.json`, `tsconfig.json`
- `go.mod`, `Cargo.toml`
- `.git/`

When multiple signals exist, keep the directory intact instead of splitting it by file type.

## Collision Handling

1. Never overwrite.
2. Detect case-only collisions on case-insensitive filesystems before execution.
3. Prefer deterministic suffixes like `-1`, `-2`, `-3`.
4. Show collisions in the preview summary so the user can change the rule if needed.
5. Preserve relative ordering for numbered files (`IMG_001`, `IMG_002`, ...).

## Watch Mode Guidance

- Restrict watchers to hot folders like `~/Downloads` or inbox-style scan folders.
- Use explicit extension filters in `watchexec` to limit noise.
- Reuse the same organize YAML that passed `organize sim`.
- Log every watcher-driven move to the manifest just like manual runs.
- Stop and recreate the watcher when rules change; do not mutate a live watcher in place.
