# Tool Integrations

Use the smallest tool set that supplies the evidence needed for the current mode.
The machine-readable capability record is `assets/tool-registry.json`. A fixture
version means its JSON contract is tested; it does not claim a native macOS run.
No adapter grants mutation permission, installs a tool, or imports upstream skill
instructions.

## Contents

1. Selection and capability limits
2. Bundled observation CLI
3. Correct command and parser contracts
4. Safe rules and optional workflows
5. Provenance and upgrades

## Selection and Capability Limits

| Need | Primary option | Bundled support | Limits |
| --- | --- | --- | --- |
| Bounded local metadata | `storage-audit.py scan`, optional fd | Native metadata producer | No file content reads; explicit hidden/mount policy; SQLite outside scope |
| Mac storage observations | Mole (`mo`) V1.73.0 | Analyze/status/history JSON import or fixed argv execution | No clean/purge/optimize/uninstall/slim execution |
| Exact duplicates | Built-in explicit SHA-256 review; fclones 0.35.0 | Built-in local hashing; imported fclones JSON | No remove/link/reflink/dedupe mutation; imported hashes retain their upstream identity |
| Rename proposals | F2 2.2.2 | Preview JSON import | Native execution/undo is not Files Buddy's recovery authority |
| Compact tree display | dust 1.2.7 | DisplayNode JSON import | Formatted sizes remain strings; not exact byte accounting |
| Configured remote listing | rclone 1.76.0 | `lsjson` import or fixed nonrecursive metadata listing | No sync/move/delete/hash/content transfer |
| Larger external trees | gdu or ncdu | Optional operator workflow | Choose one; gdu exclusive-size support is Linux-specific, not an APFS promise |
| Independent backup | restic; Kopia if already used | Report and restore-drill planning | A snapshot/check alone does not prove recovery |
| Similar media | Czkawka, targeted ExifTool/ffprobe | Optional report-only workflow | No perceptual-match deletion; native versions, cache effects and hydration need review |
| Trash/archive | gomi, ouch/zstd | Optional separately qualified workflow | No generic undo or metadata-preservation guarantee |
| Lint | rmlint | Optional JSON inspection | Never execute its generated shell file |
| Organization | Constrained rule validator | Literal proposals only | Never run arbitrary `organize sim` or `organize run` |

Do not install this entire table. Discovery is safe and does not execute the tools:

```bash
python scripts/storage-audit.py tools
```

When the user requests an installation, give the appropriate upstream/package
manager command for that selected tool and verify the installed version. Keep
Mole's GPL-3.0 implementation external; no Mole source or policy is vendored.

## Bundled Observation CLI

Commands below run from the skill directory. Imports read an existing report and
never launch the source tool:

```bash
python scripts/storage-audit.py observe mole analyze --version 1.73.0 --input mole.json
python scripts/storage-audit.py observe fclones group --version 0.35.0 --input duplicates.json
python scripts/storage-audit.py observe f2 preview --version 2.2.2 --input renames.json
python scripts/storage-audit.py observe dust tree --version 1.2.7 --input tree.json
python scripts/storage-audit.py observe rclone lsjson --version 1.76.0 --input remote.json
```

Fixed live observation commands require selecting `--execute`:

```bash
python scripts/storage-audit.py observe mole analyze --execute --path "$HOME/Downloads"
python scripts/storage-audit.py observe mole status --execute
python scripts/storage-audit.py observe mole history --execute --limit 20
python scripts/storage-audit.py observe rclone lsjson --execute --path 'configured-remote:folder'
```

These commands capture an executable/version receipt before observing. Unknown
versions fail before the observation. They use literal argv with no shell,
combined stdout/stderr limits, process-group timeouts, and no arbitrary flags.
Mole analyze requires an explicit local directory and never defaults to the
whole-Mac overview. rclone uses only an existing configured remote; it can use
credentials and refresh provider tokens. Local caches/logs/build state may be
written by upstream tools. These effects are declared in the registry and are
separate from mutation of observed source files.

Imported or native tool output is untrusted evidence. A tool exit code of zero
does not prove complete coverage; parsed coverage is retained. Tool stderr is
not copied into public reports. Mole status process commands and host/network
identity are not imported. Mole history is bounded supplementary history, not a
Files Buddy manifest or authorization to undo anything.

## Correct Command and Parser Contracts

### fd

The first positional argument is the pattern; subsequent arguments are roots:

```bash
fd -0 -t f --size +1g . "$scope"
```

