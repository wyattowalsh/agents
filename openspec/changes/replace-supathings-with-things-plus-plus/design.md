# Design

## Approach

Use MCPHub composition rather than replacing one monolith with another. Three narrowly owned internal servers provide the full Things domain; one group is the only client-facing router; `things-manager` provides portable reasoning and safety semantics; existing registry/sync/plugin/docs machinery remains authoritative. A repository-owned, content-addressed MCPHub downstream supplies one same-process dual-era HTTP edge: current stateless MCP `2026-07-28` and stateless legacy MCP `2025-11-25` normalize to the same frozen 70-tool catalog.

```text
Codex ── loopback bearer ─┐
                         ├─ MCPHub /mcp/things ─┬─ things-core (41)
ChatGPT ─ built-in OAuth ┘                     ├─ things-shortcuts (21)
                                               └─ things-native (8)
```

The group topology is a hard invariant, not a documentation convention:

- group name: `things`
- deterministic group ID: `3b94a096-b95f-586c-b2e7-e69ed177eb5a`
- local resource: `http://127.0.0.1:46683/mcp/things`
- remote resource/audience: `https://mcp.w4w.dev/mcp/things`
- members: only `things-core`, `things-shortcuts`, `things-native`
- union: exactly 70 unique qualified capability IDs, with explicit per-server allowlists and public names frozen by `capability-manifest.json`
- prohibited: `things-chatgpt`, `things-admin`, nested groups, wildcard allowlists, generic-group Things membership, enabled individual Things routes, `/mcp/tunnel`, and a second public Things path

## Capability Contract

### `things-core` — 41 audited upstream tools

Pin `mcp-server-things==1.9.0` and its accepted distributions/hashes. The adapter preserves all 41 upstream Things outcomes while adding typed boundaries, accurate annotations/security schemes, maximum batch sizes, write serialization, idempotency/retry discipline, read-after-write receipts, and content/secret/path/URL redaction.

The frozen upstream provenance is exact: wheel SHA-256 `720f27aaabe76c3daddd2d92d4fd15bed0111b9eb390dca4b56284f950b9ce2c`, sdist SHA-256 `99a6f630a0b80fe12a95ccf36a727b1dbc667ce60a6cc30ad1d391f4071e9bd0`, installed `RECORD` SHA-256 `e44727b7595a2b618118a060e5871e02065999152404055c68301613e49a1be7`, and `48/48` verified `RECORD` entries. A read-only FastMCP `list_tools` inspection of the cached extracted wheel produced ordered-name SHA-256 `6e7d22b09f4966cde99954cb37f7e5ce4566adab9d9733b75afa1ead7580efd4`, sorted-name SHA-256 `4208486cfdd749c791586ef4158e63b5fbdefcecff91cb110f6cdafe9dba8f89`, 41 row-specific input-schema hashes, and common upstream output-schema SHA-256 `82ef96cebaf5fbe16269fd18b0240d78f5b9b90a4155a17eb797115b09148ecf`. The manifest stores these audited upstream hashes separately from the adapted public schema hashes that implementation and authenticated local/remote `tools/list` must later populate and prove.

The frozen logical IDs are:

```text
things-core/add_area
things-core/add_checklist_items
things-core/add_project
things-core/add_tags
things-core/add_todo
things-core/bulk_move_records
things-core/bulk_update_todos
things-core/context_stats
things-core/create_tag
things-core/delete_todo
things-core/get_activating_in_days
things-core/get_anytime
things-core/get_areas
things-core/get_due_in_days
things-core/get_inbox
things-core/get_logbook
things-core/get_project_headings
things-core/get_projects
things-core/get_recent
things-core/get_server_capabilities
things-core/get_someday
things-core/get_tag_usage
things-core/get_tagged_items
things-core/get_tags
things-core/get_today
things-core/get_todo_by_id
things-core/get_todos
things-core/get_trash
things-core/get_upcoming
things-core/get_usage_recommendations
things-core/health_check
things-core/move_record
things-core/prepend_checklist_items
things-core/queue_status
things-core/remove_tags
things-core/replace_checklist_items
things-core/search_advanced
things-core/search_todos
things-core/update_area
things-core/update_project
things-core/update_todo
```

The five diagnostic/operational tools remain in the full union to avoid contraction, but their outputs are schema-bounded and redacted. None may expose task content, auth tokens, Things URLs, local paths, environment values, process arguments, or server configuration.

The launch wrapper selects the `mcp-things-core` workspace package from the repository's frozen lock with offline, no-sync execution; it never resolves a range, downloads at launch, or bypasses the workspace with `uvx`, `--with`, `--isolated`, or `--no-project`. It verifies the exact upstream package version and distribution hashes and fails closed on a mismatched pin. If `~/.things-auth` exists, it must be a current-user-owned non-symlink regular file with mode `0600`; its value is never logged or written to tracked config. The adapter is not a CRUD fork and never reaches SQLite directly.

### `things-shortcuts` — 21 fixed typed tools

Expose exactly:

```text
things-shortcuts/shortcuts_health
things-shortcuts/create_todo
things-shortcuts/create_todos
things-shortcuts/create_todo_with_quick_entry
things-shortcuts/create_heading
things-shortcuts/create_project
things-shortcuts/create_structured_project
things-shortcuts/find_items
things-shortcuts/get_items
things-shortcuts/get_selected_items
things-shortcuts/edit_items
things-shortcuts/edit_heading
things-shortcuts/edit_checklist
things-shortcuts/append_checklist
things-shortcuts/prepend_checklist
things-shortcuts/duplicate_items
things-shortcuts/delete_items
things-shortcuts/delete_items_immediately
things-shortcuts/delete_heading
things-shortcuts/open_list
things-shortcuts/show_items
```

