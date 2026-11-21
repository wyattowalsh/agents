# Protected Paths and Scope

## Contents

1. Scope and normalization
2. Hard exclusions
3. Review-only surfaces
4. Concurrent changes

## Scope and Normalization

An execution plan has separate exact source and destination roots. Normalize
absolute paths and use path-component containment, never string prefixes.
`/` is rejected as an execution root by exact equality. It is not a subtree rule:
otherwise every absolute path would be rejected. System-directory exclusions
below apply to the named directory and its descendants.

Reject symlink components, dangling links, special files, unsupported mounts,
unknown identities, and traversal outside the approved roots. Checking only the
resolved final string is insufficient: a symlink or parent can change afterward.
Record root and parent device/inode identities and recheck them at operation time.

Read-only all-local inventory enumerates named storage surfaces with exclusions.
It never authorizes a recursive mutation of the filesystem root or home folder.
The scanner may report an excluded app/cloud/project boundary without traversing
its internals. A skipped directory is not an empty directory.

## Hard Exclusions

Local execution rejects macOS system trees such as `/System`, `/Library`, `/usr`,
`/bin`, `/sbin`, `/etc`, `/var`, `/private`, and `/Applications`, plus device,
process, and other special system namespaces on fixture platforms. Do not offer
an override for these exclusions. User Library is a distinct path, but much of
it is app-managed and remains report-only.

Always exclude `.git` internals, including worktree `.git` files and submodule
metadata. Preserve `.gitignore`, `.gitmodules`, lockfiles, and project structure.
The bounded local executor does not flatten repositories or transfer project
files based merely on their extension or ignore status.

## Review-Only Surfaces

| Surface | Reason | Supported response |
| --- | --- | --- |
| `.ssh`, `.gnupg`, `.aws`, `.kube`, `.config`, keyrings, `.env` | Secrets or application configuration | Explain scope and hand off; no generic executor override |
| Cloud roots and user-declared sync folders | Namespace changes may propagate remotely | Provider review and native handoff |
| Photos, Music, TV, Mail, Messages and application libraries | Database/index relationships | App-native cleanup only |
| Time Machine/backups, VM disks/snapshots | Recovery chains or unique data | Inventory/owner-native review |
| Git, application, DAW and sample-library bundles | References and aggregate ownership | Preserve the boundary and plan at the owning system |
| Shared package/model caches | Referrers, offline use, regeneration cost | Owner evidence and separate specialized qualification |

Explicitly naming a sensitive path can authorize its review. It does not bypass
a capability the executor intentionally does not implement. Do not promise a
universal “yes” override that the helper cannot enforce safely.

## Concurrent Changes

A plan covers exact mapped files, not a directory count or wildcard. New files
remain untouched. Changed content, identity, link count, mode, timestamps, parents,
or destinations block the affected operation. Case/Unicode name equivalence and
actual no-clobber filesystem behavior must both be considered.

Cooperative state and directory-identity locks serialize helpers with overlapping
scopes, including different state roots. They do not lock out other applications
or hostile writers. Fresh checks, anchored path
operations, no-clobber primitives, and explicit uncertain outcomes are still
required. After an uncertain result, inspect/reconcile instead of retrying it.
