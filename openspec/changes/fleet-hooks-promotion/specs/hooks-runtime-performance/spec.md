# Hooks Runtime Performance Promotion Delta

## MODIFIED Requirements

### Requirement: Staged performance tier flag

The fleet hook rendering pipeline SHALL support a `hook_perf.tier` policy value
(`legacy` | `g1` | `bundle` | `worker`) in `config/tooling-policy.json` that
gates bundle and worker runtime optimizations. After Hooks Bundle Promotion v2
(W5), the committed repo policy SHALL use `bundle` so Cursor, Codex, Copilot,
and other dispatcher-backed harnesses collapse `fleet-pre-tool-enforce` registry
groups into `{hook_runner} --bundle` spawns while preserving enforce-tier deny
transport.

#### Scenario: Repo policy promotes bundle tier after W5

- **GIVEN** `config/tooling-policy.json` sets `"hook_perf": { "tier": "bundle" }`
- **WHEN** `scripts/sync_agent_stack.py --apply --targets repo` renders harness hooks
- **THEN** consecutive registry rows sharing a `bundle_group` SHALL collapse to
  one rendered spawn per group per logical event
- **AND** `legacy` tier behavior SHALL remain available by setting `tier` to
  `legacy` for rollback or byte-stable fixture tests

### Requirement: Relative regression gate, not an absolute latency target

Performance validation SHALL compare bundle-tier spawn counts against committed
baseline JSON under `docs/public/generated-reports/` and SHALL use optional
hyperfine p95 comparisons only when hyperfine is available. CI SHALL fail when
live inventory `total_spawns` exceeds the committed bundle baseline or when
`scripts/hooks/hook_assurance.py` reports budget violations.

#### Scenario: CI hook-perf job compares spawn counts to committed baseline

- **GIVEN** the optional CI `hook-perf` workflow_dispatch job runs
- **WHEN** it executes `hook_perf_inventory.py --tier bundle --json`
- **THEN** the job SHALL compare `summary.total_spawns` to
  `hook-perf-baseline-bundle.json`
- **AND** the job SHALL fail if live spawns exceed the committed baseline
- **AND** the job SHALL run `hook_assurance.py --json` and fail on non-empty findings

#### Scenario: Legacy baseline artifact remains for rollback analysis

- **GIVEN** `hook-perf-baseline-legacy.json` is committed with tier metadata
- **WHEN** maintainers evaluate bundle promotion impact
- **THEN** they SHALL be able to compare legacy vs bundle spawn totals without
  re-deriving historical registry layout
