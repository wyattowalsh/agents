# Change: Files Buddy evidence-bound storage workflows

## Why

The 2026-11-20 review of `skills/files-buddy` at `99a5692a` reproduced fifteen
contract, execution-state, reporting, tool-recipe, and packaging defects. The
maintainer approved implementing the enhancement plan and pushing to `main`.

## What Changes

- Correct cloud, approval, recovery, protected-path, and capability guidance.
- Add versioned report, plan, and tool-observation contracts with explicit unknowns.
- Implement bounded metadata inventory and dependency-aware duplicate review.
- Integrate Mole observation commands and qualified OSS parsers without importing
  third-party skill policy or delegating mutation authority to a tool preview.
- Harden the manifest ledger and add narrow exact-map local execution, durable
  intent, interruption reconciliation, and verified reverse plans.
- Make the offline dashboard truthful, validated, accessible, and refreshable.
- Fix standalone packaging, declare dependencies, add executable regression
  coverage, and regenerate the skill's published documentation.

## Non-Goals

No cleanup of the maintainer's files, tool installation into their Mac, live
skill sync, cloud account changes, automatic cache pruning, or background daemon
installation. Provider, archive, backup, and media workflows remain report-only
where their native acceptance evidence is unavailable. Native qualification
cannot be inferred from Linux tests.
