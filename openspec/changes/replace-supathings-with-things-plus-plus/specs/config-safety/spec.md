# Config Safety Spec Delta — Things++

## ADDED Requirements

### Requirement: Things++ config changes are exact-target transactions

Repo, home, runtime, and tunnel changes SHALL use fresh inventory, preview, exact-target backup, apply, validation/readback, and exact-byte rollback without overwriting unrelated dirty or local config.

#### Scenario: A rendered home config would drop unrelated state

- **GIVEN** a target home config contains user-owned entries outside the retired Things/SupaThings IDs
- **WHEN** the Things++ projection is previewed
- **THEN** sync SHALL preserve those entries or fail before writing with redacted exact paths
- **AND** SHALL NOT replace the entire file from a stale template.

#### Scenario: Live validation fails after apply

- **GIVEN** exact backups passed byte-restorability checks
- **WHEN** runtime, installed-client, OAuth, or tunnel readback fails after apply
- **THEN** public ingress SHALL be disabled first
- **AND** the operator SHALL restore only the exact backed-up targets and revalidate the prior runtime without resetting/stashing repository work.

#### Scenario: Stored runtime evidence is stale or inconsistent

- **GIVEN** the F0 runtime/process capture is temporally inconsistent/stale
- **WHEN** cutover is about to begin
- **THEN** the operator SHALL collect fresh provenance immediately before cutover and verify it represents one coherent current runtime
- **AND** SHALL NOT use the F0 capture as cutover evidence.

### Requirement: MCPHub downstream materialization is frozen and content addressed

Production MCPHub SHALL execute only a same-process downstream distribution materialized from the exact signed `@samanhappy/mcphub@1.0.32` tarball, the exact transitive `pnpm-lock.yaml`, and the complete owned-source/patch manifests. Every selected split TypeScript SDK v2 package SHALL be exactly `2.0.0`, including `@modelcontextprotocol/server@2.0.0`; the modern/stateless-legacy server edge SHALL remain isolated from the upstream MCPHub v1 SDK client side.

#### Scenario: The downstream is installed and built

- **WHEN** the downstream lock is installed, built, audited, and materialized
- **THEN** install SHALL use the frozen lock without a registry resolution or version range
- **AND** every freshly inventoried current v2-boundary source, deterministic build-time transformation, anchor, bundled module, dependency-graph entry, build output, output-inventory receipt, and aggregate distribution digest receipt SHALL match its manifest
- **AND** the unfrozen retrospective six-replacement/five-patch count SHALL remain non-authorizing historical evidence and SHALL NOT be a seal prerequisite
- **AND** no unspecified production module or transformation SHALL be accepted merely because a historical count matches
- **AND** `productionLoaderTransformations` SHALL equal `[]`
- **AND** production SHALL NOT invoke `npx`, download at launch, or depend on an ESM loader patch.

#### Scenario: A content-addressed runtime is selected

- **GIVEN** the verified distribution exists under `${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}/sha256-<distribution-digest>/`
- **WHEN** activation changes `${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}/current`
- **THEN** the pointer replacement SHALL be atomic and SHALL target only the verified digest directory
- **AND** launcher/runtime config SHALL resolve and validate the deployment-owned host root rather than assuming a literal machine path.

#### Scenario: A downstream input or build drifts

- **WHEN** any tarball, signature, lock entry, selected SDK version, source, patch anchor/output, build artifact, or materialized digest differs
- **THEN** materialization/startup SHALL fail closed before pointer replacement
- **AND** remote Things exposure SHALL remain disabled.

### Requirement: Live Things mutations require two independent gates

Live mutation assurance SHALL remain disabled unless `THINGS_LIVE_MUTATION_TEST=1` and separate explicit user approval are both present.

#### Scenario: Mutation assurance is not authorized

- **WHEN** either the environment flag or explicit approval is absent
- **THEN** validation SHALL use only hermetic fixtures and bounded privacy-preserving reads
- **AND** SHALL record mutation proof as `not run—not authorized` rather than claiming it.

#### Scenario: A mutation test is authorized

- **GIVEN** both gates are present
- **WHEN** the live test executes
- **THEN** it SHALL use one uniquely named disposable item, verify create/update/move, request cleanup approval, and verify deletion
- **AND** SHALL NOT change any pre-existing item.

### Requirement: Remote activation requires offline and observed-wire conformance