`create_todos` is bounded to 25 closed item models and returns a per-item structured receipt. `create_structured_project`, `edit_items`, and `duplicate_items` are bulk writes; `edit_items` is explicitly non-undoable. A `delete_heading` preview must include the number of children affected by the cascade. `create_todo_with_quick_entry` is a `ui_handoff`: it requires UI approval, cannot target a heading, and returns no changed item until the user saves in Things. Because the server itself does not perform or verify that user-completed mutation, this handoff is exempt from the execute/readback mutation-receipt protocol.

The server invokes only the fixed `Things++ Agent Bridge` and `Things++ Destructive Bridge` names owned by the implementation; neither a tool argument nor retrieved Things content can select a Shortcut. Requests and responses use `0600` temporary files, fixed encodings/output types, bounded subprocess timeouts, cleanup on every path, content-free logs, and structured errors. The F0 observation found both fixed bridges absent and TCC readiness unproven. Source implementation may proceed, but live activation cannot proceed until both bridges and noninteractive TCC readiness are freshly proven. Health and read operations must truthfully report an absent bridge or TCC denial. No uncontrolled UI automation constructs/imports a Shortcut.

### `things-native` — 8 fixed official native outcomes

Expose exactly:

```text
things-native/native_health
things-native/open_search
things-native/log_completed
things-native/empty_trash
things-native/delete_area
things-native/rename_tag
things-native/delete_tag
things-native/set_tag_parent
```

`native_health` is a static readiness tool and performs no AppleEvent. `open_search` is the sole URL-scheme operation: repository code builds the fixed `things:///search` URL and internally encodes the caller's query; callers cannot provide a URL. The other six operations select repository-owned static/fixed AppleScript templates and validate IDs/arguments against closed Pydantic models. In v1, `set_tag_parent` assigns a parent only; detach/null is unsupported until synthetic and separately authorized manual proof establishes its semantics. A `delete_area` preview must include the number of child items affected by the cascade. `delete_area`, `delete_tag`, `empty_trash`, and maintenance operations carry destructive annotations and confirmation policy. No arbitrary AppleScript source, command fragment, raw URL, filesystem path, shell, SQL, or generic UI action is accepted.

### Coverage closure

The canonical capability ledger uses stable outcome IDs and records baseline route, target route, safety class, live prerequisites, test IDs, and status. The migration gate requires:

- every one of the 37 SupaThings tools to be `implemented`, `safe-replacement`, or `semantic-skill`, with no `removed` row;
- all 17 skill workflows—Intake, Quick Capture, Inbox Triage, Today Planning, Weekly Review, Project Planning, Project Structuring, Task Placement, Project Summary, Tag Taxonomy Audit, Deadline And Reminder Review, Quick Entry Handoff, UI Handoff, Search And Audit, Cleanup, Bulk Update With Approval, and Read-Only Report—to retain a tested route;
- every one of the 25 legacy eval concepts to survive as a rewritten v2 case;
- an exact qualified union of 70 and a positive net-new outcome delta. Any future tool, name, schema, mapping, or count change requires revision of this active OpenSpec change before regeneration or activation.

SupaThings outcome mapping is frozen as follows:

| SupaThings outcome(s) | Things++ route |
|---|---|
| `app-status`, `version` | `things-native/native_health` |
| `get-areas`, `get-tags`, `get-projects`, `get-headings`, `get-todos` | corresponding `things-core/get_*` tools |
| `get-inbox`, `get-today`, `get-upcoming`, `get-anytime`, `get-someday`, `get-logbook`, `get-trash`, `get-tagged-items`, `get-recent` | corresponding core views |
| `search-todos`, `search-advanced` | corresponding core search tools |
| `search-items` | typed `things-shortcuts/find_items` with core lookup fallback only where schemas are equivalent |
| `get-project-structure`, `suggest-headings`, `validate-headings`, `suggest-task-placement`, `summarize-project` | `things-manager` semantic workflows over core reads |
| `add-todo`, `add-project`, `update-project`, `update-todo` | corresponding core writes |
| generic `update` | typed core `update_todo`, `update_project`, or `update_area`; no generic passthrough |
| `create-project-with-headings`, raw `json` structured creation | `things-shortcuts/create_structured_project`; no raw JSON/URL input |
| `show`, `show-item` | typed `open_list`/`show_items` |
| UI `search` | fixed `things-native/open_search` |
| `show-quick-entry` | `things-shortcuts/create_todo_with_quick_entry` |
| `log-completed`, `empty-trash` | fixed native operations |

Net-new coverage includes bounded multi-create, selected-item inspection, item duplication, checklist variants, safe immediate deletion, area creation/update/deletion, and tag creation/rename/delete/hierarchy management. Recurrence editing and deterministic positional reordering are reported as unsupported because no audited backend provides them; they were not SupaThings capabilities and do not count as regressions.

## Data And Control Flow

1. Every client uses only `/mcp/things`. A current `2026-07-28` client uses `server/discover` and per-request metadata; a legacy `2025-11-25` client uses `initialize`. The edge selects one era structurally, expands the same explicit three-member allowlists, and returns the same 70 unique normalized tool definitions.
2. The `things-manager` skill classifies the request as read-only, `ui_handoff`, UI-visible, single-write, bulk-write, or destructive; treats retrieved Things content as untrusted private data; and chooses core first unless a documented gap requires Shortcuts/native.
3. Reads are minimal and bounded. Writes re-read IDs/state, serialize across all backends, show the required preview/confirmation, invoke one typed operation, then return changed/skipped/failed/ambiguous plus read-after-write evidence. Quick Entry is the explicit exception: it returns handoff status rather than a changed item until the user saves.
4. The adapter/server redacts before logs or errors cross the MCP boundary. Capability and eval fixtures contain synthetic data only.
5. Local clients authenticate with the current loopback bearer. Remote ChatGPT authenticates to the same group through built-in MCPHub OAuth and requests `things.read`, `things.write`, and `things.admin`; each tool declares its minimum scope.
6. Destructive and high-risk tools remain subject to per-call client approval and MCP annotations even after OAuth consent. Authentication is not mutation approval.

