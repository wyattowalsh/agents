# OpenAI Harness Spec Delta — Things++

## ADDED Requirements

### Requirement: Codex and ChatGPT consume the same Things capability

Codex and ChatGPT SHALL route to the single MCPHub group named `things` and the same 70-tool Things domain through the single path `/mcp/things`; differences SHALL be limited to transport origin, authentication, OAuth minimum scopes, negotiated MCP era, and client approval behavior. The local origin SHALL be bearer-only `http://127.0.0.1:46683/mcp/things`; the public resource SHALL be OAuth-only `https://mcp.w4w.dev/mcp/things` through remote loopback origin `http://127.0.0.1:46684/mcp/things`.

#### Scenario: Local Codex connects

- **WHEN** Codex uses `http://127.0.0.1:46683/mcp/things` with the loopback bearer through a valid modern discovery request or legacy initialization
- **THEN** it SHALL receive the frozen 70-tool union
- **AND** read tools MAY be automatic while writes/destructive/UI-visible tools use their configured approval modes.

#### Scenario: Local activation completes before remote capture

- **WHEN** the S3 local runtime and installed Codex projection are validated
- **THEN** only bearer origin `127.0.0.1:46683` SHALL be bound and probed
- **AND** no live `46684` listener, capture receipt, capture tunnel, production tunnel, or remote ChatGPT claim SHALL exist before its later explicit gate
- **AND** absent fixed bridges or unproved TCC SHALL degrade only affected calls with typed unavailable/manual-prerequisite results, not contract the 70-tool schema/catalog or trigger a raw fallback.

#### Scenario: Remote ChatGPT connects

- **WHEN** ChatGPT uses `https://mcp.w4w.dev/mcp/things` through one supported MCP era with a resource-bound MCPHub OAuth token
- **THEN** it SHALL receive the same frozen 70-tool union subject to granted `things.read`, `things.write`, and `things.admin` scopes
- **AND** it SHALL NOT use a ChatGPT-specific group, direct server endpoint, or generic tunnel group.

#### Scenario: Remote listener modes are promoted

- **WHEN** remote work is separately authorized and S4-02 follows a passing offline-conformance receipt plus fresh fixed-bridge and noninteractive-TCC proof
- **THEN** its first `46684` bind SHALL be capture-only and unable to dispatch Things tools
- **AND** only S4-04, after capture shutdown and a matching content/config/route-manifest-bound final activation receipt, SHALL perform the first production/public `46684` bind.

#### Scenario: The two eras enumerate tools

- **WHEN** a `2026-07-28` client calls modern `tools/list` and a `2025-11-25` client calls legacy `tools/list`
- **THEN** transport envelopes MAY differ as specified
- **AND** the ordered normalized tool objects, names, adapted input/output schema hashes, annotations, and scope map SHALL be identical and exactly 70
- **AND** no transport-era change SHALL rewrite the adapted-public hashes in `capability-manifest.json`.

### Requirement: The harness boundary is dual-era and stateless

The Things endpoint SHALL implement current MCP `2026-07-28` and stateless legacy MCP `2025-11-25` only. Modern clients SHALL use `server/discover` plus matching protocol/method/name headers and per-request body metadata; legacy clients SHALL use `initialize`. Neither era SHALL create an MCP session.

#### Scenario: Modern ChatGPT wire shape is supported

- **WHEN** ChatGPT sends a valid `2026-07-28` request with matching `MCP-Protocol-Version`, `Mcp-Method`, required `Mcp-Name`, protocol body metadata, and client capabilities
- **THEN** the edge SHALL select modern dispatch and return the modern response envelope
- **AND** SHALL NOT invoke legacy initialization or fallback.

#### Scenario: Legacy ChatGPT wire shape is supported

- **WHEN** ChatGPT sends a valid `initialize` selecting `2025-11-25`
- **THEN** the edge SHALL use stateless legacy dispatch
- **AND** SHALL NOT mint, require, persist, or echo `Mcp-Session-Id`.

#### Scenario: A non-streaming method is probed

- **WHEN** an authenticated client sends canonical `GET /mcp/things` or `DELETE /mcp/things`
- **THEN** the endpoint SHALL return `405`, with `Allow: POST` on GET
- **AND** it SHALL NOT expose standalone SSE or MCP session termination.

### Requirement: Authentication does not replace mutation approval

OAuth consent SHALL authorize access but SHALL NOT waive tool annotations, `things-manager` preview/confirmation, or per-call approval for destructive/high-risk operations.

#### Scenario: An authenticated caller requests a destructive operation

- **GIVEN** the token includes the required scope
- **WHEN** the caller requests immediate deletion, trash emptying, tag/area deletion, bulk mutation, or maintenance
- **THEN** the client/tool policy SHALL still require the applicable explicit confirmation
- **AND** the operation SHALL return a structured verification receipt.

#### Scenario: Quick Entry is approved as a UI handoff

- **WHEN** an authenticated caller approves `create_todo_with_quick_entry`
- **THEN** the tool SHALL open only the fixed Things Quick Entry handoff, SHALL NOT target a heading, and SHALL return no changed item before the user saves
- **AND** it SHALL be exempt from execute/readback mutation receipts without weakening UI approval.

### Requirement: ChatGPT UI state is evidence gated

The repository SHALL provide a Things++ ChatGPT setup bundle, but SHALL claim app or Project creation only after authenticated UI creation and readback are observed.

The current continuation explicitly authorizes remote connector implementation and restricted apply. It SHALL still claim ChatGPT app/Project UI state only from authenticated UI readback; missing bridge/TCC, observed-wire, or UI evidence SHALL be reported as blocked for that exact layer and SHALL keep dependent activation gates fail closed.

#### Scenario: UI access or OAuth conformance is unavailable

