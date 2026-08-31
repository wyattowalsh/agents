# MCP Audit Spec Delta — Things++

## ADDED Requirements

### Requirement: Things core is an immutable sanitized upstream adapter

`things-core` SHALL launch `mcp-server-things==1.9.0` from the exact manifest-pinned wheel, sdist, and installed `RECORD`, with all `48/48` `RECORD` entries verified, and SHALL preserve all 41 audited tool outcomes behind a first-party protocol/security adapter rather than reimplementing CRUD. Audited upstream name/schema hashes and future adapted-public schema hashes SHALL remain separate evidence fields.

#### Scenario: The upstream pin or credential file is unsafe

- **GIVEN** the resolved upstream version/hash differs from the audited pin or `~/.things-auth` is a symlink, wrong-owner file, or not mode `0600`
- **WHEN** the managed wrapper starts
- **THEN** startup SHALL fail closed without printing the token or path contents.

#### Scenario: A core result contains sensitive material

- **GIVEN** an upstream result, error, or diagnostic contains an auth token, Things URL, local path, environment value, or private task content
- **WHEN** the adapter serializes the MCP response or log
- **THEN** the material SHALL be removed or masked before it crosses the boundary.

#### Scenario: The audited upstream schema inventory is checked

- **WHEN** FastMCP `list_tools` is inspected without invoking a tool or reading Things data
- **THEN** the ordered and sorted name hashes, all 41 sorted-key compact-JSON input-schema hashes, and the common upstream output-schema hash SHALL equal `capability-manifest.json`
- **AND** adapted schema hashes SHALL be populated and compared separately before activation.

### Requirement: Native bridges expose only fixed typed operations

`things-shortcuts` SHALL expose exactly 21 fixed tools and `things-native` SHALL expose exactly 8 fixed tools, each with closed Pydantic models, accurate annotations, bounded execution, and structured errors. Native `native_health` SHALL remain a static readiness tool that performs no AppleEvent. Native `open_search` SHALL use only the repository-owned fixed `things:///search` builder with internal query encoding and no caller URL; the other six native tools SHALL use static/fixed AppleScript.

#### Scenario: A caller attempts to select executable source

- **WHEN** a request attempts to choose a Shortcut name, AppleScript source, command fragment, URL, file, or raw payload
- **THEN** the applicable server SHALL reject it before process execution
- **AND** only repository-owned fixed bridge/script identifiers or the fixed search URL builder SHALL be invocable.

#### Scenario: Shortcuts or TCC is unavailable

- **GIVEN** a bridge is absent or macOS denies access
- **WHEN** health or an affected operation runs
- **THEN** the tool SHALL return a typed unavailable/degraded result
- **AND** SHALL NOT fall back to raw URL, UI automation, or direct database access.

#### Scenario: F0 prerequisites are reconciled

- **GIVEN** both fixed Things++ Shortcut bridges were observed absent, TCC readiness is unproven, and the current runtime capture is temporally inconsistent/stale
- **WHEN** source work or activation readiness is evaluated
- **THEN** source implementation and local bearer schema/catalog activation MAY proceed after fresh coherent runtime provenance, with the complete frozen 70-tool catalog visible
- **AND** each affected invocation SHALL return a typed unavailable/degraded result without raw execution, UI automation, direct database access, or a false operational claim
- **AND** remote/public activation SHALL remain blocked until both fixed bridges, noninteractive TCC readiness, and every remote/observed-wire gate are freshly proven.

### Requirement: Fixed operations preserve audited safety semantics

`create_structured_project`, `edit_items`, and `duplicate_items` SHALL be bulk writes; `edit_items` SHALL be documented non-undoable; `delete_heading` and `delete_area` previews SHALL count affected children; and `set_tag_parent` SHALL assign a parent only in v1.

#### Scenario: A caller requests an unproven or cascading operation

- **WHEN** a caller requests tag-parent detach or previews heading/area deletion
- **THEN** detach SHALL be rejected until synthetic and separately authorized manual proof exists
- **AND** each deletion preview SHALL include its affected-child count before confirmation.

### Requirement: MCPHub built-in OAuth is end-to-end resource bound