### Public names, collisions, and schema identity

`capability-manifest.json` is the exact source inventory. Public names use `normalize(server) + "__" + serverToolName`, where normalization replaces the server ID's hyphens with underscores. Thus `things-core/add_area` is exposed as `things_core__add_area`. Generation and startup fail on a duplicate public name, duplicate qualified capability ID, a server tool name containing `__`, an unmanifested name, a missing name, or an alias. Calls reverse-map one exact public name to one exact server/tool pair; there is no guessing or fallback.

For every row, the validator canonicalizes the source `inputSchema` and `outputSchema` as UTF-8 JSON with sorted keys and compact separators, then stores/compares SHA-256 values. Audited upstream and future adapted-public hashes remain separate fields. Authenticated local and remote `tools/list` must match the manifest's exact public-name set and the adapted input/output schema hashes. Cross-era comparison removes only transport-envelope fields, then proves byte-canonical equality of the ordered 70 tool objects; the modern `resultType`, `ttlMs`, and `cacheScope` envelope does not alter any tool definition. A count-only check cannot pass. Any future tool name, schema, mapping, or count change requires an explicit OpenSpec revision before regeneration or activation. This change SHALL NOT rewrite the capability manifest's adapted-public hashes merely to accommodate a transport era.

### Shared state, lock, and two-phase mutation receipts

Add `packages/things-common` as a non-server library imported by exactly three backends. It owns:

- a per-user runtime root under the Darwin user temporary directory, created mode `0700`, owner-checked, non-symlink, and opened with `O_NOFOLLOW`; state files are mode `0600` and rechecked with `fstat` plus device/inode comparison before use;
- an opaque-receipt store, redaction/canonicalization helpers, artifact-hash verification, and one owner-checked non-symlink advisory lock shared across core, Shortcuts, and native writes;
- crash recovery that expires abandoned reservations and reports an `ambiguous` execution for verification instead of retrying an unknown write.

Every server-executed mutating tool retains its existing public name and closed domain fields but adds a common envelope: `mutationPhase` (`preview` or `execute`) and optional `mutationReceipt`. Preview acquires the shared transaction lock, freshly reads targets, canonicalizes arguments and scope, and issues a cryptographically random 256-bit opaque receipt with a five-minute TTL. The stored record contains only the receipt hash and is atomically bound to principal, client ID, exact resource, tool, target IDs, canonical argument hash, fresh-state hash, and the one independent minimum scope. `create_todo_with_quick_entry` is exempt because it only opens a user-controlled UI handoff and cannot provide execute/readback proof; its UI approval and truthful no-changed-item response remain mandatory.

The issued receipt creates a transaction reservation: no other Things++ mutation passes the shared lock until that receipt is consumed, expires, or is explicitly abandoned. Execute must use the same principal/client/resource/tool/targets/arguments/scope, atomically moves the receipt from `issued` to `executing`, rechecks target state inside the reservation, performs the backend action, verifies with a fresh read, and seals the record `consumed` with a content-free receipt. Preview reread, execute, and verification are therefore one serializable critical section across all three backends. Replayed, expired, substituted, wrong-client, wrong-resource, wrong-tool, wrong-target, wrong-argument, wrong-scope, or stale-state receipts fail closed. A crash in `executing` never replays automatically; recovery verifies state and reports changed or ambiguous.

`~/.things-auth`, the core distribution, native scripts, and Shortcut protocol artifacts are opened/verified without following symlinks; credentials/runtime files use pre/post-read `fstat` and inode checks, and executable artifacts are hashed immediately before `exec`. The Shortcuts bridge performs an exact protocol-version plus request/response-schema-digest handshake before enabling its tools. Health checks use noninteractive probes and must not trigger a silent TCC prompt; missing TCC approval is a typed prerequisite failure with manual instructions.

## OAuth And Public Ingress

### Content-addressed dual-era MCPHub downstream

Production SHALL run a repository-owned MCPHub downstream built from the audited `@samanhappy/mcphub@1.0.32` tarball (tarball SHA-256 `4cb58d4cb11c7d036bde169504f0ddbe9849159e40fe764950ad62853d1502bb`, npm integrity `sha512-k0csMxsrZZOmh1Cef4WF/KGwFBtusJGPhCq5d1xTlhTfxy6qd61sGzU9ImoagquJZnnIaGp5SOWBv3xASNT5Tw==`) and a complete exact transitive lock. The public edge freezes `@modelcontextprotocol/server@2.0.0` and, when imported, `@modelcontextprotocol/node@2.0.0` and `@modelcontextprotocol/core@2.0.0`; the private MCPHub-to-backend client side isolates exact-locked `@modelcontextprotocol/sdk@1.29.0`. The modern packages SHALL NOT leak into legacy backend-client framing, and the legacy package SHALL NOT parse the public `2026-07-28` edge.

