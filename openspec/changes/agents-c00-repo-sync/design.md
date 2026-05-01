# Design

## Decision

Complete the repo-sync foundation as an auditable inventory and drift-ledger contract. The lane classifies repo-owned, generated, merged, symlinked, live, and experimental surfaces so downstream lanes can reason about ownership before they mutate files.

## Rationale

The platform overhaul spans repo files, generated artifacts, and user-owned live configuration. A shared inventory prevents later lanes from guessing which files are canonical, which are derived, and which require path-only or redacted handling.

## Implementation Notes

- `planning/manifests/repo-sync-inventory.json` records managed paths, ownership class, source tier, drift policy, validation evidence, and secret posture.
- `planning/manifests/repo-drift-ledger.json` records observed drift state and next action without resolving unrelated dirty work.
- `planning/00-overview/12-repo-sync-and-drift-ledger.md` explains promotion rules and the validation expectations for downstream lanes.

## Risks

- The worktree includes unrelated dirty changes, so this lane must use explicit pathspecs and avoid broad staging.
- Live user config and credential-bearing surfaces are intentionally represented by metadata only.
- Foundation artifacts do not validate harness behavior by themselves; child lanes must add fixtures before raising support tiers.