The Things remote route SHALL use only the same-process, repository-owned MCPHub downstream and its built-in authorization server, hardened across authorization parsing, client identity, code persistence, token issue, refresh, verification, route dispatch, revocation, metadata, and log/error serialization. It SHALL NOT delegate authorization to an external identity provider or facade.

#### Scenario: An authorization or token invariant fails

- **GIVEN** missing state, non-S256 PKCE, wrong resource/audience/principal/route, insufficient scope, replayed refresh token, revoked token, dashboard JWT, local bearer, or query/body token
- **WHEN** the request reaches any public Things auth or MCP module
- **THEN** it SHALL fail closed
- **AND** remote Things exposure SHALL remain disabled if the conformance suite does not pass in full.

#### Scenario: A downstream input, anchor, or output drifts

- **GIVEN** an upstream tarball, dependency lock, owned source, patch anchor, materialized output, or conformance digest differs from the manifest
- **WHEN** materialization or production startup runs
- **THEN** it SHALL abort rather than applying a partial or best-effort patch
- **AND** the remote listener and tunnel SHALL remain disabled.

### Requirement: MCPHub downstream distribution is exact and content addressed

The downstream SHALL bind the exact `@samanhappy/mcphub@1.0.32` tarball SHA-256 `4cb58d4cb11c7d036bde169504f0ddbe9849159e40fe764950ad62853d1502bb`, npm integrity, signature evidence, complete transitive lock, source/patch inventory, patch anchors, and output hashes into one immutable content ID. It SHALL freeze `@modelcontextprotocol/server@2.0.0` and exact `2.0.0` split `node`/`core` packages when imported, while isolating exact-locked `@modelcontextprotocol/sdk@1.29.0` to private legacy backend-client traffic.

#### Scenario: The production launcher is asked to resolve mutable code

- **WHEN** launch would use `npx`, a semver/range install, mutable npm cache, live patch, ESM loader, `--loader`, `--import`, or `NODE_OPTIONS`
- **THEN** production startup SHALL fail closed
- **AND** SHALL resolve only an atomically published, output-verified content ID.

#### Scenario: Retrospective transformation counts cannot authorize production

- **GIVEN** historical notes counted six whole-module replacements and five guarded patches without freezing their identities, anchors, preimages, postimages, or outputs
- **WHEN** the downstream seal is evaluated
- **THEN** those counts SHALL remain non-authorizing historical evidence and SHALL NOT be required or accepted as proof of closure
- **AND** a fresh complete inventory SHALL name and digest every current production-loaded module, deterministic build-time transformation, anchor, bundled input, and output before materialization.

#### Scenario: Production loader transformations are absent

- **GIVEN** the complete current source, transformation, bundle, and output inventories are sealed
- **WHEN** materialization or same-process launch is checked
- **THEN** `productionLoaderTransformations` SHALL equal `[]`
- **AND** any live patch, ESM hook, `--loader`, `--import`, unresolved dynamic import, or native runtime resolver SHALL fail closed.

### Requirement: The public edge supports exactly two stateless MCP eras

The sole public edge SHALL support current MCP `2026-07-28` and stateless legacy MCP `2025-11-25`, structurally select one era, and SHALL never fall back from an invalid modern request to legacy. It SHALL never mint, require, persist, or echo an MCP session ID; `Last-Event-ID` SHALL NOT resume a transport session.

#### Scenario: A current request is valid

- **GIVEN** a POST body containing matching `params._meta["io.modelcontextprotocol/protocolVersion"]` and `params._meta["io.modelcontextprotocol/clientCapabilities"]`
- **WHEN** `MCP-Protocol-Version`, `Mcp-Method`, and any required `Mcp-Name` agree with the JSON-RPC body
- **THEN** the edge SHALL dispatch it as `2026-07-28`
- **AND** `server/discover` SHALL report exactly `supportedVersions: ["2026-07-28"]` plus tools/cache metadata
- **AND** stateless `2025-11-25` SHALL remain available only through its separate legacy `initialize` compatibility lane.

#### Scenario: Current headers and body disagree