The downstream manifest binds the upstream tarball and signature evidence, complete dependency graph, owned sources, current deterministic build-time replacements or guarded patches, materialized output hashes, output-inventory receipt, aggregate digest receipt, and build command. The retrospective report of six whole-module replacements plus five guarded patches did not freeze entry identities or transformation evidence; it is non-authorizing historical context and is not a seal prerequisite. A fresh exact owned-source/patch inventory SHALL enumerate and digest every current production-loaded module and transformation before materialization. Materialization verifies every current input and anchor, builds in an isolated staging directory, verifies every output and receipt, and atomically publishes one immutable content ID. The production launcher resolves only that content ID and requires `productionLoaderTransformations: []`; it rejects `npx`, semver/range installation, a mutable npm cache, live patching, `--loader`, `--import`, `NODE_OPTIONS`, or any ESM load-hook path. OAuth, routing, and the dual-era edge remain in the same MCPHub process; this is not an external facade or identity provider.

### First-cutover failure and recovery boundary

The first selected downstream seal passed its byte, signature, dependency, materialization, and selection checks but failed its first operational startup before either loopback listener bound. MCPHub 1.0.32's parameterless `McpHubAppServer.initialize()` walks the complete configured `mcpServers` collection before request-time group routing; the provider session's `group: "things"` filters later `tools/list` and `tools/call` handling and is not a first-boot server allowlist. An unrelated preserved DeepWiki backend at `https://mcp.deepwiki.com/mcp` therefore ran URL preflight, resolved to public IPv4 `100.23.203.190`, and was falsely rejected by the upstream range table. The failure aborted global initialization and left the Things catalog unavailable. Rollback occurred before listener bind: the failed selection was removed/restored through the verified pointer/config path, no remote listener or tunnel was enabled, and the failed content remained evidence rather than an active fallback.

The upstream comment says `100.64.0.0/10`, but its inclusive numeric bounds are malformed: `[0x64000000, 0x657fffff]` denotes `100.0.0.0` through `101.127.255.255`. The only authorized correction is exact replacement with `[0x64400000, 0x647fffff]`, the actual RFC 6598 interval `100.64.0.0` through `100.127.255.255`. The build transformation is named `mcphub-ssrf-rfc6598-cgnat-range-v1`, applies only when upstream `dist/utils/ssrf.js` has SHA-256 `d7fc7ac44dd23e74f599538c1bb92e698f5280311cfa6ed7582695abdd423e0e` and the malformed anchor occurs exactly once, and emits an exact preimage/postimage event. It does not allow loopback, private, link-local, multicast, documentation, reserved, IPv6, redirect, DNS-rebinding, or correctly classified RFC 6598 addresses.

The second authorized correction is `mcphub-transport-construction-isolation-v1` against upstream `dist/services/mcpService.js` SHA-256 `e7a8f7d0b566ff4fb3988add3fa01bd7f6a058b0ad2e4fcdabc5ea5cd894f87e`. It wraps the existing awaited `createTransportFromConfig(name, expandedConf)` call inside the per-server initialization loop. A preflight or construction failure records only that server as enabled-but-`disconnected` with a sanitized error and empty tool/prompt/resource lists, then continues; it neither creates a transport nor dispatches a request for the rejected server. Wrong source SHA, missing/duplicate anchor, unexpected event count, or wrong postimage fails the build.

Both corrections are deterministic build-time transformations and must appear in the transform-event inventory, bundled-module inventory, materialized output inventory, audit manifest, and aggregate distribution digest. Production still requires `productionLoaderTransformations: []`; the launcher performs no correction, fallback, dynamic patch, or dual-form load. The canonical registry and generated/runtime settings preserve every unrelated server and group. DeepWiki is not removed, disabled, granted `allowInternal`, or moved into `things`; no Things server enters another group, and all Things list/call logic remains behind exactly one `things` group with the fixed `41 + 21 + 8 = 70` union. Because upstream provides no native group-scoped first-start API, the containment correction—not topology contraction—is what prevents one unrelated failed preflight from aborting Things startup.

The failed seal and every receipt derived from it are non-reusable after either correction. Recovery must: rebuild from the exact signed tarball and frozen lock; regenerate and validate all source/transform/output/attestation/digest artifacts; publish a new immutable digest; rematerialize it in an isolated owner-only root; run the tracked startup-scope/containment tests; run a no-bind preselection probe that neither changes `current` nor opens `46683`/`46684`; and only then perform a fresh local cutover followed by doctor, modern/legacy 70-tool closure, route negatives, bounded reads, and installed-client readback. The tracked pre-seal startup-scope suite is synthetic definition/branch containment only: it proves the transformed loop continues through the three Things backend names while preserving the complete registry/settings definition set, but it does not instantiate the real `McpHubAppServer`, exercise provider list/call, normalize 70 runtime tools, inspect listeners, or touch selection state. Those actual provider/no-bind claims first become admissible in S2-01A after a fresh seal. The no-bind fixture deliberately contains only the three Things servers and one `things` group so it can prove the sealed provider/session path without network or listener mutation; it does not prove parameterless MCPHub startup avoids unrelated preflights under the full reconciled settings. A no-bind receipt proves only its isolated layer and cannot be promoted to full-topology live, remote, or ChatGPT proof.

Nonreuse is mechanically enforced, not merely documented. `mcp/mcphub/downstream/src/materializer/revocations.mjs` freezes exactly the failed cutover digest `sha256-7369fbfd45eebe415500d41cbb9de5c55b2d95338932344ed09820d7e72a7262` and the historic quarantined digest `sha256-bda99d286dd44377d37a7c9500fea8d3f9005c426c59ce92b4a0018bebce0182`; invalid or duplicate registry entries fail module load. `scripts/mcphub/downstream-select.mjs` applies the shared assertion to explicit selection, the existing `current` pointer, and rollback receipt identities before it reads distribution bytes or writes/replaces a pointer or receipt. `mcp/mcphub/downstream/src/materializer/launch.mjs` validates and reads the owner-only `current` symlink, validates its exact digest basename, applies the same revocation assertion, and only then resolves the distribution directory or reads its manifest/files. There is no environment override, alias, fallback, or production-loader bypass. A newly sealed digest must not equal any registry entry.

