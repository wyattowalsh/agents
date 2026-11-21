# Design

## Contracts and ownership

Use Python 3.13, skill-local modules, argparse entrypoints, and JSON stdout.
The approved design uses one canonical per-run JSON execution state with a
single writer, unique temporary files, atomic replace, and durability flushes.
SQLite is allowed for a bounded, resumable inventory, not a second execution
authority. File and state updates are not one filesystem transaction.

Reports use `schema_version: "2.0"`, `run_id`, `updated_at`, `status`, `scope`,
`coverage`, `counts`, `savings`, and optional collection fields. Unknown byte or
risk evidence is null/unknown. Existing documented 1.1 reports may be normalized
explicitly, but completed bytes never become verified reclaimed bytes. Source
identity is included when available. Collection fields must have the right type.
All producers use the report normalizer owned by the reporting lane.

Plans bind an exact source/destination mapping, immutable IDs, object identity,
hash algorithm, before-state, source and destination roots, policy version,
failure policy, verification, and recovery. An editable approval flag is not
authority. The trusted invoker must supply approval for the exact plan digest;
it is responsible for obtaining user consent. New files never join implicitly.

Local execution supports only explicitly qualified owned regular-file
operations. It rejects symlinks, cloud/app-managed/protected roots, collisions,
unknown versions, unsupported metadata or volume semantics, and stale inputs.
Durable `prepared` precedes effects; applied/verified/failed/uncertain/conflict
are distinct. No uncertain operation is blindly replayed. Reverse operations
never overwrite an occupied original path.

Tool adapters observe and normalize only. Registry records declare version,
parser, commands, side effects, limits, and provenance. Mole cleanup, arbitrary
organize actions, generated rmlint scripts, and tool-native undo do not bypass
the common approval/execution contract. Unknown tool versions fail closed for
parsing, with their raw reports available for manual inspection.

## Parallel lanes

| Lane | Owned paths | Validation |
| --- | --- | --- |
| Lead | SKILL, packaging, policy/cloud/dependency references, evals, OpenSpec, integration | package, policy, eval, repository gates |
| Execution | manifest-manager, execution module, plan/state schemas, execution tests | concurrency, interruption, drift, collision, reverse fixtures |
| Observation | scanner/tool CLI, inventory/adapters, registry, fixtures, tool/scan/duplicate/rename/organization references | parser, scan-resume, dependency, safe-rules fixtures |
| Reporting | renderer, report contract/schema, dashboard, reporting references/tests | truthfulness, malformed data, offline behavior, accessibility |

The lead arbitrates contract changes. Generated surfaces have one docs-steward
owner after source changes settle. Independent review follows implementation.

## Qualification

Report separately: deterministic Linux/Python tests, installed-package tests,
rendered browser evidence, macOS/APFS metadata behavior, native tool execution,
provider behavior, and live model evals. Missing native evidence narrows claimed
support instead of silently passing a gate.