- **WHEN** a modern protocol/method/name header is missing, malformed, or contradicts the body
- **THEN** the edge SHALL return HTTP `400` with JSON-RPC `-32020`
- **AND** unsupported versions SHALL return HTTP `400`/`-32022`, missing capabilities SHALL return `-32021`, and an unknown modern RPC SHALL return HTTP `404`/`-32601`
- **AND** no legacy handler SHALL run.

#### Scenario: A legacy client initializes

- **WHEN** a structurally valid initialization negotiates `2025-11-25`
- **THEN** subsequent legacy calls SHALL use the stateless legacy envelope
- **AND** SHALL NOT receive or require `Mcp-Session-Id`.

#### Scenario: A non-POST transport method reaches the authenticated resource

- **WHEN** either credential class sends canonical `GET /mcp/things` or `DELETE /mcp/things`
- **THEN** the edge SHALL return `405`, with `Allow: POST` on GET
- **AND** invalid present `Origin` SHALL return `403` before group dispatch.

### Requirement: Both MCP eras normalize to one exact Things catalog

Exactly one MCPHub group named `things` and exactly one MCP path `/mcp/things` SHALL expose only `things-core` (41), `things-shortcuts` (21), and `things-native` (8). Modern and legacy `tools/list` SHALL normalize to the same deterministic 70 public tool objects and adapted schema digests; direct, global, smart, generic, alternate-group, and alternate-path Things access SHALL remain denied.

#### Scenario: Catalog closure is checked across eras

- **WHEN** authenticated modern and legacy catalogs are canonicalized after removing only their transport-envelope fields
- **THEN** their ordered 70 tool objects, names, input schemas, output schemas, annotations, and minimum scopes SHALL be equal
- **AND** closure SHALL retain all 37 SupaThings mappings, 17 skill workflows, 25 rewritten eval concepts, and exactly 16 new eval cases
- **AND** adapted-public hashes in `capability-manifest.json` SHALL NOT be rewritten merely because the envelope differs.

### Requirement: CIMD is primary and DCR is a strict fallback

MCPHub built-in OAuth SHALL prefer an approved HTTPS Client ID Metadata Document, SHALL allow constrained DCR only when the observed ChatGPT profile selects it, and SHALL bind each transaction to exactly one registration mode. Authorization-server metadata SHALL advertise RFC 9207 issuer identification; protected-resource and authorization-server metadata SHALL use the same exact issuer; every successful and error authorization response SHALL return its matching `iss`.

For durable ChatGPT connectivity the profile SHALL request and the
authorization flow SHALL accept `offline_access` and issue rotating refresh
tokens. `offline_access` is a refresh capability only: it SHALL NOT enter the
Things authorization-scope set or MCP `AuthInfo`, imply `things.read`,
`things.write`, or `things.admin`, widen catalog/tool access, or satisfy any
tool's minimum scope. Conformance evidence SHALL prove refresh replay-family
revocation separately from the three independent Things scope checks.

#### Scenario: ChatGPT uses approved CIMD

- **GIVEN** the user-owned app confirms the exact client metadata URL and callback
- **WHEN** the server validates a `none` or `private_key_jwt` CIMD client
- **THEN** it SHALL bind the exact metadata/callback/resource digests and PKCE S256
- **AND** private-key JWT verification SHALL enforce approved JWKS, issuer, subject, audience, time, and one-time hashed JTI without storing a client secret.

#### Scenario: DCR fallback or issuer identification is invalid

- **WHEN** DCR metadata/callback differs, the registration mode is substituted, `iss` is missing or mismatched, or an issued DCR secret does not match its stored hash
- **THEN** registration, authorization, or exchange SHALL fail closed as applicable
- **AND** no wildcard, private/loopback, insecure, custom-scheme, fragment, userinfo, or unapproved redirect SHALL be accepted.

### Requirement: Remote enablement is bound to conformance and observed wire evidence

Remote exposure SHALL default disabled. A nonexpired passing activation receipt SHALL bind the downstream output, npm provenance/tarball, complete lock, owned-source/patch manifest, route manifest, dual-era codec/SDK lock, settings, single-group policy, normalized 70-tool catalog/scope map, client-registration/callback policy, redacted observed-wire evidence, and conformance result digests, with `noSecrets: true`.