The edge accepts exactly two request eras: modern `2026-07-28` and stateless legacy `2025-11-25`. A valid modern request carries `MCP-Protocol-Version: 2026-07-28`, matching `params._meta["io.modelcontextprotocol/protocolVersion"]`, `params._meta["io.modelcontextprotocol/clientCapabilities"]`, and the required `Mcp-Method`; name-bearing calls such as `tools/call` also carry the matching `Mcp-Name`. The JSON-RPC body is authoritative. Missing, malformed, or contradictory modern headers fail with HTTP `400` and JSON-RPC `-32020`; unsupported versions fail with HTTP `400` and `-32022`; missing required capabilities fail with `-32021`; and an unknown modern RPC fails with HTTP `404` and `-32601`. A valid legacy `initialize` structurally selects `2025-11-25`. A malformed modern request never falls back to legacy.

Modern `server/discover` reports exactly `supportedVersions: ["2026-07-28"]` plus the tools capability and cache metadata, matching the exact v2 SDK and current schema. Legacy `2025-11-25` remains available only through its structurally separate `initialize` compatibility lane and is never inserted into modern discovery. The conformance client always exercises `server/discover` before modern `tools/list`, but the stateless server does not retain or enforce a cross-request ordering prerequisite because discovery is optional at the protocol layer. Modern `tools/list` includes its required `resultType`, `ttlMs`, and `cacheScope`; legacy `tools/list` uses its legacy envelope; both normalize to the same deterministic 70 tool objects. The edge is stateless for both eras: it never mints, requires, persists, or echoes `Mcp-Session-Id`, never resumes from `Last-Event-ID`, and returns `405` for session-termination `DELETE`. A present invalid `Origin` fails with `403`. Modern and legacy transport state is distinct from the OAuth browser login session described below.

The current MCP and OpenAI documentation establishes the dual-era server contract, Streamable HTTP/OAuth requirements, and supported client-registration modes; it does not document which MCP version/header shape ChatGPT currently emits. Therefore remote exposure defaults disabled until a redacted observed-wire run proves one supported era without weakening either parser. Observations SHALL update evidence and conformance inputs, never silently add a third protocol, route, group, alias, or fallback.

### Credential-class separation

The two credential classes reach the same `things` group/path through distinct loopback listeners:

- local bearer-only origin: `http://127.0.0.1:46683/mcp/things`;
- remote OAuth-only ingress origin consumed exclusively by cloudflared: `http://127.0.0.1:46684/mcp/things`.

Listener availability is sequenced, not implied by topology. S3 local activation materializes and selects the audited runtime with remote mode disabled, binds only managed loopback `46683`, and proves that `46684`, cloudflared, and capture-receipt authorization are absent. The local endpoint advertises the frozen 70-tool schema/catalog even when a fixed Shortcut bridge is absent or TCC readiness is unproved; only an affected invocation degrades, returning a typed unavailable/manual-prerequisite result without raw execution, direct-database access, UI automation, or a false success claim. S4/F5/J5 and ChatGPT UI activation are now explicitly authorized but remain dependency- and evidence-gated. Passing offline conformance plus fresh bridge/TCC proof may authorize S4-02's first `46684` bind, which is loopback-only, short-lived, restricted to frozen handshake/registration paths, and unable to dispatch any Things tool. S4-03 may attach only the restricted capture tunnel and must stop both it and the capture listener after observation. Only S4-04's final content/config/route-manifest-bound activation receipt may authorize the first production/public `46684` bind and tool dispatch. No earlier gate may pre-bind, warm, or expose the remote listener.

The `46684` ingress adapter is a policy/transport adapter over MCPHub's built-in authorization and the existing `things` group; it is not another MCP group, CRUD server, authorization server, or identity provider. Listener identity is derived from the accepted socket, never `Host`, `Forwarded`, `X-Forwarded-*`, or other caller-controlled headers. The bearer listener accepts only the configured local bearer and rejects OAuth tokens; the remote listener accepts only opaque MCPHub OAuth access tokens and rejects the local bearer, dashboard JWTs, cookies as MCP credentials, and query/body credentials. Both listeners reject credential substitution, multiple Authorization values, comma-folded credentials, spoofed forwarding headers, and an origin/path mismatch. Cloudflared points only at `127.0.0.1:46684`.

### Opaque OAuth state and token model

The OAuth client supplies the protocol `state` value, which MCPHub validates and binds but does not misrepresent as server-generated entropy. MCPHub independently issues an at-least-256-bit random opaque authorization-transaction nonce/handle, authorization codes, access tokens, and refresh tokens; token contents carry no claims. Server-side records store only SHA-256 hashes of client state, the server nonce/handle, codes, and tokens. An authorization transaction and its state/nonce/code are one-time, atomically persisted, and bound to `client_id`, the exact approved redirect URI, S256 challenge, authenticated principal, exact resource `https://mcp.w4w.dev/mcp/things`, and the exact unordered scope set. Predictable client state never removes the independent server nonce/handle entropy.

