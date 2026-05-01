# Design: Docs And Instructions Truth

## Planning-First Consolidation

C08 first defines the consolidation contract under `planning/65-docs-and-instructions/`. This keeps shared generated docs untouched until registry inputs, child fragments, and worktree conflicts are stable.

## Source Contracts

- Docs artifact registry usage defines how generated and curated docs identify owners, inputs, and freshness checks.
- AI instruction sync planning defines canonical instruction sources and bridge-file constraints.
- Generated-doc ownership planning defines which generator owns each derived output.
- Support matrix ownership defines how support tiers and harness variants project into docs.
- Truth-surface rules and blind-spot labels prevent unsupported, experimental, unverified, and quarantine surfaces from being guessed or hidden.

## Deferred Consolidation

Generated docs, shared bridge instructions, and root docs are intentionally deferred when they are dirty or forbidden by parent dispatch. The final consolidation pass must run freshness checks and stage generated outputs only when explicitly scheduled.

This pass completes the planning contract for consolidation. It does not claim that generated docs have been refreshed.
