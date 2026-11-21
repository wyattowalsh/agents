# Specialized Workflows and Qualification

## Contents

1. Capability gates
2. Caches and app-owned data
3. Archive and backup
4. Media and watchers
5. Native acceptance matrix

## Capability Gates

The local executor accepts an intentionally narrow operation set. These workflows
can produce useful observations and plans without claiming unqualified mutation
support. Never route a rejected cloud/cache/archive operation through a shell or
native tool as an automatic fallback.

| Family | Current useful surface | Required before mutation support |
| --- | --- | --- |
| Cloud | Metadata observations, provider/mode/identity review, offload plan | Exact per-object provider contract, sync state, hydration consent, postconditions and recovery |
| Caches | Owner/dependency inventory and regeneration explanation | Owner-native bounded command, exact effect scope, active-use checks, separate approval |
| Archive | Destination/format/metadata/restore plan | Supported native metadata preservation, staged output verification and restore drill |
| Backup | Existing-destination review and verification checklist | Configured destination, approved transfer, credential handling outside reports, demonstrated restore |
| Media | Explicit local-content metadata/similarity review | Version-qualified tool, bounded reads, safe parsing, no similarity-driven deletion |
| Watch | Finite metadata observation and proposal generation | No automatic mutations in this version |

## Caches and App-Owned Data

Use the storage map to identify package managers, Xcode, containers, model stores,
VM disks, snapshots, and app libraries. Record ownership, lockfiles/refs, active
use, shared links, offline needs, source availability, and regeneration costs.
Unknown dependency evidence is a review state. Old timestamps, ignored paths,
Mole `cleanable` flags, and duplicate hashes do not prove disposability.

`docker system df`, owner-native listings, and Mole observations can establish
usage, but not the exact objects a future prune will affect. Rebuild is
regeneration, not undo; named volumes, unique model quantizations, VM snapshots,
Xcode archives, and backups may contain irreplaceable data. Do not issue blanket
prune or Mole clean/purge/slim commands under a storage-audit request.

## Archive and Backup

Use an existing, explicitly chosen destination. restic is the preferred optional
backup candidate; Kopia is an alternative when already in use. Do not install
both or initialize repositories/credentials implicitly. rclone transfers data;
remote presence alone is not a versioned independent recovery guarantee.

For an archive/backup plan:

1. Enumerate exact source objects, hardlink/symlink relationships, ACLs, xattrs,
   resource forks, flags, timestamps, sparse files, and app ownership.
2. Select a format and native tool only when that metadata has a supported round
   trip. `ouch`/zstd are compression helpers, not blanket Mac metadata assurance.
3. Name a nonexisting staging/output destination and budget space. Preserve all
   sources while creating/verifying the output through a separately approved workflow.
4. Verify inventory/content and perform a bounded restore to a new location.
   Compare supported metadata, links, content and names. A readable archive list
   or successful process exit is not a restore drill.
5. Record backup/snapshot/object IDs, verifier versions, exclusions, and failures
   without credentials. Authorize source release only as a distinct plan afterward.

Do not automate source release for an archive/backup family until these gates
have native acceptance evidence. The operation remains report-only otherwise.

## Media and Watchers

ExifTool and ffprobe are optional metadata observers. Open only explicitly
approved local files; provider placeholders and app-owned libraries stay excluded.
Keep tool versions, format errors, output bounds, and content-read effects visible.
Czkawka similarity groups are human review queues, not exact-duplicate authority.
Preserve sidecars, photo/video pairs, DAW sessions, sample libraries and model assets.

Watch mode is finite and observation-only: declare roots, interval, scan/file
budgets, output state, and stop behavior. Emit candidates only after files settle.
Do not start a persistent `watchexec`, `pueue`, launchd, or organize daemon. A prior
simulation cannot authorize future files. Future automatic execution would need
an explicit expiring/revocable standing policy and the same exact-plan executor;
that policy is not implemented by a generic “yes, watch this folder”.

## Native Acceptance Matrix

| Area | Evidence needed beyond portable fixtures |
| --- | --- |
| APFS | Case-sensitive/insensitive and Unicode collisions, same-volume no-clobber, interruption, clones/snapshots/free-space limits |
| Metadata | ACL/resource-fork/xattr/flag/sparse/hardlink round trips or explicit rejection |
| Permissions | Owned/unowned objects, TCC-denied reads, unreadable parents, unavailable/remounted volumes |
| Provider | Pending upload, online-only and pinned items, offline/network failure, custom roots and remote IDs |
| Restore | Occupied originals, modified outputs, moved parents, partial copy/archive, quarantine collisions |
| Tools | Actual supported binary/version, parser shape, exit codes, auxiliary writes, cancellation and bounds |
| User interface | Responsive, keyboard/focus, long/empty/error state, reduced motion, and refreshed-data validation |

Record which cases ran. Linux unit tests, parser fixtures, static scores, and
schema-valid language evals cannot substitute for these native tests. Narrow the
supported capability or hand off when evidence is unavailable.