The three Things authorization scopes are independent: `things.read`, `things.write`, and `things.admin` imply none of one another. The durable ChatGPT Things profile must obtain exactly all three plus the distinct `offline_access` refresh capability before modern catalog discovery or legacy initialization, so authenticated local and remote clients see the identical 70-tool set. `offline_access` is filtered out of MCP `AuthInfo`, grants no Things permission, and cannot satisfy any row's minimum independent scope on `tools/call`. Authorization transactions expire after 10 minutes, codes after 60 seconds, access tokens after 10 minutes, and refresh tokens have a 24-hour sliding and 30-day absolute expiry. Refresh rotation is atomic by family; replay of any consumed refresh token revokes the whole family. Access-token revocation takes immediate effect. Config/runtime rollback excludes the auth database, WAL, browser sessions, state/code/token rows, refresh families, dynamic-client records, client-secret hashes, and private-key-JWT replay state; rollback must never resurrect, copy backward, or replace that monotonic state.

### CIMD primary, strict DCR fallback, and issuer binding

Client ID Metadata Documents (CIMD) are the primary ChatGPT registration mode. When current documented OpenAI facts are confirmed by the user-owned app configuration, the client ID is exactly `https://chatgpt.com/oauth/client.json` and the callback is exactly `https://chatgpt.com/connector_platform_oauth_redirect`; both remain evidence-gated rather than assumed from documentation. The server fetches and validates the exact HTTPS metadata subject, accepted token-endpoint auth method, callback, and content digest under bounded cache rules. For `private_key_jwt`, it verifies the signature against the exact approved JWKS, issuer/subject/audience/time claims, and one-time JTI; only JTI hashes and public metadata digests persist. A `none` client remains PKCE-S256-bound and receives no secret.

Strict DCR remains a fallback only when the observed ChatGPT configuration selects it. DCR stores only a hash of any issued client secret and binds the registration to the approved metadata digest, exact web callback, principal, resource, and registration mode. DCR and CIMD cannot substitute identities within an authorization transaction. Authorization-server metadata sets `authorization_response_iss_parameter_supported` to true; protected-resource metadata and authorization-server metadata identify the same exact external issuer, and every successful or error authorization response returns the matching RFC 9207 `iss`. Issuer/resource mismatch fails before code issue or token exchange.

### Frozen ingress manifest

Cloudflare and the remote ingress adapter use this exact case-sensitive method/path allowlist; no implicit `HEAD`, wildcard asset, trailing-slash alias, or alternate method is allowed. The issuer-path well-known is the RFC 8414 insertion of `/.well-known/oauth-authorization-server` in front of the issuer path `/mcp/things`, not a trailing-slash alias:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Browser landing that names the public MCP resource |
| `POST` | `/mcp/things` | Streamable HTTP MCP |
| `GET` | `/mcp/things` | Authenticated Streamable HTTP capability check; exact `405` with `Allow: POST` because no standalone SSE stream exists |
| `GET` | `/.well-known/oauth-protected-resource/mcp/things` | Protected-resource metadata |
| `GET` | `/.well-known/oauth-authorization-server` | Authorization-server metadata |
| `GET` | `/.well-known/oauth-authorization-server/mcp/things` | RFC 8414 issuer-path authorization-server metadata |
| `GET` | `/oauth/authorize` | Authorization/consent form |
| `POST` | `/oauth/authorize` | Consent submission |
| `POST` | `/oauth/token` | Code/refresh exchange |
| `POST` | `/oauth/register` | Constrained DCR |
| `POST` | `/oauth/revoke` | Access/refresh revocation |
| `GET` | `/oauth/login` | Local-account login form |
| `POST` | `/oauth/login` | Local-account authentication |
| `POST` | `/oauth/session/logout` | Session termination |
| `GET` | `/oauth/assets/login.css` | One hash-pinned static asset |

Parsing decodes once using strict UTF-8 and rejects invalid encodings, encoded `/` or `\\`, double encoding, dot segments, repeated separators, semicolon parameters, NUL/control characters, unexpected trailing slashes, noncanonical percent case, or a normalized path different from the raw allowed form. Query parameters are denied except endpoint-specific OAuth parameters; duplicates and unknown security-sensitive parameters are rejected. Host/SNI must be `mcp.w4w.dev`. After its listener-specific credential gate succeeds, canonical `GET /mcp/things` returns exact `405` with `Allow: POST`, and canonical `DELETE /mcp/things` returns `405` without attempting MCP session termination. Every other method/path—including `/mcp`, direct `things-core`/`things-shortcuts`/`things-native` routes, `/$smart`, `/mcp/$smart`, `/mcp/tunnel`, alternate groups, encoded variants, and `/health`—terminates at the adapter/Cloudflare content-free `404` catch-all before MCPHub routing. The same negative matrix runs authenticated and unauthenticated against both local and remote listeners.

CIMD and fallback DCR accept only the exact observed ChatGPT callback URI recorded in a user-owned runtime allowlist; they reject wildcards, loopback/private/file/custom-scheme redirects, fragments, userinfo, insecure schemes, multiple callbacks, and mutable/unknown client metadata. Remote remains disabled until the user has approved the observed callback and registration mode. The login session cookie is `__Host-mcphub_things_session` with Secure, HttpOnly, SameSite=Lax, Path=/, and no Domain. Login/authorize forms require one-time session-bound CSRF plus exact Origin; successful login rotates the browser session identifier; redirects must equal the allowlist. Rate limits are persistent across process restart and fixed at five login attempts per account-and-IP per 15 minutes, ten registrations per IP per hour, and 30 token/authorize requests per client/session per minute; responses are content-free and do not reveal account existence.

