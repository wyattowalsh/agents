# Design: External Repo Intake

## Intake Model

The lane normalizes the 93-record source ledger into committed planning manifests that downstream lanes can consume without depending on untracked planning scratch space.

Each repository receives:

- a stable `EXT-*` identifier and GitHub URL
- source domain, cluster, and recommended next step
- a target downstream lane for clean-room follow-up
- a discovery-only intake status
- seven required review gates before install, vendoring, execution, or promotion

## Review Gates

Every repo has pending tasks for source verification, license review, maintainer/activity review, executable-surface review, security/provenance review, conformance-fixture review, and rollback/docs sync review.

These tasks deliberately separate research input from adoption. A repo can be an adopt or wrap candidate only after all gates have evidence.

## Quarantine Handoff

Repos with credential proxy, auth bridge, account-sharing, or offensive-security risk remain denied-by-default. C10 writes a handoff manifest for C15 and routes those records to `security-quarantine` while leaving final policy ownership with C15.

## Reconciliation

The committed source ledger is treated as the current URL set because no separate pasted URL artifact exists in this repo. The reconciliation manifest records duplicate checks, contiguous ID checks, and empty additions/removals for this pass.
