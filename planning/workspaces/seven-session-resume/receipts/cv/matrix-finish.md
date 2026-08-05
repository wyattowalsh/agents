# Acceptance matrix — full finish (v11 residual)

Updated: 2026-08-04 (v11 closeout)

| ID | Pass criterion | Status | Evidence |
| --- | --- | --- | --- |
| S1 | R002 assure | **PASS** | receipts/assure/R002-s1.json |
| S2 code zero-set | store_missing=0, projection_blocked=0, projection_ensure=0 | **PASS** | baseline/cursor-sync-finish.json + V011 |
| S2 L092 home uninstall | 10 remove targets gone; frontend-designer keep | **PASS** | H012-uninstall.json; live on-disk absent |
| S2 skipped inventory | disposition + on-disk authority | **ACCOUNTED** | dry-run skipped=10 (catalog residual incl. keep + opsx:tdd + removed names not on disk); see V011 note |
| S2 unresolved | quarantine filter non-blocking (145) | **ACCOUNTED** | C012 + matrix note — no mass delete |
| S3 | apply-gate no | **PASS** | R003 |
| S4 | gstack absent | **PASS** | R004 |
| S5 | trailer deny + attr flags false | **PASS** | A021 + cli-config |
| S6 | canaries + dirty map (light) | **PASS** | U011-canaries.json |
| S7 skills 6×6 | core+extras present; Tot not installed | **PASS** | W001-plannotator-6x.json |
| S7 hook | improve-context injects | **PASS** | W002-hook.json |
| S7 R006 AGENTS | compound + hook + Tot ref-only documented | **PASS** | AGENTS.md §6 table; R006-s7-agents.json CLOSED |
| T-FLAKE | apply JSON partial-failure test | **PASS** | T014-flake.json; hybrid structured capture |
| Docs/validate | generate --no-installed + readme + validate | **PASS** | D013-docs.json |
| P020 compound full HTML | optional | **SKIP** | P020-skip.json (hook already good) |
| Commits | user-gated | **PENDING user** | not run unless user says commit |

## Code bucket finish counts (Cursor dry-run)

```json
{
  "store_missing": 0,
  "projection_blocked": 0,
  "projection_ensure": 0,
  "skipped": 10,
  "unresolved": 145,
  "already_present": 1613
}
```

## Definition of Done checklist

1. [x] T-FLAKE green  
2. [x] Code buckets zero  
3. [x] L092 remove set absent on disk; keep intact  
4. [x] Unresolved 145 quarantine residual documented  
5. [x] R006 AGENTS closed  
6. [x] Docs generate + readme + validate  
7. [x] Plannotator 6×6 + hook (prior W001/W002)  
8. [x] matrix-finish + ledger CLOSED stamp  
9. [x] P020 SKIP  
10. [ ] Commits — **ask user**  

**Verdict:** implementation + assurance **FINISHED**. Working-tree ship ready. **Commits only on explicit user request.**
