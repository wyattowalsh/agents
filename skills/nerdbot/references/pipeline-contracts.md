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
| Wiki plan | `config/wiki-plan.json` or `config/wiki-plan.md` | Optional steering surface for scope, focus paths, page hierarchy, and caps; never overrides provenance or approval gates |
| Evidence ledger | `indexes/evidence-ledger.md` | Update with claim-level provenance when wiki claims change |
| Review queue | `indexes/review-queue.md` | Queue uncertain save-back, parser warnings, and watch events before promotion |
| Activity log | `activity/log.md` | Append-only human projection of committed operations, keyed by an exact standalone `<!-- nerdbot-operation-id: ... -->` marker; missing committed entries are repaired idempotently from the journal |
| Operation journal | `activity/operations.jsonl` | Canonical append-only JSONL with `prepared -> committed|failed|review-needed`; immutable payload and exactly one terminal transition per operation ID |
| Research journal | `activity/research/` | Journal-only by default; approved ingest required before adding sources |
| Generated artifacts | `indexes/generated/` | Rebuildable; never canonical |

Mutating workflows serialize the entire apply batch—not only journal appends—through `activity/.nerdbot-operation.lock`. After bootstrapping any required coordination directory and lock file, a writer must append `prepared` before its first workflow data write and append one terminal transition while it still owns the lock. Abrupt stops may leave `prepared` for deterministic resume; ordinary exceptions record `failed`. Only `committed` entries reach the activity log.

## Advanced Wiki Payloads

`nerdbot plan` exposes `advanced_wiki_logics` so machine callers can see which LLM-wiki patterns are in scope before mutating files. `nerdbot query` exposes `payload.provenance_sources` and `payload.missing_provenance_sources` so cited source IDs can be checked against `indexes/source-map.md` without changing the stable `QueryResult` shape.
