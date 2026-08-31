# Things++ App Setup Reference

This is a secret-free operator reference. It does not create a ChatGPT app,
change ChatGPT UI state, enable remote access, or authorize a Things mutation.
Remote implementation/apply is explicitly authorized, while the checked-in
posture keeps remote ingress disabled and remains fail closed until its live
prerequisites and activation receipt pass.

## One endpoint contract

Use only the MCPHub `things` group at the exact `/mcp/things` endpoint.

- Current local bearer resource: `http://127.0.0.1:46683/mcp/things`
- Authorized public OAuth target, currently gated: `https://mcp.w4w.dev/mcp/things`
- Catalog closure: exactly 70 qualified tools from 41 core, 21 fixed
  Shortcuts, and 8 fixed native operations

Do not register an individual backend, a generic MCPHub route, Smart Routing,
an alias, or an administrative group. The future public resource preserves the
same endpoint path; it does not introduce a second Things endpoint.

## Manual prerequisites

Before local catalog discovery and unaffected core read-only assurance, an
operator must verify all of the following:

1. Things 3 is installed on the Mac that owns the private Things library.
2. MCPHub is configured from the repository registry and is listening only on
   loopback port 46683 in local-only mode.
3. The `things-core`, `things-shortcuts`, and `things-native` servers appear
   only as internal members of the one `things` group.
4. A bearer token is present in the process environment or the local secret
   file expected by MCPHub. Never paste, log, commit, or copy its value into
   this bundle or ChatGPT Project instructions.
5. Before the authorized S4 sequence reaches its verified production gate,
   remote mode and the Cloudflare tunnel remain disabled, port 46684 is not
   listening, and this reference has not created a public connector.

The fixed Things++ Shortcuts and the required Shortcuts, Automation,
Accessibility, or TCC permissions are prerequisites only for affected bridge
or native operations and for any future remote activation. When one is absent,
the exact 70-tool schema remains discoverable and unaffected core reads may
proceed, but each affected call must return a typed unavailable/degraded result.
It must not activate arbitrary Shortcuts, AppleScript, shell, raw URLs, direct
database access, or UI automation.

## Local refresh and test

1. Reconcile the repository registry into MCPHub and verify that only the
   `things` group owns Things-related client routing.
2. Start MCPHub with its local-only wrapper. Keep remote mode and tunnel
   settings disabled.
3. Run the repository MCPHub doctor and smoke checks.
4. Discover tools through the local bearer resource and require exactly 70
   unique qualified names with the 41/21/8 backend partition.
5. Run the read-only cases in `TEST_PROMPTS.md`. Do not confirm mutation
   previews during assurance.
6. If a client cached an older catalog, refresh that connection only after the
   server-side 70-tool closure passes. Recheck the count and route after the
   refresh; a successful refresh is not proof that a ChatGPT UI was created.

Do not mark local assurance complete from configuration files alone. Record
source validation, generated-config validation, listener/process evidence,
tool discovery, and bounded read-only behavior as separate proof layers.

## Authorized OAuth rollout

Remote implementation and restricted apply are authorized. They proceed only
in the specified gate order; a current redacted observed-wire run, bridge/TCC
readiness, authenticated UI access, and the content/config/route-manifest-bound
activation receipt remain evidence requirements rather than authorization
questions.

When those gates are satisfied:

1. Keep Client ID Metadata Documents as the primary registration mode. Permit
   Dynamic Client Registration only if the observed flow selects it.
2. Approve the exact observed callback; checked-in candidate URLs are not
   approval.
3. Require PKCE `S256`, RFC 8707 resource binding to the exact public resource,
   RFC 9207 authorization-response issuer binding, and the independent scopes
   `things.read`, `things.write`, and `things.admin`.
   Require `offline_access` for the durable ChatGPT profile only as its
   refresh-token capability. It is not a Things authorization scope, grants no
   read/write/admin access, and never satisfies a tool's minimum scope.
4. Require an unexpired activation receipt bound to source/runtime content,
   configuration, route manifest, callback, scope, protocol, and observed-wire
   digests before enabling ingress.
5. Enable the public listener and tunnel only for the approved resource. Then
   refresh and inspect the ChatGPT connection manually, requiring the same 70
   qualified tools and no alternate Things route.

The restricted capture listener can establish a redacted client-registration
candidate and wire shape. It does not prove a production OAuth exchange,
refresh-token rotation, ChatGPT **Scan Tools** success, or authenticated UI
catalog readback; record each of those only from its own observed gate.

The finalized public evidence must validate against
`observed-wire-record.schema.json` v1.1 with `status: observed-pass`. It binds
RFC 3339 capture/expiry times, the capture receipt and callback digests, exact
resource/callback/registration/protocol facts, exact independent Things scopes,
refresh-only `offline_access`, PKCE S256, discovery, and the closed capture-route
status map. Recompute `evidenceDigestSha256` from canonical JSON with that one
field omitted. Reject any additional/free-form field and any cookie, token,
authorization code, verifier, state, private Things content, or account
identifier. Keep the capture runtime and receipt at or below 30 minutes. The
finalized evidence must bind that receipt and a `capturedAt` inside its window;
its separate freshness `expiresAt` may outlive capture but must be no more than
24 hours after `capturedAt`.

OAuth permission never replaces user confirmation, mutation receipts, or
read-after-write verification.

## Account and workspace limits

ChatGPT app availability, developer controls, OAuth registration behavior,
write-tool access, and administrator approval can differ by account and
workspace. Verify the current user-owned ChatGPT UI and workspace policy before
starting connector setup. If the required controls, tool scan, or
administrator approval are unavailable, keep remote access disabled and use
the local bearer route only. Never infer availability from this reference or
claim that an app or Project exists without direct UI readback.

## Emergency disable

If any route, catalog, OAuth, callback, evidence, prerequisite, or privacy
check fails:

1. Disable the tunnel and remote mode immediately.
2. Stop the remote OAuth listener on port 46684 and leave the local bearer
   listener bound to loopback only if local work is still approved.
3. Disable remote tool dispatch and revoke any affected short-lived grant or
   token through its owning control plane. Never record the credential value.
4. Confirm that the public resource is unreachable, port 46684 is closed, and
   the one local `things` route has not changed.
5. Preserve only redacted diagnostics and require a fresh conformance and
   activation-receipt run before any re-enable attempt.

Emergency disable is fail-closed. Never fall back to another endpoint, direct
backend, bearer query parameter, forwarded identity header, or weaker parser.
