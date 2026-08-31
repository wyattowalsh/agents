# Repo Sync Spec Delta — Things++

## ADDED Requirements

### Requirement: Harness sync projects the Things group without direct servers

Repo and home projection SHALL derive Things client configuration only from the canonical `things` group and its client policy.

#### Scenario: Codex projection is rendered

- **WHEN** repo or approved home sync renders Codex configuration
- **THEN** `mcphub_group_things` SHALL point to loopback `/mcp/things`
- **AND** individual `things-core`, `things-shortcuts`, `things-native`, SupaThings, and alternate Things group entries SHALL be absent or disabled
- **AND** group default/per-tool approval modes SHALL match canonical registry policy.

#### Scenario: Approved installed Codex projection is applied

- **WHEN** local closeout applies the home projection with a Codex-only platform filter
- **THEN** sync SHALL process Codex rather than returning without a target and SHALL NOT touch any other home harness
- **AND** it SHALL capture an exact recoverable backup before mutation, preserve every unrelated Codex entry, apply only the managed `mcphub_group_things` projection and scoped retired-entry tombstones, and read back exact `/mcp/things`
- **AND** any apply or readback failure SHALL restore the exact backed-up Codex configuration without changing repository state or another harness.

#### Scenario: Another local harness is rendered

- **WHEN** an opt-in supported harness requests Things capability
- **THEN** it SHALL receive the `things` group route rather than a generic or direct server route
- **AND** the default `harness` projection SHALL remain unchanged.

### Requirement: Repo-only generation is private-state-free and complete

Before shared generation, repo-only sync SHALL resolve the requested targets without reading home/private secret fallbacks and SHALL own every managed repo MCP projection it claims to check. It SHALL render disabled opt-in entries where the target format supports them and SHALL strip only managed/tombstoned entries while preserving unrelated configuration.

#### Scenario: Repo-only sync is previewed or applied

- **WHEN** `scripts/sync_agent_stack.py` runs with `--targets repo`
- **THEN** target selection SHALL occur before any `.env.mcphub`, home Codex config, Codex backup, home harness, or other private fallback read
- **AND** the command SHALL perform no home write, live apply, runtime action, or secret materialization.

#### Scenario: Managed repo MCP surfaces are rendered

- **WHEN** repo generation renders Codex, OpenCode, Cursor, or another supported local harness
- **THEN** the sanitized repo Codex config SHALL be derived without reading home Codex config
- **AND** OpenCode's repo `mcp` map SHALL be rerendered rather than preserving stale managed entries
- **AND** Cursor SHALL retain one disabled `mcphub_group_things` opt-in projection rather than dropping the disabled spec
- **AND** each supported repo projection SHALL contain exactly one disabled local `mcphub_group_things` at `http://127.0.0.1:46683/mcp/things` and no direct, generic, alternate, or SupaThings route.

#### Scenario: A pre-generation repo-sync blocker remains

- **WHEN** repo-only sync would read private/home fallbacks, omit a managed Codex/OpenCode projection, drop Cursor's disabled opt-in group, or produce unrelated generated churn
- **THEN** S2-03 generation SHALL stop before any shared output is written
- **AND** focused source tests SHALL prove the remediation before serialized apply/check resumes.

### Requirement: Retired Things projections use scoped tombstones

Sync SHALL support explicit retired projection IDs for active SupaThings and the stale unmanaged direct Things entry, applied only after exact backup and source proof.

#### Scenario: A retired entry is present beside unrelated config

- **GIVEN** a local config contains a retired Things/SupaThings ID and unrelated user-owned entries
- **WHEN** approved home sync applies the tombstone
- **THEN** only the exact retired entry SHALL be removed
- **AND** all unrelated keys and values SHALL remain byte/semantically equivalent.

### Requirement: Shared generation is serialized

Registry settings, repo projections, root plugin reconciliation, and docs generation SHALL run only after all source writers have joined and SHALL have one active writer at a time.

#### Scenario: A source owner is still active

- **WHEN** the integration captain reaches a shared generator step
- **THEN** generation SHALL wait until every dispatched source task is resolved
- **AND** the captain SHALL inspect generated diffs for unrelated churn before the next generator runs.

### Requirement: Capability manifest and schema are validated before projection

Repo sync SHALL consume only a schema-valid, semantically closed `capability-manifest.json` with exact 70/37/17/25/16 inventories, zero removed/unmapped rows, net-new outcomes, exact audited upstream provenance/schema hashes, and separate adapted-public schema hashes.

#### Scenario: A manifest row drifts

- **WHEN** a tool, mapping, workflow, eval ID, public name, scope, annotation, prerequisite, or test ID differs from the active OpenSpec contract
- **THEN** projection SHALL stop before writing generated or local config
- **AND** maintainers SHALL revise and validate this OpenSpec change before continuing.
