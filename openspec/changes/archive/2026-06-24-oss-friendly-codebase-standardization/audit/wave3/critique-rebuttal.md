# Wave 3 Critique & Rebuttal Summary

Generated: 2026-06-15

## Critique protocol
Four critic lenses applied to register-v1 (138 findings):
1. **Evidence critic**: Require file:line or command output
2. **Severity critic**: Challenge P0 inflation
3. **Dedup critic**: Merge path-leak cluster
4. **Actionability critic**: Drop vague recommendations

## Outcomes
- **Dropped** (confidence <6): 0 findings
- **Merged theme**: path-portability-cluster (P0-001, W1-005, W1-T-05, W2-DX-01, W2-SEC-01, W1-HARNESS-B-001)
- **Downgraded**: W1-HARNESS-B-021 (experimental), W1-T-14 (minor DX)
- **Strength findings retained**: W1-ASSETS-DOCS-001..004, W2-COMP-001..003, 007..009

## Rebuttals (selected)

| Finding | Critique | Rebuttal | Verdict |
|---------|----------|----------|---------|
| P0-002 zero validated tiers | "Intentional conservative posture" | Registry explicitly requires fixtures; public docs must say plan-only | **Accept P0** for OSS honesty |
| W2-COMP-004 MCPHub complexity | "Feature not bug" | Strangers need opt-in; default docs should not require MCPHub | **Accept P1** |
| W1-003 Codex stub | "Sync script works" | Adapter contract + testability require implementation | **Accept P0** |
| W2-SEC-04 quarantine not enforced | "Planning artifact" | Register referenced in tests but not sync — gap confirmed | **Accept P1** |

## register-v2.json
See `findings/merged/register-v2.json` — 138 accepted findings, median confidence 8.
