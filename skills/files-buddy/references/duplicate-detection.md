# Duplicate Detection

Content equality is evidence for review. It does not establish that either copy
is disposable, select a keeper, or authorize a move, link, or deletion.

## Contents

1. Exact local workflow
2. External engines
3. Keeper and dependency review
4. Similar media and cloud
5. Accounting and verification

## Exact Local Workflow

First collect metadata with `storage-audit.py scan`. Then obtain explicit consent
for content reads of eligible local files:

```bash
python scripts/storage-audit.py dedupe \
  --database "$HOME/.files-buddy/runs/downloads/inventory.sqlite" \
  --read-content --max-bytes 2147483648 --max-seconds 60
```

This emits exact SHA-256 review groups only. It does not create an execution
plan or choose a keeper. Every group includes the algorithm, digest, paths,
logical candidate bytes, dependency evidence, `review_only: true`, and unknown
risk. A stable alphabetical `keeper_candidate` is a display aid; `keeper`
remains null until the user makes a choice.

Only owned regular local files with eligible metadata enter size pre-groups.
Files with the same `(device,inode)` are one object. Multi-link files, symlinks,
placeholders, known cloud paths, sparse/flagged objects, project/app-managed
stores, and sidecar families remain excluded from built-in content reads.
Zero-byte files remain inventory observations, not cleanup candidates.

Each content candidate is opened using non-following descriptors, checked
against its stored per-file fingerprint, checked for fresh ancestor/project
and companion-sidecar markers, hashed in bounded chunks, and checked again. Resume caches never rely on a parent directory timestamp. Changes or
byte/time limits produce partial coverage. Unchecked cached rows cannot make
an interrupted hash pass look complete.

## External Engines

| Tool | Role | Supported surface | Boundary |
| --- | --- | --- | --- |
| fclones 0.35.0 | Primary optional exact engine | Versioned JSON import | No remove/link/dedupe execution |
| rmlint | Filesystem lint and optional cross-check | Operator-reviewed JSON | Never execute generated shell scripts |
| Czkawka | Optional exact/media review | Operator-reviewed reports | Similarity is never deletion evidence |
| rclone | Remote object/name review | Versioned metadata listing | Names/sizes do not prove content equality |
| dupeGuru / Video Duplicate Finder | Interactive specialist review | User-selected workflow | No automated keeper/deletion policy |

A separate tool is useful when it resolves a concrete evidence gap, not merely
because another duplicate engine exists. Native commands can read content,
hydrate cloud placeholders, and write caches. Record those effects before use.

### fclones Parser

Use `header.stats`, not a top-level stats object. Current statistic names are
`group_count`, `total_file_count`, `total_file_size`, `redundant_file_count`,
`redundant_file_size`, `missing_file_count`, and `missing_file_size`. Null stats
mean incomplete evidence. Groups have `file_len`, `file_hash`, and an array of
string paths in `files`. See the tagged serializer in `tool-integrations.md`.

An imported fclones hash retains an unspecified upstream algorithm label unless
the recorded command proves which algorithm was used. Before mutation, the
common executor must collect its own supported algorithm-labelled evidence.
Do not reinterpret historical BLAKE3 values as SHA-256.

## Keeper and Dependency Review

For each exact group:

1. Confirm content and stable object identity independently of path names.
2. Identify canonical project/app ownership, sidecars, metadata, permissions,
   cloud provider IDs, and active references. Similar names are only hints.
3. Preserve Git projects, DAW/Logic bundles, sample libraries, model stores, and
   app-managed libraries as dependency units.
4. Ask the user to select a keeper when intended canonical location is unclear.
5. Build exact source/destination mappings only for selected eligible files.
6. Preview collisions, repercussions, retained bytes, and the supported restore
   path. Require approval bound to that plan's digest before execution.

Do not normalize or rewrite filesystem paths merely for display. NFC/NFD or
case-folded text can help flag a potential collision, but the original path
bytes/strings remain the operation identity. Files on separate devices can
share inode numbers; compare both device and inode.

## Similar Media and Cloud

Czkawka image/video/music, dupeGuru, and similar tools produce review queues.
Separate them from exact groups in every table and report. Never include their
potential savings in exact duplicate totals or auto-trash a perceptual match.
Metadata enrichment via ExifTool/ffprobe is opt-in and scoped to selected local
materialized files; it may read content. Preserve originals and associated
sidecars. Czkawka cache writes, exit-11 findings behavior, and ffmpeg video
requirements are version-specific and need native qualification.

For cloud paths, start with metadata-only listing. Hashing/copying a placeholder
can download it. Materialization needs a separate decision explaining network
and local-space cost. Distinguish equal names, equal sizes, provider hash
comparisons, local content equality, and provider sync completion. None are
interchangeable. Unknown provider state stays report-only.

## Accounting and Verification

`candidate_bytes` means logical bytes in possible redundant copies, before keeper
selection and dependency checks. It is not physical APFS reclaimability.
`verified_reclaimed_bytes` remains unknown unless a qualified workflow supplies
actual evidence. Quarantine and Trash retain storage; cloud quota and local
bytes are separate metrics.

Lint findings such as empty files/directories and broken links are separate
review classes. Empty objects may be intentional sentinels or placeholders.
No finding is piped into deletion, and no external preview replaces the exact
approved mapping, fresh object checks, and manifest-backed recovery contract.
