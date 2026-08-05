# Acceptance matrix — seven-session residual (v9 execute)

Updated: 2026-08-01T14:22:04.022618+00:00

| ID | Pass criterion | Status | Evidence |
| --- | --- | --- | --- |
| S1 | R002 assure | PASS | receipts/assure/R002-s1.json |
| S2 code zero-set | store_missing=0, projection_blocked=0, projection_ensure=0 | **PASS** | baseline/cursor-sync-final-summary.json |
| S2 skipped | disposition L092 | ACCOUNTED | dispositions/approved.json (11 remove / 1 keep; no auto uninstall) |
| S2 unresolved | quarantine filter non-blocking | ACCOUNTED | C012 receipt |
| S3 | apply-gate no | PASS | R003 |
| S4 | gstack absent | PASS | R004 |
| S5 | trailer deny + attr flags false | **PASS** | A021 + cli-config |
| S6 | canaries + dirty map | **PASS** | U011-canaries.json |
| S7 | plannotator 6×6 | PASS | R005 |
| PORT | validate + tests | SEE CV | receipts/cv/ |

## Code bucket final counts

```json
{
  "store_missing": 0,
  "projection_blocked": 0,
  "projection_ensure": 0,
  "skipped": 12,
  "unresolved": 145,
  "already_present": 1613
}
```
