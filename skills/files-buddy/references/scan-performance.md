# Scan Performance

Use a bounded, metadata-first inventory. A cached scan is observation evidence;
it never substitutes for fresh executor preconditions or grants approval.

## Contents

1. Portable inventory
2. Resume semantics
3. Classification and scope
4. Budgets and accounting
5. Native qualification

## Portable Inventory

Run from the skill directory with the SQLite database outside the source tree:

```bash
python scripts/storage-audit.py scan "$HOME/Downloads" \
  --database "$HOME/.files-buddy/runs/downloads/inventory.sqlite" \
  --output "$HOME/.files-buddy/runs/downloads/report-1.json"
```

The scanner uses stat metadata and descriptor-based, non-following traversal.
It does not read file contents, run `file`, calculate hashes, invoke external
scanners, or open media. Filenames remain structured strings, including names
with spaces, newlines, Unicode, or leading dashes. The output is a report v2
snapshot with capped rows and complete aggregate counts for the observed set.

Inventory databases and report outputs must stay outside the observed tree.
Artifact paths reject parent traversal (`..`) and symlink components; database
files and SQLite sidecars must be owned, regular files with one hardlink.
Containment also checks existing directory identities to catch alternate case
spellings on macOS. Reports use exclusive creation through a non-following
parent handle. A relocated database is checked against its stored scan scope
before duplicate review opens a writer. SQLite still uses pathname-based file
opening; this is not isolation from concurrent, noncooperating same-user path
replacement. Keep observation state in a private, stable directory.

Explicit policies are recorded in the report and pinned in the database:

- Hidden files are excluded unless `--include-hidden` is selected.
- `.git` internals remain excluded. Gitignore patterns are not interpreted;
  project files are classified for ownership review, not discarded as ignored.
- `--exclude` takes repeatable relative-path glob patterns.
- Symlinks and special files are reported, never followed or hashed.
- Mounted descendants are not entered without `--cross-filesystems`.
- Add known nonstandard provider roots with repeatable `--cloud-root`.
- App-managed bundles and protected credential stores are not traversed.

`all-local` remains an orchestration mode that enumerates explicit audit roots.
The scanner deliberately rejects `/` as a scope. Aggregate separate root reports
without counting overlapping trees twice.

## Resume Semantics

```bash
python scripts/storage-audit.py scan "$HOME/Downloads" \
  --database "$HOME/.files-buddy/runs/downloads/inventory.sqlite" --resume \
  --max-entries 100000 --max-seconds 60
```

Resume requires the same root device/inode identity and exclusion policy. Every
encountered file is re-statted. File fingerprints include device, inode, kind/
mode, owner, size, modification/change timestamps, link count, and flags.
Directory mtime is **never** used to skip validation of descendants.

The entry budget counts new or changed objects. Previously observed unchanged
objects are re-statted without spending that entry budget, allowing repeated
bounded passes to advance through a stable tree. The whole pass still has a
time limit; increase that explicit budget if revalidation alone reaches it.
A report includes only rows observed during its current pass. On a complete
pass, missing old entries are removed from the cache. Partial passes retain
unseen rows internally for subsequent revalidation, but do not present them
as current observations.

SQLite commits the completed or budget-limited pass atomically. Abrupt process
termination rolls back that in-progress pass; resume starts from the previous
committed observation checkpoint. This is not a filesystem snapshot or a
promise of progress after every individual file.

Hashes are cached only against per-file fingerprints. Duplicate review checks
the actual opened object again before using a cached hash, and verifies the
fingerprint again after a new content read. A changed descendant invalidates
its hash even when its parent's modification time remains unchanged.

## Classification and Scope

Keep dependency classes visible: user files, projects, known cloud roots,
protected stores, app-managed packages, caches, models, VMs, archives, and
sidecars. Projects are detected by metadata markers such as `.git`,
`pyproject.toml`, `package.json`, `Cargo.toml`, and `go.mod`. Package directories
such as Photos libraries, Logic projects, and VM bundles remain intact.

Known cloud roots, `.icloud` names, filesystem flags, sparse/compressed
allocation, non-owned objects, hardlinks, projects, `.env` variants, credential
stores, application data under Library, managed model/package stores, and
sidecar families are ineligible for built-in content hashing. Provider detection
uses known path
conventions, supplied cloud roots, and available flags. Policy comparisons
conservatively case-fold known components and supplied cloud roots, including
on case-sensitive volumes, while retaining the original filesystem paths in
reports. Unknown third-party sync bindings cannot be inferred reliably;
supply their roots and use an
operator/provider handoff when residency is uncertain.

Cached candidate paths are untrusted. Duplicate review rejects noncanonical,
relative, escaping, or parent-traversing paths before opening content. Its fresh
descriptor walk reapplies hidden-file, exclusion, depth, mount, project, and
owner-managed-path checks even if a cached eligibility flag has changed.

Permission failures, changed directory identity, depth limits, timeouts, and
entry limits produce partial coverage with explicit omissions. A policy
exclusion is recorded separately from an I/O error. “Complete” means complete
within the declared policy and observed walk, not an atomic view of a changing
filesystem. None of these classifications means a file is disposable.

## Budgets and Accounting

Defaults are 100,000 new/changed entries, 60 seconds, depth 64, and 500 displayed
rows. Counts and aggregate accounting are queried from SQLite, not accumulated
in a full Python list. Output limits do not reduce the observed file count.
Directory rows expose no subtree byte estimate when only inode metadata is
available. Category and summary totals both de-duplicate `(device,inode)` identities.
Objects linked across multiple categories are counted once as `hardlink-shared`,
so category bytes sum to the summary logical-byte total.

Allocated bytes use available block metadata and remain estimates. APFS clones,
snapshots, compression, purgeable space, and concurrent activity prevent equating
those estimates with recoverable physical space. Moving a file to quarantine or
Trash does not establish reclaimed bytes. Keep candidate, selected, acted-on,
quarantined, Trash-retained, verified-reclaimed, and observed-free-space metrics
separate; unknown values remain null.

Built-in hashing is single-worker, size-grouped, chunked, and separately bounded
by bytes and time. It does not nest a full-core native hashing pool inside a
Python worker pool. Use optional fclones for a specifically reviewed local
content scope when its measured need justifies the extra tool.

## Native Qualification

The deterministic tests use temporary POSIX fixtures, including interruption-
style bounded resumes, stale children, hardlinks, symlink swaps, permission
errors, and row caps. They do not establish macOS File Provider residency,
TCC access, APFS physical reclaimability, or external-tool performance. Those
claims require evidence from the actual Mac and provider involved.