#### Scenario: Documentation exists but current ChatGPT wire behavior is unobserved

- **GIVEN** OpenAI documents Streamable HTTP and OAuth/CIMD/DCR behavior but does not document the MCP protocol version/header shape emitted by ChatGPT
- **WHEN** activation readiness is evaluated without a current redacted observed-wire pass
- **THEN** source and hermetic validation MAY pass
- **AND** `remotePublicReady` and `tunnelAllowed` SHALL remain false.

#### Scenario: Capture output is finalized as public evidence

- **WHEN** the restricted recorder finalizes an observed-wire artifact
- **THEN** it SHALL match the closed public v1.1 schema with `status: observed-pass`, an unexpired RFC 3339 capture window, the exact public resource/callback/registration/protocol facts, exact ordered independent Things scopes, refresh-only `offline_access`, resource indicator, PKCE S256, discovery fact, and fixed capture route statuses
- **AND** it SHALL bind the capture-receipt, callback, and canonical internal-record digests while admitting no free-form field, cookie, token, authorization code, verifier, state, account identifier, or private Things content
- **AND** `capturedAt` SHALL fall inside the at-most-30-minute capture-receipt window while the separate evidence `expiresAt` MAY outlive capture but SHALL be no more than 24 hours after `capturedAt`
- **AND** public receipt issuance SHALL reject a schema/version/key/status/time/digest/route/scope/privacy mismatch before hashing the evidence as a receipt binding.

#### Scenario: An activation-receipt input changes or expires

- **WHEN** any bound digest, result, callback approval, `createdAt`/`expiresAt`, or no-secrets assertion is absent, stale, or mismatched
- **THEN** the OAuth listener SHALL NOT become remotely reachable
- **AND** tunnel enablement SHALL fail closed without a fallback route or credential class.

### Requirement: Local bearer and remote OAuth ingress are separate

The same `things` group/path SHALL be reachable on a bearer-only local listener and a distinct OAuth-only loopback listener used exclusively by cloudflared; listener provenance SHALL come from the accepted socket rather than forwarding headers.

#### Scenario: A credential class is substituted

- **WHEN** OAuth is presented to the local listener, the local bearer is presented to the remote listener, or forwarding headers claim another ingress
- **THEN** route middleware SHALL reject the request before group dispatch
- **AND** direct servers, generic paths, `$smart`, alternate groups, and encoded path variants SHALL remain unreachable under both credential classes.

### Requirement: OAuth credentials are opaque, one-time, and atomically bound

MCPHub SHALL validate and hash the client-supplied OAuth `state`, independently issue an at-least-256-bit opaque authorization-transaction nonce/handle plus authorization codes/access/refresh tokens, store only hashes of state/nonce/tokens and DCR client secrets, bind authorization transactions atomically to client ID and registration mode, exact redirect URI, S256 challenge, transaction nonce, principal, exact resource, and exact independent scope set, and enforce fixed expiries/rotation/revocation. Predictable client state SHALL NOT remove the independent server nonce/handle entropy. Private-key-JWT JTI replay state SHALL also be hash-only and monotonic.

#### Scenario: Refresh replay or rollback occurs

- **WHEN** a consumed refresh token is replayed or config rollback runs
- **THEN** the refresh family SHALL be revoked atomically
- **AND** rollback SHALL NOT restore, copy backward, or replace the auth database/WAL, browser sessions, consumed/expired/revoked authorization state, refresh families, client registrations, client-secret hashes, or JWT replay state.

### Requirement: Local artifacts and native prerequisites are integrity checked

Credentials/runtime files SHALL use `O_NOFOLLOW`, owner/mode checks, and pre/post-read inode verification; executable distributions/scripts SHALL be hash-checked immediately before exec; Shortcuts SHALL complete an exact protocol/schema/version handshake without triggering a silent TCC prompt.

#### Scenario: Integrity or TCC readiness fails

- **WHEN** an inode/hash/protocol/schema/version check changes or TCC is not already authorized
- **THEN** affected execution SHALL remain unavailable/degraded with a typed manual prerequisite while the fixed tool schema remains in the local 70-tool catalog
- **AND** SHALL NOT prompt silently or execute the changed artifact.
