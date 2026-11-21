# Rename Patterns

F2 supplies a preview. Files Buddy owns the selected exact mapping, approval,
collision checks, manifest, and recovery. Native F2 history is supplementary
and is not a second undo authority.

## Contents

1. Preview workflow
2. Versioned patterns
3. Collision and metadata checks
4. Execution boundary

## Preview Workflow

1. Identify the specific local files and their project/sidecar ownership.
2. Capture the installed F2 version. The current parser fixture is 2.2.2.
3. Preview with F2's default non-executing behavior and `--json`; do not add
   `--exec`, `--allow-overwrites`, `--clean`, or `--undo`.
4. Import the report:

```bash
python scripts/storage-audit.py observe f2 preview \
  --version 2.2.2 --input rename-preview.json
```

5. Resolve `base_dir`/`source` and `target_dir`/`target` into absolute mappings.
6. Verify every destination, case/Unicode collision, dependency, and source
   fingerprint. Select exact operations and review their restore behavior.
7. Use only a supported common-executor operation after approval of its digest.

The importer never launches F2 or changes files. Unknown versions and malformed
shapes fail explicitly. Non-ok/unchanged statuses and duplicate destination
strings remain conflicts. A relative mapping is not yet an executable plan.

## Versioned Patterns

These are **preview shapes** for the source-reviewed F2 2.2.2 grammar:

| Intent | Example | Notes |
| --- | --- | --- |
| Remove noisy text | `f2 --json -f 'FINAL' -r '' "$scope"` | Review every resulting name |
| Normalize separators | `f2 --json -f '[ _]+' -r '-' "$scope"` | Check case/Unicode collisions separately |
| Add sequence numbers | `f2 --json -f '^' -r '{%03d}-' "$scope"` | `%03d` is the index syntax, not `{nr}` |
| Prefix parent name | `f2 --json -f '^' -r '{p}-' "$scope"` | Avoid flattening project structure |
| ID3 labels | `f2 --json -f '.*' -r '{id3.artist} - {id3.title}.{ext}' "$scope"` | Content/metadata reads require consent |
| Content hash names | `f2 --json -f '.*' -r '{hash.sha256}.{ext}' "$scope"` | Content reads; no BLAKE3 variable in this grammar |

`{ext}` is the extension variable; `{.ext}` is not. The index family uses
`{%d}`/`{%03d}`. Built-in EXIF variables use `x.*` or `exif.*`; for example
`{x.make}` and `{x.cdt.YYYY}`. `xt.*` requests ExifTool fields and can require
that external executable. ID3 variables such as `{id3.artist}` and
`{id3.title}` are supported. Hash variables in this tagged grammar are sha1,
sha256, sha512, md5, xxh32, and xxh64; do not claim `{hash.blake3}` support.

Metadata/hash patterns can read file content and hydrate cloud placeholders.
They are not appropriate for a broad metadata-only scan. Preserve extensions
according to the actual preview, including compound-extension edge cases.

## Collision and Metadata Checks

Never overwrite existing files. Also detect duplicate targets within the same
plan, directories used as destinations, case-only renames on a case-insensitive
volume, Unicode-normalized lookalikes, and names that escape approved roots.
A tool's `status: ok` is not a substitute for fresh checks at execution time.

`--fix-conflicts-pattern` only specifies a suffix format; it does not itself
turn on conflict fixing. If the user wants suffixes, generate and review the
resulting final mapping. Never let a later rescan silently choose new suffixes
or include additional files under an earlier approval.

CSV workflows are optional input formats, not authorization. A sampled preview
may help a human navigate a large batch, but the exact complete mapping and
its digest must remain reviewable. New files are excluded from the approved
set; changed inputs block their affected operations.

## Execution Boundary

The common executor supports only its explicitly qualified local operations.
Unknown provider state, unqualified metadata, special files, cross-volume or
case-only semantics require a report/manual handoff until qualified. Reverse
plans verify current destinations and refuse occupied original paths. Do not
run `f2 -u` behind the manifest manager's back.

Primary grammar: [F2 v2.2.2 variable expressions](https://github.com/ayoisaiah/f2/blob/v2.2.2/replace/variables/variable_regex.go).
The tagged help fixture can retain an older printed version banner; qualify
actual installed `--version` output instead of copying that banner as evidence.