Remote activation SHALL first pass offline MCP `2026-07-28` and stateless MCP `2025-11-25` conformance, OAuth/resource/route/schema checks, CIMD-primary and constrained-DCR-fallback tests, and content-digest verification. It SHALL then require a bounded redacted observation of the current ChatGPT wire protocol and registration behavior before explicit remote apply. Ambiguous, missing, or mismatched observation SHALL keep remote disabled.

#### Scenario: Offline conformance passes without current ChatGPT evidence

- **GIVEN** every hermetic protocol, OAuth, route, and distribution test passes
- **WHEN** no current redacted ChatGPT handshake/registration observation is available
- **THEN** local validation MAY proceed
- **AND** the tunnel/public route SHALL remain disabled.

#### Scenario: Current ChatGPT registration is reconciled

- **WHEN** the observed connector selects CIMD or the constrained DCR fallback and negotiates one supported protocol era
- **THEN** the exact observed flow SHALL be matched to the frozen compatibility manifest without retaining tokens or private Things content
- **AND** unobserved registration, session, or transport behavior SHALL NOT be inferred from older documentation.

#### Scenario: A restricted-tunnel probe fails or times out

- **WHEN** OAuth, credential separation, route normalization, tools/schema parity, or external reachability proof fails
- **THEN** the tunnel and public route SHALL be disabled immediately
- **AND** external plus local readback SHALL prove the disabled state.

### Requirement: Local and remote listener activation is strictly sequenced

Local activation SHALL bind only the managed bearer listener on `127.0.0.1:46683` with remote mode disabled. It SHALL NOT bind, prewarm, or probe a live `46684` listener, start cloudflared, or consume/create a capture receipt. A passing offline-conformance receipt MAY authorize the first `46684` bind only in the restricted S4-02 capture mode; only the final content/config/route-manifest-bound activation receipt MAY authorize the first production/public `46684` bind in S4-04.

#### Scenario: S3 local runtime is activated

- **WHEN** the verified content-addressed runtime is selected and local doctor/smoke runs
- **THEN** only managed loopback `46683` SHALL be listening
- **AND** readback SHALL prove `46684`, capture mode, capture receipts, and cloudflared are absent while remote remains disabled
- **AND** the local endpoint SHALL expose the exact frozen 70-tool schema/catalog even when missing bridge/TCC prerequisites make only affected calls return typed unavailable/degraded results.

#### Scenario: Remote work is authorized but live prerequisites are unproven

- **WHEN** the explicitly authorized S4/F5 continuation is evaluated after J4 without fresh bridge/TCC, observed-wire, or authenticated UI evidence
- **THEN** remote source implementation and offline conformance MAY proceed in dependency order
- **AND** each missing live proof SHALL be recorded as blocked or unrun for that exact layer rather than `not authorized`
- **AND** production `46684`, tool dispatch, and cloudflared SHALL remain disabled until every prerequisite and activation-receipt check passes.

#### Scenario: Offline remote conformance passes

- **WHEN** S4-01 produces a passing offline-conformance receipt
- **THEN** public/production remote mode SHALL remain disabled
- **AND** S4-02 MAY bind only a short-lived loopback `46684` capture listener limited to frozen handshake/registration paths with Things tool dispatch disabled.

#### Scenario: Production remote activation is requested

- **WHEN** separate remote authorization exists, both fixed bridges and noninteractive TCC readiness are freshly proven, the capture listener/tunnel have stopped, and the final activation receipt matches every required content, configuration, route-manifest, and unexpired observed-wire input digest
- **THEN** S4-04 MAY perform the first production/public `46684` bind and restricted cloudflared attachment
- **AND** any missing, expired, ambiguous, or mismatched input SHALL leave `46684` unbound and public ingress disabled.

### Requirement: Auth state is excluded from rollback snapshots

Exact binary/config pointer rollback SHALL NOT snapshot, replace, or restore `${MCPHUB_OAUTH_STATE_DIR}/oauth.sqlite3`, authorization transactions, codes, access tokens, refresh tokens, receipt state, or consumed/revoked credential families. The OAuth database is a separate owner-only hash-state store and SHALL never contain Things database content.

#### Scenario: Runtime config is rolled back

- **WHEN** prior config bytes are restored
- **THEN** only verified binary pointers and exact configuration bytes SHALL be restored
- **AND** current auth/receipt revocation and consumption state SHALL remain monotonic
- **AND** no credential or mutation receipt SHALL become reusable.