- **WHEN** source/package validation succeeds but the external UI or remote auth gate is unavailable
- **THEN** the handoff SHALL provide exact manual setup and test steps
- **AND** SHALL label app/Project creation and authenticated readback as not run or blocked.

### Requirement: ChatGPT grants the exact independent scope set

The Things ChatGPT profile SHALL grant exactly the independent Things authorization scopes `things.read`, `things.write`, and `things.admin` before modern catalog discovery or legacy initialization; no Things scope implies another, and every tool still enforces its manifest minimum scope independently on `tools/call`. For durable connectivity the profile SHALL additionally request `offline_access` solely to permit refresh-token issuance. `offline_access` SHALL NOT be represented as a Things authorization scope, imply any Things scope, widen catalog/tool access, or satisfy a tool's minimum scope.

#### Scenario: One scope is missing or an extra scope is requested

- **WHEN** ChatGPT attempts modern catalog discovery or legacy initialization without the exact three Things-scope set, or requests any scope other than those three plus the distinct `offline_access` refresh capability
- **THEN** catalog access SHALL fail without returning a partial tool subset
- **AND** remote and local clients SHALL expose the identical 70-tool set only after their own credential class succeeds.

#### Scenario: Durable connectivity requests offline access

- **WHEN** ChatGPT requests `offline_access` alongside the exact three Things scopes
- **THEN** the server SHALL issue and rotate a refresh token under the bounded refresh-family policy
- **AND** MCP `AuthInfo` and every catalog/tool authorization decision SHALL remain bound only to the exact independent Things scopes.

### Requirement: CIMD is primary and DCR is a strict observed fallback

MCPHub built-in OAuth SHALL use an approved HTTPS Client ID Metadata Document as the primary ChatGPT identity and SHALL permit DCR only when the observed user-owned ChatGPT configuration selects it. Under a confirmed RFC 9207 issuer configuration, the documented stable client metadata URL is `https://chatgpt.com/oauth/client.json` and the documented callback is `https://chatgpt.com/connector_platform_oauth_redirect`; these values SHALL remain approval/readback facts rather than source-only assumptions. Login/session flows SHALL use a `__Host-` Secure/HttpOnly/SameSite cookie, rotate the session ID after login, require one-time session-bound CSRF plus exact Origin and redirect checks, and apply persistent endpoint-specific rate limits.

#### Scenario: The callback is not yet approved

- **WHEN** the observed callback/registration mode is absent from the user-owned allowlist or client metadata/redirect differs
- **THEN** CIMD validation or fallback registration and remote activation SHALL remain disabled
- **AND** no wildcard, loopback/private, insecure, custom-scheme, fragment, or userinfo redirect SHALL be accepted.

#### Scenario: CIMD client authentication is verified

- **WHEN** the approved metadata selects `none` or `private_key_jwt`
- **THEN** PKCE S256, exact resource, issuer, metadata subject, and callback SHALL remain bound through exchange
- **AND** `private_key_jwt` SHALL verify the approved JWKS and issuer/subject/audience/time/JTI claims with one-time hashed-JTI replay prevention
- **AND** CIMD SHALL NOT create or persist a client secret.

#### Scenario: RFC 9207 issuer identification is incomplete

- **WHEN** protected-resource metadata, authorization-server metadata, or the authorization success/error response omits or disagrees on the exact issuer
- **THEN** authorization SHALL fail before a usable code or token is issued
- **AND** the server SHALL NOT infer issuer identity from redirects or caller-controlled headers.

### Requirement: Documented support and observed ChatGPT wire facts remain distinct

Repository evidence SHALL distinguish official documented requirements from observed current client behavior. Official OpenAI documentation establishes public Streamable HTTP, OAuth 2.1, PKCE S256/resource checks, CIMD/DCR/pre-registration support, and RFC 9207 behavior; it does not establish the MCP protocol version/header shape ChatGPT currently emits.

#### Scenario: Only documented client behavior is available

- **WHEN** hermetic dual-era and OAuth conformance passes but no current redacted ChatGPT wire capture and app readback exists
- **THEN** source validation MAY be reported as passed
- **AND** remote activation, app creation, Project creation, and authenticated readback SHALL remain disabled, not run, or blocked as applicable.

#### Scenario: Observed-wire evidence enables remote readiness

- **WHEN** a redacted current run produces closed v1.1 `observed-pass` evidence for one supported era, approved registration mode/callback, issuer/resource binding, exact three independent Things scopes plus refresh-only `offline_access`, capture/callback/internal digests, fixed capture-route statuses, and normalized 70-tool catalog
- **THEN** its digest MAY enter the build-specific activation receipt
- **AND** remote enablement SHALL still require every other receipt digest, `noSecrets: true`, verified redactions/prohibited-data absence, passing status, and unexpired evidence to match
- **AND** capture evidence alone SHALL NOT be reported as an observed production OAuth exchange, ChatGPT Scan Tools result, or authenticated UI readback.

### Requirement: Production uses one content-addressed same-process MCPHub downstream

The OpenAI-facing endpoint and MCPHub built-in OAuth SHALL run in one immutable downstream process materialized from exact npm tarball, dependency lock, owned-source/patch manifest, and output digests. Production SHALL NOT use a runtime loader, live patch, `npx`, range resolution, mutable cache, external OAuth facade, or external identity provider.

#### Scenario: Runtime or conformance identity changes

- **WHEN** the downstream content ID, protocol codec, route/group policy, OAuth/client policy, settings, normalized catalog, observed-wire evidence, or conformance result differs from its stamp
- **THEN** remote listener publication and tunnel enablement SHALL fail closed
- **AND** local bearer access SHALL remain a separate credential class on `127.0.0.1:46683` without creating a second Things group.