fd ignores hidden and ignored paths by default. Select `--hidden` and
`--no-ignore` deliberately and record that choice. Never pass execution flags
or pipe results into mutation. `fd -t d -e ''` is not an empty-directory test.
Use metadata enumeration with explicit permission-error handling for emptiness.

### Mole V1.73.0

`mo analyze --json <path>` emits one object with `scan_status`, `path`,
`overview`, `total_size`, optional `total_files`, and `entries`. Entry fields
include `scan_status`, `name`, `path`, `size`, `is_dir`, and optional `cleanable`.
`partial` sizes are lower bounds; `unavailable` sizes become null. `cleanable`
is an upstream classification hint, never approval or verified savings.

`mo clean --dry-run` writes a cleanup-list file. Actual cleanup rescans, so the
preview is not an immutable action mapping. Clean, purge, and installer flows
can permanently remove files, and clean can empty Trash. They are outside the
bundled execution adapter. Source status and history have their own parsers;
they do not become verified reclaim measurements.

### fclones 0.35.0

The JSON root has `header` and `groups`. Statistics live in `header.stats`:
`group_count`, `total_file_count`, `total_file_size`, `redundant_file_count`,
`redundant_file_size`, `missing_file_count`, and `missing_file_size`. Stats may
be null. Each group has numeric `file_len`, `file_hash`, and **string paths** in
`files`. There is no `groups[].files[].path` field in this tagged contract.

A manual `fclones group --format json <reviewed-local-scope>` reads content.
Avoid broad/cloud scopes; hashing placeholders can download them. Do not use
transform/exec options. Importing the result does not select a keeper, validate
metadata/dependencies, or authorize mutations. The parser never relabels an
unspecified fclones hash algorithm as BLAKE3 or SHA-256.

### dust 1.2.7

`dust -j <scope>` emits **one DisplayNode root**, not an array. Each node has
`name`, a formatted string `size`, and `children`. Values such as `"1.0G"` are
rounded display data. The adapter preserves `size_display` and sets raw bytes
to null. Use the bounded metadata inventory for byte totals.

### F2 2.2.2 and rclone 1.76.0

F2 `--json` previews contain `base_dir`, `target_dir`, `source`, `target`,
`status`, and `is_dir`. Conflicting/overwriting/unknown status rows remain blocked
for planning. Resolve relative paths, check case/Unicode collisions, and freeze
exact mappings before creating an executor plan. See `rename-patterns.md`.

rclone `lsjson` rows contain `Path`, `Name`, `Size`, `ModTime`, `IsDir`, and
optional provider IDs. Unknown size `-1` becomes null. Listing metadata does not
prove content identity or sync completion. The live adapter omits `--hash` and
`--recursive`; broader scopes and content verification are separate decisions.

## Safe Rules and Optional Workflows

Validate organization proposals before any external simulation. `organize sim`
can run a shell action configured with `run_in_simulation: true`. The bundled
validator rejects shell/Python/custom actions, deletion, custom filters,
expression templates, traversal, extra locations, and symlink destinations.
It returns proposals and never launches organize:

```bash
python scripts/storage-audit.py validate-rules rules.yml --root "$HOME/Downloads"
```

Czkawka may exit 11 when findings exist; that is a version-specific outcome,
not a generic process failure. It writes caches, and video review needs ffmpeg.
No Czkawka subprocess adapter is claimed in this release. ExifTool/ffprobe
content reads, restic restore drills, gomi restore receipts, and archive metadata
fidelity require separately reviewed commands and native evidence.

## Provenance and Upgrades

Synthetic minimal fixtures and provenance live in `tests/fixtures/tools/`.
They derive from primary tagged contracts and do not represent native runs:

- [Mole macOS reference V1.73.0](https://github.com/tw93/Mole/blob/V1.73.0/skills/mole/references/macos.md)
- [fclones serializer 0.35.0](https://github.com/pkolaczk/fclones/blob/v0.35.0/fclones/src/report.rs)
- [dust DisplayNode 1.2.7](https://github.com/bootandy/dust/blob/v1.2.7/src/display_node.rs)
- [F2 variables 2.2.2](https://github.com/ayoisaiah/f2/blob/v2.2.2/replace/variables/variable_regex.go)
- [rclone lsjson](https://rclone.org/commands/rclone_lsjson/)

For an upgrade: inspect the new primary contract, add labelled fixtures and
negative cases, update the registry version, verify its argv and auxiliary
effects, then run the behavioral suite. Do not silently accept any new version
because its version string looks compatible.