The production launcher verifies the immutable downstream content ID and a digest-bound final activation receipt before it can bind the production `46684` listener or enable durable/public tool dispatch. To break the observation dependency without weakening this gate, a separate offline-conformance receipt may authorize one short-lived loopback-only capture listener on `46684` and a restricted capture tunnel. That mode has Things tool dispatch disabled, accepts only the handshake/registration paths needed for redacted observation, runs under a hard timeout, and is stopped before the final activation receipt is sealed. The final receipt binds the downstream output SHA, upstream npm audit/tarball/provenance SHA, full dependency-lock SHA, complete owned-source/replacement/patch manifest SHA, route-manifest SHA, dual-era codec and modern SDK lock SHA, generated settings SHA, single-group policy SHA, normalized 70-tool catalog and scope-map SHA, CIMD/DCR/callback-approval policy SHA, redacted observed-wire evidence SHA, and conformance-suite/result-bundle SHA, plus `noSecrets: true`, `status: pass`, `createdAt`, and `expiresAt`. Any missing, expired, or mismatched input makes `remotePublicReady` and `tunnelAllowed` false. The conformance suite exercises protocol selection/header-body agreement, `server/discover`, both `tools/list` envelopes, authorization request parsing, CIMD/JWKS and fallback DCR, authorization-code persistence, token issue, refresh, verification middleware, route dispatch, revocation, metadata/issuer binding, and log/error serialization—not merely one endpoint.

Remote enablement requires all of the following:

- external HTTPS issuer and exact protected resource/audience `https://mcp.w4w.dev/mcp/things`;
- RFC 9207 issuer identification in metadata and every authorization success/error response;
- passing `2026-07-28` and `2025-11-25` transport suites, mandatory modern header/body agreement, `server/discover`, no MCP sessions, and identical normalized 70-tool catalogs;
- nonempty state and PKCE `S256`; `plain` and missing verifier are rejected;
- resource, audience, principal, and granted scopes survive code exchange and refresh and are enforced on every tool call;
- `things.read`, `things.write`, and `things.admin` minimum scopes are enforced per tool;
- refresh tokens rotate, consumed refresh tokens cannot be replayed, and access/refresh token revocation is observed;
- dashboard JWTs, loopback bearer keys, query/body tokens, wrong-resource tokens, wrong-route tokens, and insufficient-scope tokens fail closed;
- login uses a Secure, HttpOnly, SameSite session cookie; tokens never appear in URLs, logs, redirects, exceptions, or persisted test artifacts;
- CIMD is validated as the primary client identity; fallback DCR is limited to the exact approved ChatGPT web redirect and metadata, and consent is explicit;
- a current, redacted observed-wire proof identifies the ChatGPT era and registration mode without parser fallback or secret persistence.

Cloudflare ingress implements the frozen manifest above. Failure of any OAuth or ingress test leaves remote exposure disabled; there is no bearer-in-URL, unauthenticated, external-IdP, credential-substitution, spoofed-header, or alternate-group fallback.

## Skill, Plugin, And Documentation Integration

- Release `things-manager` as v2.0.0 while keeping portable frontmatter strict; native-only metadata such as `argument-hint` stays in `config/skill-adapters.json`.
- Make `skills/things-manager/references/capabilities.md` the canonical routing/capability ledger. A deterministic script renders maintainer and ChatGPT copies and supports `--check` parity.
- The generated ownership chain is strict: `skills/things-manager` source and its capability ledger -> catalog authoring sync -> web/catalog/README generation. Never hand-edit generated catalog/index/research MDX. The focused parity command is `uv run python skills/things-manager/scripts/render_capabilities.py --check`.
- Preserve read-before-write, ID-first targeting, duplicate prevention, 25-item default bounds, ambiguity blocking, preview/confirmation, cross-backend serialization, read-after-write verification, privacy, and changed/skipped/failed/ambiguous reporting.
- Remove active SupaThings names and raw `things_json` guidance. Unsupported recurrence/reorder requests fail truthfully without a hidden fallback.
- Keep the existing root plugin/manifests as the only packaging source. The Things++ ChatGPT bundle is setup/documentation, not a second plugin or claim that ChatGPT loads the portable skill.
- Rewrite all 25 current eval IDs to v2 semantics, then add exactly 16 cases covering: single-group routing; local/remote endpoint parity; 70-tool closure; core-first precedence; fixed Shortcut names; fixed native scripts; unavailable Shortcut degradation; unavailable native degradation; cross-backend serialization; stale-write reread/verification; bounded `create_todos`; structured-project no-raw-JSON; immediate-delete confirmation; tag/area administration confirmation; truthful recurrence/reorder refusal; and cross-backend prompt-injection resistance.

## Hyperfine Parallel Execution

The integration captain coordinates but does not create a fourth writer lane. Three exclusive writer owners are kept occupied whenever dependencies allow:

The executable owner table in `tasks.md` is authoritative. Its current dependency-safe lanes are:

| Wave | Owner A | Owner B | Owner C |
|---|---|---|---|
| F1 | core/common adapter, immutable wrapper, core tests | Shortcuts/native MCPs, bridge contracts, their tests | `things-manager`, capability ledger/parity/evals |
| F2A | audited downstream intake, exact package/lock, materializer, same-process launcher, candidate inventory | dual-era protocol/preflight/provider boundary, fixtures, protocol tests, runtime-contract source | OAuth, shared policy/security, hash-only state, OAuth fixtures/tests |
| F2B | registry/schema/generator/projections and focused topology tests | ingress/runtime/listeners plus every active start/reconcile/doctor/loader/process-retirement surface | ChatGPT setup bundle, source docs, authoring inputs |

F2A-A publishes only a candidate inventory because B and C are still creating owned sources. The captain freezes the complete `owned-sources.json`, `patch-manifest.json`, `audit-manifest.json`, final `pnpm-lock.yaml`, materialized output inventory, and aggregate distribution digest only at `TPP-S2-01`, after both F2 joins.

