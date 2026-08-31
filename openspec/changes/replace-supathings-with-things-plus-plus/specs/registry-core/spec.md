# Registry Core Spec Delta — Things++

## ADDED Requirements

### Requirement: One Things MCPHub group owns every Things route

The canonical registry SHALL define exactly one Things-related group named `things`, with deterministic ID `3b94a096-b95f-586c-b2e7-e69ed177eb5a`. All Things MCP tools, policy, authentication, discovery, and dispatch SHALL route only through that group at exact `/mcp/things`: local bearer origin `http://127.0.0.1:46683/mcp/things`, OAuth/cloudflared origin `http://127.0.0.1:46684/mcp/things`, and public resource `https://mcp.w4w.dev/mcp/things`.

#### Scenario: Registry topology is validated

- **GIVEN** `things-core`, `things-shortcuts`, and `things-native` are registered internal servers
- **WHEN** registry validation enumerates all group and client memberships
- **THEN** only `things` SHALL contain any Things server
- **AND** no `things-chatgpt`, `things-admin`, generic-group membership, nested group, alternate Things route, or enabled individual client route SHALL exist.

#### Scenario: A Things policy or transport bypass is introduced

- **WHEN** registry, generated settings, projection, ingress, or runtime inspection finds Things-specific logic outside the `things` group route
- **THEN** generation and startup SHALL fail
- **AND** no direct-server, generic-group, alternate-path, or fallback dispatch SHALL activate.

#### Scenario: Listener topology is activated in stages

- **WHEN** local S3 activation starts the selected runtime
- **THEN** only the registered local bearer origin on `46683` SHALL bind and remote mode SHALL remain disabled
- **AND** the registered `46684` origin SHALL remain unbound until S4-02 capture authorization, and SHALL NOT enter production/public mode before S4-04 final-stamp authorization.

### Requirement: The Things group uses explicit complete allowlists

The `things` group SHALL list all 41 core, 21 Shortcuts, and 8 native tools explicitly and SHALL reject wildcard or allow-all declarations.

#### Scenario: Group settings are generated

- **WHEN** the settings generator renders the `things` group
- **THEN** its per-server tool sets SHALL equal the frozen manifests
- **AND** the qualified union SHALL equal 70 unique tools
- **AND** all 37 SupaThings outcomes, 17 Things Manager workflows, 25 rewritten legacy eval concepts, and 16 additive eval cases SHALL remain mapped
- **AND** set/schema-digest comparison SHALL fail on missing, extra, renamed, or colliding tools.

#### Scenario: Coverage changes

- **WHEN** implementation or generation changes any tool, outcome, workflow, or eval mapping
- **THEN** coverage MAY expand only through an explicit OpenSpec/manifest revision
- **AND** it SHALL NOT contract below 70/37/17/25/16 or remove a previously covered outcome.

#### Scenario: Public tool names are qualified

- **WHEN** registry generation maps a server tool into the group
- **THEN** its public name SHALL equal `normalize(server) + "__" + serverToolName` from `capability-manifest.json`
- **AND** duplicate IDs/names, aliases, server names containing `__`, or an unmanifested name SHALL fail generation and startup.

#### Scenario: Local and remote tools lists are observed

- **WHEN** authenticated `tools/list` runs through both credential listeners
- **THEN** each public name and UTF-8 sorted-key compact-JSON input/output schema SHA-256 SHALL equal the adapted-public manifest contract
- **AND** audited upstream schema hashes SHALL remain separately recorded rather than overwritten by adapted hashes
- **AND** count-only equality SHALL NOT pass.

### Requirement: The exact group route is dual-era, stateless, and session-free

Authenticated and unauthenticated route middleware SHALL expose the same `things` group only at canonical `/mcp/things` and SHALL support MCP `2026-07-28` plus stateless MCP `2025-11-25`. The edge SHALL use exact `@modelcontextprotocol/server@2.0.0` `createMcpHandler` behind a body-primary fail-closed preflight seam that compensates for the exact v2.0.0 missing-header defect, while isolating the upstream MCPHub v1 SDK client side. Neither era SHALL issue, require, or accept `Mcp-Session-Id`, and no GET event-stream transport SHALL exist.

#### Scenario: A modern client discovers the server

- **GIVEN** a request declares MCP `2026-07-28`
- **WHEN** the conformance client begins protocol negotiation
- **THEN** it SHALL call `server/discover` and then `tools/list` over canonical POST requests as a proof sequence
- **AND** the stateless edge SHALL NOT retain or require prior discovery state before an independently valid modern request
- **AND** each request SHALL carry the required `MCP-Protocol-Version`, `Mcp-Method`, conditional `Mcp-Name`, and body `_meta.io.modelcontextprotocol/{protocolVersion,clientCapabilities}` contract
- **AND** a header/body protocol or method mismatch SHALL fail with HTTP `400` and protocol error `-32020` before group dispatch.

#### Scenario: A legacy client uses compatibility initialization

- **GIVEN** a request declares MCP `2025-11-25`
- **WHEN** it invokes `initialize`
- **THEN** initialization SHALL be handled only by the stateless legacy compatibility path
- **AND** initialize-only success SHALL NOT count as modern, tool-list, capability, or remote compatibility proof.

#### Scenario: A caller assumes an MCP session or GET stream

- **WHEN** a caller sends `Mcp-Session-Id`, requests GET/DELETE `/mcp/things`, or attempts a standalone SSE stream
- **THEN** session-bearing requests SHALL fail closed and GET/DELETE SHALL return the versioned method-not-allowed response
- **AND** no stateful fallback, implicit session, or alternate streaming route SHALL be created.

#### Scenario: A caller targets another route form

- **WHEN** the method/path targets `/mcp`, a direct Things server, `$smart`, an alternate group, a noncanonical encoding, slash/dot variant, or disallowed method
- **THEN** middleware SHALL terminate with the versioned deny-by-default response before MCPHub group routing.

### Requirement: SupaThings is retired from active registry surfaces

Active registry, current generated settings, and managed client projections SHALL contain no `supathings` server or membership after cutover.

#### Scenario: Historical evidence contains SupaThings text

- **GIVEN** archives, raw captures, rollback evidence, or historical planning records retain SupaThings references
- **WHEN** the active-surface absence guard runs
- **THEN** named historical allowances MAY remain
- **AND** canonical/current/generated runtime roots SHALL contain no active SupaThings configuration.
