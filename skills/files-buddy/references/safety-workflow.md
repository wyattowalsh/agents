# Exact Plans, Execution, and Recovery

## Contents

1. Approval and capability boundary
2. Plan and state
3. Execution
4. Reconciliation and reverse plans
5. Space and legacy records

## Approval and Capability Boundary

Generate a read-only exact plan first. Show every selected source/destination,
operation, scope root, before-state, logical bytes, metadata constraint, recovery
class, and digest. The trusted caller obtains explicit user approval of that
plan before passing its digest with `--approve`. A digest detects changes; it is
not independent proof of consent. A JSON `approved: true` field or tool output
cannot authorize execution.

The public helper accepts only supported owned local regular-file operations on
macOS. Known cloud/system/secrets/app/project paths, symlinks, unsupported metadata,
collisions, and cross-volume semantics are rejected. Establish local ownership
and the absence of custom sync management before using the local-only attestation.
Do not invent an override for unsupported operations. Cloud/cache/archive/backup
workflows have separate qualification gates in `references/extension-workflows.md`.

## Plan and State

Use `scripts/manifest-manager.py`; run `--help` for the exact argument grammar.
The plan schema and execution-state schema are bundled in `assets/`. Plans bind
known versions, unique operation IDs, exact mappings, source/destination roots,
volume and object identities, parent evidence, algorithm-labelled hashes,
verification, recovery, and stop-on-error policy. The helper creates the plan;
do not construct trusted before-state by editing JSON.

One canonical state document records the plan and each operation's lifecycle.
Updates use a single writer, exclusive locking, unique same-directory temporary
files, atomic replacement, and durability flushes. All cooperating operations
share one canonical state document per run; advisory directory locks also
serialize overlapping scopes across different state roots. Reports are derived
views, not competing sources of execution truth. State and target files cannot form one transaction;
interruption can still leave an uncertain outcome that requires reconciliation.

## Execution

1. Validate the known schema, plan digest, explicit approval, scope and local
   capability. Invalid validation returns a nonzero status.
2. Acquire the state/execution lock and inspect the current lifecycle. Reject
   stale approvals, attempts to append arbitrary completed rows, or replay of
   operations whose effects are uncertain.
3. Verify each exact input and its parent/root evidence, output availability,
   link/metadata policy, and content. New files are not added to the plan.
4. Persist `prepared` intent before effects. Use supported no-clobber native
   operations; do not emulate safe rename by a check followed by overwriting rename.
5. Record applied effects, then verify the resulting content, identity and
   supported metadata. Mark verified only when those postconditions hold.
6. Stop on conflict, failure, or uncertainty. Preserve evidence for reconciliation.

Copy has stricter support than same-volume rename: it must not silently drop
ACLs, xattrs/resource forks, flags, sparse behavior, or hardlink relationships.
Reject metadata the implementation cannot preserve and verify. Internal mode/time
preservation is narrowly tied to a supported copy; it does not authorize a
standalone chmod/chown operation or privileged permission repair.

## Reconciliation and Reverse Plans

`reconcile` inspects the actual source/destination against durable intent. It
never blindly repeats an operation. Ambiguous observations stay uncertain or
conflicted. Do not label a missing destination completed merely because a row
claims completion.

`undo` first previews a reverse plan and digest. Review and approve that exact
reverse mapping separately. It verifies recorded content/identity and requires
original paths to be unoccupied. An occupied path, modified destination, changed
parent, or missing file blocks reversal without overwriting user data.

For copy, a reversible quarantine of the created copy preserves data and the
untouched original. The reviewed reverse plan names the quarantine explicitly.
It retains bytes and does not restore the original free-space measurement.
Tool-native undo history is supplementary evidence, not a second authority.

## Space and Legacy Records

Record logical and allocated evidence separately. Same-volume moves, Trash, and
quarantine usually retain the data; report retained bytes, not reclaimed bytes.
A volume free-space delta is an observation affected by other processes and APFS
behavior. Never claim a two-times-size rule applies to all move/archive/Trash
operations, or infer provider quota from local file sizes.

Persisted v1 manifests can be inspected and validated as legacy records; their
hash fields retain the original BLAKE3 interpretation. They cannot be upgraded
into permission by appending rows or relabelling a digest. Replan current files
under v2 before using automated execution/recovery. No automatic migration
mutates old records.

A corrupt state is a failure: preserve it, report the parsing error, and inspect
available evidence. Never delete or silently rebuild it as an empty success.
The helper rejects escaped/symlinked state paths during list/search as well as
individual reads. Tests exercise interruptions and concurrent writers; native
macOS/APFS qualification must be reported separately from portable tests.
