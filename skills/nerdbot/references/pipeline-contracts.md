# Pipeline Contracts

## Gate Sequence

| Gate | Purpose | Required Output |
|------|---------|-----------------|
| Classify | Select mode and safety posture | Mode, target, read-only/mutating default |
| Inventory | Map layers, vault state, canonical material, risky paths, and automation | JSON inventory and next actions |
| Plan | Propose the smallest reviewable batch | File-level plan with non-goals |
| Confirm | Stop before destructive/high-impact work | Approval or downgrade to plan-only |
| Execute | Apply one additive batch | Files changed by layer |
| Verify | Check provenance, indexes, schema, config, and activity log | Lint/audit result |
| Handoff | Record unresolved gaps | Activity entry and next safe batch |

Machine callers should prefer CLI JSON payloads. `plan` includes both `suggested_next_command` for humans and `suggested_next_argv` for shell-safe execution. Empty `nerdbot` invocation renders the read-only mode gallery and exits successfully.

## Mode Defaults

| Mode | Default behavior |
|------|------------------|
| `create` | Scaffold with `bootstrap`; no synthesis before indexes and activity log exist |
| `ingest` | Add originals/extracts/stubs under `raw/`, then update source map and review queue |
| `enrich` | Synthesize only from `raw/` or declared canonical material |
| `audit` | Read-only inventory and lint |
| `query` | Read-only answer from `wiki/` and `indexes/` first |
| `derive` | Generate rebuildable artifacts without replacing canonical inputs |
| `improve` | Inventory-first additive repair for imperfect repos |
| `migrate` | Interview, blast-radius map, rollback, explicit approval |

## Review-First Durable Surfaces

| Surface | Default path | Mutation rule |
|---------|--------------|---------------|
| Evidence ledger | `indexes/evidence-ledger.md` | Update with claim-level provenance when wiki claims change |
| Review queue | `indexes/review-queue.md` | Queue uncertain save-back, parser warnings, and watch events before promotion |
| Operation journal | `activity/operations.jsonl` | Append-only JSONL for replayable operations |
| Research journal | `activity/research/` | Journal-only by default; approved ingest required before adding sources |
| Generated artifacts | `indexes/generated/` | Rebuildable; never canonical |
