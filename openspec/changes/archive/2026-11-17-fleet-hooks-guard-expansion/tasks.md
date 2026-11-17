# Tasks

## G0 — Prep

- [x] T-000a proposal.md
- [x] T-000b design.md
- [x] T-000c tasks.md
- [x] T-001a agents-*.json audit in design.md
- [x] T-001b dual fix strategy in design.md

## G1 — P1 deny wiring

- [x] T-010a opencode `_deny`
- [x] T-010b grok-build `_deny`
- [x] T-010c `_stop_retry` grok + opencode
- [x] T-011a `before-read-file-guard` alias
- [x] T-012a bridge POLICY_MAP fix
- [x] T-020–T-024 P1 tests

## G2 — P2

- [x] T-030 ENFORCE_POLICY_IDS fail-closed
- [x] T-040 OpenSpec parity close-out + deny-transport spec
- [x] T-042 deny matrix tests

## G3 — P3 hygiene

- [x] T-050 agents-*.json + apm.lock
- [x] T-051 shell layering docs
- [x] T-052 convert lossy docs + test

## G4 — Validate

- [x] T-060 pytest + wagents validate + sync check

## G5 — Completion wave (v4)

- [x] C-010 RV-004 shell guard fail-closed on dangerous git when module missing
- [x] C-020 T-011b allow-path matrix (opencode/grok read + bash)
- [x] C-030 parity tasks verify-then-checkoff — see [`fleet-hooks-parity/tasks.md`](../fleet-hooks-parity/tasks.md)
