# Things++ ChatGPT Reference Bundle

This directory is the secret-free, static operator bundle for the Things++
MCPHub group. It documents local verification and the explicitly authorized
remote implementation/apply sequence. It does not by itself create an app,
install a connector, enable a tunnel, approve a callback, or mutate Things.

Current checked-in observation status: `not-observed`. Remote work is
authorized, but checked-in evidence still requires remote ingress and tool
dispatch to remain disabled until the receipt, bridge/TCC, observed-wire, and
route gates pass.

## Fixed topology

- App name: `Things++`
- MCPHub group: `things`
- Current local bearer resource: `http://127.0.0.1:46683/mcp/things`
- Authorized public OAuth target, currently gated: `https://mcp.w4w.dev/mcp/things`
- Authorized remote OAuth loopback origin, currently gated: `http://127.0.0.1:46684/mcp/things`
- Catalog: exactly 70 tools: 41 core, 21 fixed Shortcuts bridges, and 8 fixed
  native operations

Every Things client uses the one `things` group. There is no direct backend,
generic-group, smart-routing, compatibility-alias, or alternate public route.

## Bundle map

| File | Purpose | Ownership |
|---|---|---|
| `README.md` | Bundle status, topology, inventory, and validation entrypoint | Hand-authored |
| `APP_SETUP.md` | Local setup, authorized OAuth gates, refresh/test flow, emergency disable, and manual prerequisites | Hand-authored |
| `registration-reference.json` | Machine-readable, non-secret registration and activation contract | Hand-authored |
| `PROJECT_INSTRUCTIONS.md` | Copy-ready behavioral policy for a future ChatGPT Project | Hand-authored |
| `SAFETY.md` | Privacy, approval, routing, and failure-mode rules | Hand-authored |
| `TEST_PROMPTS.md` | Bounded acceptance prompts and expected results | Hand-authored |
| `observed-wire-record.template.json` | Fail-closed shape for a later redacted observation | Hand-authored template; never evidence by itself |
| `CAPABILITY_MATRIX.md` | Exact generated 70-tool capability copy | Generated from the Things Manager ledger at the serialized docs barrier |

Do not hand-edit `CAPABILITY_MATRIX.md`. Its source is
`skills/things-manager/references/capabilities.md`, rendered by
`skills/things-manager/scripts/render_capabilities.py`.

## Registration sequence

1. Complete source, offline conformance, local runtime, and read-only catalog
   gates while public ingress remains disabled.
2. Use only the restricted capture listener and short-lived capture tunnel
   defined by the implementation plan. Things tool dispatch stays disabled.
3. Record the current ChatGPT registration mode, callback, and MCP wire shape in
   a separate redacted evidence artifact. The checked-in template is never a
   passing record. A passing v1.1 record binds its capture-receipt and callback
   digests, exact Things scope set, refresh-only `offline_access` request,
   resource indicator, PKCE S256, protocol/discovery result, and closed route
   statuses. Its canonical internal digest omits only the digest field itself;
   the closed record admits no cookie, token, code, verifier, state, account
   identifier, or free-form notes. The capture runtime/receipt remains bounded
   to 30 minutes; finalized evidence binds that receipt and a capture time
   inside its window, then may remain fresh for at most 24 hours.
4. Prefer Client ID Metadata Documents (CIMD). Permit Dynamic Client
   Registration (DCR) only if the current observed flow selects it.
5. Require PKCE `S256`, the exact resource indicator
   `https://mcp.w4w.dev/mcp/things`, RFC 9207 issuer binding, and the independent
   Things authorization scopes `things.read`, `things.write`, and
   `things.admin`. The durable ChatGPT profile also requires `offline_access`
   only as the capability that permits refresh-token issuance; it grants no
   Things permission, implies none of the three Things scopes, and cannot
   satisfy any tool's minimum scope.
6. Bind the approved observation and every source/runtime digest into an
   unexpired final activation receipt.
7. Create or configure the ChatGPT app and enable durable public ingress only
   within the authorized rollout and after every activation gate passes. This
   static bundle performs neither step.

The documented ChatGPT CIMD client ID and web redirect in
`registration-reference.json` are candidates until a current, redacted
observed-wire run confirms them. They are not an assertion about installed UI
state or proof that the activation gates passed.

## Validation

Validate the hand-authored bundle without requiring the later generated ledger:

```bash
uv run python platforms/chatgpt/things-plus-plus/validate_bundle.py
```

After the serialized capability render, require the exact generated copy too:

```bash
uv run python platforms/chatgpt/things-plus-plus/validate_bundle.py --require-generated-capabilities
```

Run `TEST_PROMPTS.md` only after the corresponding runtime gate. Mutation
examples stop at preview unless the user separately confirms the exact bounded
change.

## Primary references

- [Connect from ChatGPT](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [Plugin authentication](https://developers.openai.com/plugins/build/auth)
- [Build plugins](https://developers.openai.com/plugins/build/plugins)
- [MCP 2026-07-28 specification](https://modelcontextprotocol.io/specification/2026-07-28)
- [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