Shared `pyproject.toml`, `uv.lock`, root manifests, generated outputs, home configs, runtime reconciliation, and live mutations are singleton barriers owned by the integration captain only after all active writers join. A task is not resolved until it is completed with evidence or explicitly interrupted with a recorded reason; every wave enforces `N dispatched = N resolved`.

The recovery ladder is: message the current owner; inspect disk/transcript; interrupt only if necessary; resume the same owner; retry once with narrower scope; then reassign after confirming no live writer remains. Never dispatch two writers to the same path or re-run a generator while source owners are active.

## Integration Points

- Reuse FastMCP v3 conventions with bounded source requirement `fastmcp>=3.4.7,<4` and exact frozen lock/runtime `3.4.7`, plus the existing MCPHub registry/schema/settings generator, runtime reconciler, projection renderer, root plugin builders, skill validators/eval CLI, web generator, and docs-steward. Replace the development-only loader assumption with the content-addressed source/materializer/launcher contract above.
- Add no compatibility aliases. Retired projection IDs remove current SupaThings/direct stale entries only after exact backups and fresh source proof.
- Capability-matrix and tool-list checks compare set equality and schema digests; a raw tool count alone is insufficient evidence.

## Alternatives Rejected

- **Keep SupaThings beside the new stack:** duplicates writes, keeps raw/unsafe surfaces, and makes zero-loss proof ambiguous.
- **Separate local, ChatGPT, or admin groups:** violates the single-router requirement and creates drifting capability subsets.
- **Wildcard group membership:** cannot prove the exact union or prevent future accidental exposure.
- **Hide diagnostics to reduce schema size:** contracts the audited upstream surface; sanitize and scope them instead.
- **Expose arbitrary URL/JSON/Shortcut/AppleScript:** defeats the closed-schema and prompt-injection boundary.
- **Use an external OAuth façade/IdP:** contradicts the selected built-in MCPHub OAuth architecture.
- **Patch MCPHub at production load time or launch it through `npx`:** cannot bind a complete dependency/source/output identity and permits mutable runtime behavior.
- **Adopt `thingskit` or UI automation:** adds unreleased/signing/TCC risk without supplying the known recurrence/reorder gaps.

## Migration Or Compatibility Notes

1. Freeze the active SupaThings `tools/list`, current skill modes/evals, current group memberships, client projections, tunnel behavior, runtime/process state, and exact rollback targets before edits. The F0 runtime capture is temporally inconsistent/stale and is not cutover evidence; refresh provenance immediately before cutover and stop if it does not describe one coherent current runtime.
2. Implement and validate all tracked source while SupaThings remains the live rollback path. Do not expose both stacks to clients simultaneously.
3. Generate and inspect repo projections. Prove the 37/17/25 closure, exact 70 union, no generic/direct routes, and complete test matrix.
4. Preserve the first-cutover receipt as a failed operational attempt: the authenticated/materialized selection aborted before listener bind on the unrelated DeepWiki preflight, and the clean pointer/config rollback left remote/tunnel state disabled. Do not retry or select that stale seal; keep its exact digest and the exact historic quarantine identity in the selector/launcher-enforced revocation registry.
5. Apply only the two exact-preimage deterministic build corrections above and use the synthetic startup-scope/containment suite solely to authorize rebuilding every transform/output receipt and aggregate digest. After a non-revoked reseal and isolated owner-only rematerialization, run the actual no-bind preselection gate; only that post-seal gate may claim real MCPHub/provider readiness, normalized 70-tool closure, unchanged `current`/selection state, and both managed ports absent before and after.
6. Refresh exact local backups, select only the newly verified digest, reconcile the full preserved topology, and run privacy-preserving local modern `server/discover`/`tools/list`, legacy `initialize`/`tools/list`, health, route-negative, and bounded read-only Things probes. Prove no MCP session identifier is minted or required and prove normalized catalog identity. Missing fixed bridges or unproved TCC do not contract the advertised 70-tool catalog and do not block this local-only cutover; affected calls must instead prove typed unavailable/degraded behavior and must not be reported as operational. Any unrelated server may be truthfully disconnected, but its failure cannot erase the 70-tool Things inventory or abort the listener.
7. Continue after local J4 through the explicitly authorized remote implementation and apply sequence. Require fresh fixed-bridge and noninteractive-TCC readiness plus offline dual-era/OAuth/ingress conformance first; a remote-mode environment value alone cannot activate production. Then require a current redacted observed-wire ChatGPT proof and a content/config/route-manifest-bound activation receipt before the explicit remote-apply action starts the restricted tunnel under a five-minute timeout guard. Probe the complete positive/negative route, credential, OAuth, issuer, protocol, and 70-tool schema matrix before durable enablement. Missing TCC, observed-wire, or authenticated UI evidence is a precise blocked proof layer, not `not authorized`. Any failed, stale-receipt, digest-mismatched, or timed-out probe stops cloudflared before the origin listener, disables the public route, and proves the disabled state by external and local readback.
8. Live mutation remains off. If separately approved with `THINGS_LIVE_MUTATION_TEST=1`, create one uniquely named disposable item, verify create/update/move, request cleanup approval, then verify deletion without touching existing items.
9. Roll back by disabling public ingress first, moving the content-addressed runtime pointer and restoring only exact backed-up non-auth config/settings/runtime bytes, restarting the singleton MCPHub, and verifying prior SupaThings process/group behavior. The OAuth database, WAL, browser-session store, replay/revocation state, and client-registration state are explicitly excluded: never restore or copy them backward. Do not reset/stash/revert the dirty repository to perform runtime rollback.
