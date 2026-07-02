# Hooks Runtime Performance Delta

## Purpose

Define the runtime performance contract for repo-managed hook projections,
including staged optimization tiers, bundling safety, worker behavior, and
relative regression gates.

## Requirements

### Requirement: Staged performance tier flag

The fleet hook rendering pipeline SHALL support a `WAGENTS_HOOK_PERF_TIER`
policy value (`legacy` | `g1` | `bundle` | `worker`) that gates bundle and
worker runtime optimizations introduced by this change. The default tier SHALL
be `legacy`, which SHALL keep the one-rendered-entry-per-registry-row
dispatcher shape for every supported harness.

#### Scenario: Default tier is behavior-neutral

- **GIVEN** `WAGENTS_HOOK_PERF_TIER` is unset in repo policy
- **WHEN** any harness hook projection is rendered
- **THEN** the rendered output SHALL NOT collapse multiple registry rows into
  a bundle or worker invocation
- **AND** baseline registry metadata fields and matcher-narrowing quick wins
  MAY be present as default behavior when covered by focused validation

### Requirement: Enforce-tier deny transport preserved under bundling

Bundled policy execution (`wagents.hooks.bundle.run_bundle`) MUST preserve
the exact per-harness deny/allow JSON shapes and stdout/exit-code transport
established by `fleet-hooks-guard-expansion`. A bundle MUST NOT convert an
enforce-tier deny into a non-blocking outcome for any harness.

#### Scenario: Bundled Cursor shell guard still denies

- **GIVEN** a `bundle_group` containing `cursor-destructive-shell-guard` and
  `cursor-protected-file-guard`
- **WHEN** the bundle runs with a destructive `rm -rf /` command payload
- **THEN** stdout SHALL contain `{"permission":"deny",...}` and exit code
  SHALL be 0, identical to invoking `cursor-destructive-shell-guard` alone

#### Scenario: Bundle timeout budget never exceeds harness timeout

- **GIVEN** a `bundle_group` whose member policies sum to more timeout than
  the harness's configured hook timeout
- **WHEN** the bundle is rendered
- **THEN** the rendered timeout SHALL be
  `min(sum(policy_timeout), harness_timeout)`

### Requirement: OpenCode and Grok fail-open scope is not widened

The bundle and worker execution paths MUST fail open only under the same
conditions already permitted for OpenCode and Grok Build: dispatcher
crash, timeout, or an unparseable/absent stdout payload. An explicit deny
payload from any policy in a bundle MUST still block.

#### Scenario: OpenCode bundle deny still blocks

- **GIVEN** the OpenCode bridge invokes `run-wagents-hook --bundle
  cursor-destructive-shell-guard,git-commit-push-guard --harness opencode`
- **WHEN** the payload contains a force-push to `main`
- **THEN** stdout SHALL contain an OpenCode deny shape and the bridge
  `isDeny()` check SHALL return true

### Requirement: Relative regression gate, not an absolute latency target

Performance validation SHALL compare against the legacy-tier baseline using a relative p95 latency regression threshold of at most 10 percent, and SHALL NOT use a fixed absolute wall-clock target as a gate because hook latency is machine-dependent.

#### Scenario: CI perf job compares relative regression only

- **GIVEN** the optional CI `hook-perf` job runs hyperfine against a bundle
  or worker tier
- **WHEN** it reports p95 latency
- **THEN** the job SHALL fail only if p95 exceeds the recorded `legacy`
  baseline p95 by more than 10%, not against a fixed millisecond constant
