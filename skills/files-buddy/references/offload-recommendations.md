# Offload Recommendations

## Contents

1. Eligibility and ranking
2. Provider handling
3. Recommendation fields
4. Stop conditions

## Eligibility and Ranking

Plan local storage release while preserving a verified recoverable copy. Evaluate
eligibility before ranking bytes. Exclude app-managed packages, active projects,
unsynced content, unknown owners, unsupported provider state, and unique data
without independent recovery evidence.

Rank eligible candidates by evidenced allocated storage, user-selected coldness,
restore friction, remote quota, and offline requirements. Do not manufacture
0–5 importance scores or rebuild/download times from filenames. Unknown quota,
allocated size, or ownership remains unknown and produces a review recommendation.

## Provider Handling

| Provider/workflow | Evidence needed | Action boundary |
| --- | --- | --- |
| iCloud Drive | Provider state for the exact file, uploaded content, local residency, offline needs | Review Finder Remove Download; no generic CLI eviction |
| Google Drive Stream | Confirmed Stream setting, object identity, upload and residency state | Provider-native local release after approval |
| Google Drive Mirror | Confirmed Mirror setting and intended local retention | Explain settings/native workflow; do not delete mirrored paths to offload |
| rclone copy | Explicit remote, object mapping, supported hashes, transfer/restore evidence | Copy and verify separately from any later local source release |
| Backup destination | Existing configured destination, successful backup and restore drill | Recovery evidence; backup creation alone does not authorize source release |

Inspect `references/cloud-drives.md` for namespace effects. A move out of a synced
root can propagate deletion; local staging does not make it safe. Copying or
hashing a placeholder can download it. Report the expected hydration and space
cost before requesting content-read approval.

## Recommendation Fields

Use the report contract's canonical `local_bytes` and `cloud_bytes`
fields in recommendation rows. `local_bytes` is the candidate estimate, never
verified reclaimed space. Use null for unknowns; include evidence and limits.

```json
{
  "action": "review",
  "provider": "icloud",
  "path": "~/Documents/example.dat",
  "local_bytes": null,
  "cloud_bytes": null,
  "risk": "Unknown",
  "prerequisites": ["Confirm exact object upload and residency state"],
  "verification": ["Provider-native per-object evidence required"],
  "repercussions": ["Later access may require download; offline access changes"],
  "restore_path": null,
  "recovery_class": "unknown"
}
```

Only a supported, verified operation supplies completed/verified metrics. A
provider's displayed logical file size is not automatically reclaimable space.

## Stop Conditions

Stop at review/native handoff when upload state, provider semantics, quota,
materialization, exact remote identity, or restore capability is unknown.
Size-only `rclone check` success is not content equality. A synced remote is not
necessarily an independent backup. Preserve sources until the user separately
approves a qualified source-release plan with recovery evidence.

Sources: [Apple iCloud management](https://support.apple.com/en-ie/guide/mac-help/mchl1a02d711/27/mac/27),
[Google Drive modes](https://support.google.com/drive/answer/13401938?hl=en),
[rclone verification](https://rclone.org/commands/rclone_check/).
