# Rename Patterns Reference

Rules for `rename` mode using `f2`. Preview first, then execute with `-x`. Use native undo support (`f2 -u` in the installed version) when reversing a rename batch.

## Workflow

1. Translate the user's intent into an `f2` expression or replacement pattern.
2. Run `f2` in preview mode (default) and capture the before/after table.
3. Check for collisions, case-only renames, and directory escapes before execution.
4. Present the diff to the user.
5. Execute with `-x` only after confirmation.
6. Prefer `f2 -u` for undo when the rename batch maps cleanly to a single native undo record.

## Pattern Catalog

| Intent | Example Command Shape | Notes |
|--------|------------------------|-------|
| Replace noisy text | `f2 -f 'FINAL' -r '' <path>` | Good for removing suffix clutter |
| Normalize separators | `f2 -f '[ _]+' -r '-' <path>` | Preview case-only collisions on APFS |
| Add sequence numbers | `f2 -f '^' -r '{nr}-' <path>` | Use `{nr}` for stable ordering |
| Prefix with parent dir | `f2 -f '^' -r '{p}-' <path>` | Useful after flattening |
| Rebuild from EXIF | `f2 -f '.*' -r '{xt.date}-{xt.make}-{nr}.{.ext}' <path>` | Preview long filenames |
| Rebuild from ID3 | `f2 -f '.*' -r '{id3.artist} - {id3.title}.{.ext}' <path>` | Great for messy music folders |
| Hash-based names | `f2 -f '.*' -r '{hash.blake3}.{.ext}' <path>` | Useful for collision-proof archival names |

## Supported Variable Families

Use only variables verified in the installed `f2` version and mirrored in `references/tool-integrations.md`.

| Family | Examples | Best For |
|--------|----------|----------|
| Built-in | `{.ext}`, `{nr}`, `{p}` | numbering, extension preservation, parent naming |
| EXIF | `{xt.make}`, `{xt.model}`, `{xt.date}` | photos and scans |
| ID3 | `{id3.artist}`, `{id3.title}`, `{id3.album}` | music files |
| Hash | `{hash.blake3}` | canonical archival names |

## CSV / Batch Review

If the rename set is large or sensitive:

1. Export the preview to CSV if the installed `f2` version supports it.
2. Let the user review the mapping outside the terminal.
3. Re-run with the reviewed mapping.

When CSV export is unavailable, keep the terminal preview as the source of truth and limit the batch size shown at once.

## Conflict Handling

- Never overwrite an existing file.
- Prefer `--fix-conflicts-pattern` when the user wants automatic suffixes.
- On case-insensitive filesystems, treat case-only changes as collisions unless the operation is serialized carefully.
- When two source files map to the same destination, stop and ask the user which naming scheme to keep.

## Safety Notes

- Rename within the same scope-pinned directory unless the user explicitly asks for a move.
- Materialize cloud placeholders before metadata-driven patterns.
- Keep previews NUL-safe and path-safe when filenames contain spaces, newlines, or leading dashes.
- For very large batches, show a sampled preview plus summary counts before execution.
