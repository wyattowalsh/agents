# Cloud Drive Detection and Safety

## Contents

1. Detection and uncertainty
2. Operation semantics
3. Provider handoffs
4. Verification and content reads

## Detection and Uncertainty

| Surface | Discovery hint | Limits |
| --- | --- | --- |
| iCloud Drive | `~/Library/Mobile Documents/com~apple~CloudDocs` | Desktop/Documents may also be managed; path alone cannot prove sync completion |
| File Provider domains | `~/Library/CloudStorage/*` | Provider names, account layout, and state vary |
| Google Drive | A GoogleDrive-prefixed provider domain or configured custom root | The root does not prove Stream versus Mirror |
| Dropbox, OneDrive, Box | Known domains plus user-declared sync roots | Custom/legacy roots may not be automatically detectable |
| rclone | An explicitly selected configured remote | Do not enumerate credentials or assume a remote is a backup |

Path classification is a conservative observation, not authoritative provider
state. An unknown provider or unknown materialization/sync state means review
only. The local executor rejects known cloud paths and requires the trusted
caller to establish that its scope is local. It cannot detect every custom sync
client. Do not represent that attestation as an automated proof.

## Operation Semantics

| Operation | Local effect | Remote implication |
| --- | --- | --- |
| Provider-native Remove Download / eviction | Can release cached local content | Intended to preserve the cloud object, subject to provider state |
| Copy outside a sync root | Creates another local copy | Usually leaves the source namespace intact; copying may hydrate it |
| Move outside a sync root | Removes the path from the synced namespace | Can propagate deletion to the cloud and other devices |
| Move within a sync root | Changes its path; usually retains local data | Syncs the rename/move and can break references |
| Trash/delete a synced path | Removes the synced path | Can propagate remote deletion |
| Local quarantine | Retains bytes at another location | Does not cancel any source-side sync deletion |

A `.files-buddy-trash` directory is not a cloud safety mechanism. Outside the
sync root it does not prevent source deletion from syncing; inside it, it remains
part of that provider's namespace. Neither case establishes local bytes reclaimed.

## Provider Handoffs

### iCloud Drive

Inspect Finder's provider state and use the documented **Remove Download**
action when the user has approved local eviction of fully uploaded content.
Keep cloud deletion and eviction as distinct plans. Do not automate undocumented
`brctl` or `fileproviderctl` mutations from generic recipes: command presence is
not a qualified provider contract. A version-specific adapter would need native
fixtures for pending upload, pinned content, package bundles, offline state, and
post-action materialization before it could enter the executor.

### Google Drive Desktop

Confirm **Stream files** versus **Mirror files** using Drive settings/provider
state. Stream files can be fetched on demand; Mirror intentionally retains local
copies. Use the provider UI when local release is ambiguous. Google Drive can
have multiple remote objects with the same name, so retain remote IDs and do not
assume a path string uniquely identifies the object to keep or remove.

### rclone

Use an explicitly configured remote for bounded metadata listings. Start without
`--hash`, which may add expensive provider work or content reads. A later
operator-approved copy workflow is copy, verify, restore proof, then a separate
source-release plan. Never substitute `move`, `sync`, `delete`, or `purge` for
that sequence. Review `rclone check`'s actual hash support; size-only success does
not prove equal contents. See `references/extension-workflows.md`.

## Verification and Content Reads

1. Record provider/account identity without secrets, object IDs where available,
   root, mode, sync/materialization status, capture time, and unknowns.
2. Metadata logical size and allocated estimates are different. Do not open a
   placeholder to obtain a hash or “correct” its size without informed consent.
3. Before approved hydration, show potential download/local-space impact and
   confirm available space. Hashing, copying, media probes, and duplicate tools
   can hydrate files even when described as read-only.
4. Verify the specific copied/evicted objects. A quiet generic status command
   alone is insufficient to establish all object-level postconditions.
5. Record recoverability, offline consequences, and retention limits. A synced
   copy is not automatically an independent backup.

Sources: [Apple iCloud file management](https://support.apple.com/en-ie/guide/mac-help/mchl1a02d711/27/mac/27),
[Google Drive streaming and mirroring](https://support.google.com/drive/answer/13401938?hl=en),
[rclone check](https://rclone.org/commands/rclone_check/).
