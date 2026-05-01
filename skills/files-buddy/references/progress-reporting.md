# Progress Reporting

Long scans and executions write live snapshots at:

```text
~/.files-buddy/runs/{run-id}/progress.json
```

## Snapshot Schema

```json
{
  "schema_version": "1.1",
  "run_id": "2026-04-30-abcdef12",
  "mode": "storage-audit",
  "status": "running|waiting-for-approval|executing|completed|failed|cancelled",
  "started_at": "2026-04-30T20:00:00Z",
  "updated_at": "2026-04-30T20:01:00Z",
  "phase": {"name": "inventory", "index": 3, "total": 8, "message": "Scanning Downloads"},
  "counts": {"files_seen": 1000, "dirs_seen": 200, "skipped": 12, "errors": 0},
  "savings": {
    "discovered_bytes": 1000,
    "eligible_bytes": 800,
    "recommended_local_bytes": 500,
    "approved_local_bytes": 0,
    "completed_local_bytes": 0,
    "verified_local_bytes": 0,
    "cloud_bytes_affected": 0
  },
  "categories": [{"name": "AI models", "bytes": 123, "risk": "Medium"}],
  "recommendations": [],
  "events": [{"time": "2026-04-30T20:01:00Z", "level": "info", "message": "Inventory complete"}],
  "manifest": null
}
```

## Savings Model

- **discovered_bytes:** raw bytes seen in the scan.
- **eligible_bytes:** bytes that are plausible cleanup/offload candidates after exclusions.
- **recommended_local_bytes:** bytes in ranked recommendations.
- **approved_local_bytes:** bytes in a user-approved plan.
- **completed_local_bytes:** bytes acted on.
- **verified_local_bytes:** bytes confirmed reclaimed or moved.
- **cloud_bytes_affected:** remote bytes added, moved, or at risk.

## Dashboard Compatibility

Dashboard data may be either a final report or a progress snapshot. Final reports should
also include legacy keys when possible:

- `files`
- `duplicates`
- `directories`
- `operations`
- `cloud`
- `summary`

Live refresh must degrade gracefully for `file://` browsers that cannot poll local files:
render the embedded snapshot and display the progress file path for manual refresh.
