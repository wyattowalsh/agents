# Design

## Invariants (non-negotiable, inherited from `fleet-hooks-guard-expansion`)

- Enforce-tier deny transport is unchanged: JSON on **stdout**, **exit 0**, per the
  harness-specific shape documented in
  [`fleet-hooks-guard-expansion/design.md`](../fleet-hooks-guard-expansion/design.md).
- OpenCode and Grok bridges/adapters fail open **only** on dispatcher
  crash/timeout/missing-runner; an explicit deny payload always blocks. This
  program does not widen that fail-open surface.
- Cursor `failClosed` semantics (`matcher != ".*"` fail-closed for enforce
  policies) are preserved by every bundle/render change.
- No secret-guard weakening; `research-readonly-write-guard`,
  `cursor-before-read-file-guard`, `git-commit-push-guard`, and the image
  optimizer keep their current deny conditions verbatim through every wave.

## Lane model

| Lane | Owner file(s) |
|------|---------------|
| L0 | `openspec/changes/fleet-hooks-performance/**` |
| D | `hooks/wagents-hook.py`, `hooks/run-wagents-hook`, `hooks/wagents-hook-worker.py`, `wagents/hooks/bundle.py` |
| R | `config/hook-registry.json`, `config/schemas/hook-registry.schema.json` |
| P | `wagents/hooks/render.py`, `wagents/hooks/merge.py` |
| A | `wagents/platforms/{codex,cursor,claude,copilot,gemini,grok,opencode}.py` |
| B | `platforms/opencode/plugins/wagents-hook-bridge.ts` |
| T | `tests/hooks/**`, hook integration tests under `tests/` |
| S | `scripts/sync_agent_stack.py` (G7 only) |
| C | `wagents/image_inputs.py` |
| O | `docs/src/content/docs/hooks/index.mdx` |

Same-file edits within a lane are serialized; different lanes proceed in
parallel once their upstream gate passes (see wave schedule in `tasks.md`).

## Baseline measurement (`WAGENTS_HOOK_TIMING`)

`hooks/wagents-hook.py` gains an opt-in timing sidecar: when
`WAGENTS_HOOK_TIMING=1` is set, `main()` records `policy_id`, `harness`,
`event`, wall-clock duration in milliseconds, and the exit code as one JSON
line appended to `~/.cache/wagents/hook-timing.jsonl` (best-effort; a write
failure never affects the hook's exit code or stdout). This is
behavior-neutral: the flag is unset by default in every rendered harness
command, so W1 ships with zero change to fleet behavior.

`scripts/hooks/hook_perf_inventory.py` reads `config/hook-registry.json` and
reports, per harness and per logical event, how many enabled hook rows (and
therefore how many process spawns under the `legacy` tier) fire for that
event. This is the process-count half of the baseline; `hook-timing.jsonl`
is the wall-clock half.

### Baseline appendix (captured `T-010a-f`, live via `hook_perf_inventory.py --json`)

Snapshot from `uv run python scripts/hooks/hook_perf_inventory.py --json`
against the pre-bundle registry (`WAGENTS_HOOK_PERF_TIER=legacy`, the
default; 60 total enabled dispatcher/script rows across 5 hook-capable
harnesses). This table is a point-in-time snapshot — re-run the script for
the authoritative live count after any registry change:

| Harness | Total spawns | Max spawns, single event | Event |
|---------|--------------|---------------------------|-------|
| cursor | 17 | 6 | `PreToolUse` (destructive-shell, protected-file, git-commit-push, image-optimizer, research-readonly-write, research-dangerous-shell) |
| codex | 13 | 6 | `PreToolUse` (same 6-row shape as Cursor) |
| github-copilot | 13 | 6 | `preToolUse` (2 shell-script guards + 4 dispatcher policies) |
| claude-code | 10 | 4 | `PreToolUse` (git-commit-push, image-optimizer, research-readonly-write, research-dangerous-shell) |
| gemini-cli | 7 | 4 | `PreToolUse` (same shape as Claude Code) |

Each dispatcher-backed row is a distinct cold `python3 hooks/wagents-hook.py`
invocation; the image optimizer additionally nests one `uv run python -m
wagents.image_inputs` subprocess per triggering event under the `legacy` and
`g1` tiers (removed by G3's in-process path). A single Cursor Bash tool call
therefore costs up to 6 cold Python starts (7 including the nested image
optimizer `uv run`) before G2/G3 bundling and in-process image handling.

## Bundle contract (G2)

New module: [`wagents/hooks/bundle.py`](../../../wagents/hooks/bundle.py).

`bundle_mode` values, stored per bundle group on the registry row
(`bundle_group`, `bundle_mode`):

| `bundle_mode` | Behavior | Timeout |
|---------------|----------|---------|
| `enforce-chain` | Run enforce-tier policies in registry order; first deny wins and short-circuits the remaining chain. | `min(sum(policy_timeout for policy in chain), harness_timeout)` |
| `context-chain` | Run context-tier policies; merge `additional_context` / status messages in order (later messages append, no policy "wins"). | same as above |
| `mixed` | Run the `enforce-chain` first (reserving its budget); only if every enforce policy allows does the bundle continue into `context-chain` policies using the remaining budget. | enforce budget reserved first, context runs with the remainder |

CLI surface:

```
hooks/run-wagents-hook --bundle policyA,policyB,policyC --harness cursor
python3 hooks/wagents-hook.py --bundle policyA,policyB,policyC --harness cursor
```

`wagents/hooks/bundle.py` exposes `run_bundle(policy_ids, harness, payload,
*, mode)` which:

1. Loads each policy function from the existing `POLICIES` dispatch table in
   `hooks/wagents-hook.py` (imported lazily to avoid a circular import — the
   dispatcher module imports `wagents.hooks.bundle` for the `--bundle` CLI
   path, and `bundle.py` imports the policy table from the dispatcher module
   at call time).
2. Normalizes the payload once (single `_normalize()` call shared across the
   whole bundle instead of once per subprocess).
3. Executes the chain per `bundle_mode`, tracking cumulative elapsed time
   against the bundle's timeout budget; a policy that would exceed the
   remaining budget is skipped and audited as `bundle-timeout-skip`.
4. Emits exactly one stdout JSON payload for the harness (the first deny in
   `enforce-chain`/`mixed`, or the merged context payload in
   `context-chain`), preserving each policy's existing per-harness deny/allow
   shape from `_deny()` / `_additional_context()`.
5. Never widens fail-open behavior: if a **required** enforce policy's module
   fails to load mid-bundle, the existing `_enforce_module_load_failure()`
   fail-closed path still fires for that policy id.

Only policies that already share a `logical_event` + harness + adjacent
registry ordering are grouped into a `bundle_group`; policies with
conflicting `mode` semantics (e.g. an enforce guard and Stop-time truth gate)
are never placed in the same group.

## Fleet projection (G2, render)

`wagents/hooks/render.py::collapse_bundle_entries(hooks, harness)` walks the
harness's enabled hook rows, groups consecutive same-event rows that share a
non-null `bundle_group`, and replaces them with a single rendered entry whose
command invokes `{hook_runner} --bundle id1,id2,id3 --harness {harness}`.
Rows without a `bundle_group` (or with `bundle_group: null`) render exactly
as before — this keeps the projection change opt-in per hook row and fully
backward compatible for any row a maintainer does not annotate.

Per-harness matcher/timeout on the collapsed entry is the union of the
member rows' matchers — computed by `union_bundle_matchers()`, which splits
each member's `|`-delimited matcher, dedupes tokens case-sensitively in
first-seen order, and rejoins them — and the summed timeout budget capped at
the harness maximum. Member matchers are **not** guaranteed to be identical
within a bundle group: `cursor-shell-file-guards` groups a shell-only guard
(`Bash|bash|run_shell_command|shell|terminal`) with a guard that also covers
file-write tools (`Write|Edit|MultiEdit|apply_patch|edit|create|replace|write_file`),
so taking only the first member's matcher would silently narrow the
collapsed entry and stop firing for tool calls the dropped member used to
guard.

Matcher narrowing stays policy-specific: protected-file rows may drop shell
tokens only when a separate shell hook covers the same protected-file behavior.
Codex and Cursor protected-file rows intentionally retain shell tokens because
they catch shell writes to protected paths; the destructive-shell guards do not
cover that policy.

`WAGENTS_HOOK_PERF_TIER` (env, read by `render.py` at render time):

| Tier | Effect |
|------|--------|
| `legacy` (default) | No collapsing; one rendered entry per registry row (current behavior, byte-identical). |
| `g1` | Registry quick wins active (matcher narrowing, dispatcher caches) but no bundling. |
| `bundle` | `collapse_bundle_entries()` active; bundle groups render as single spawns. |
| `worker` | Bundle groups render through `wagents-hook-worker.py` warm-process forwarding instead of a fresh `--bundle` subprocess. |

Sync tooling (`scripts/sync_agent_stack.py`) reads `WAGENTS_HOOK_PERF_TIER`
from `config/skill-registry-policy.json`-style repo policy (not from the
invoking shell environment) so rendered `.cursor/hooks.json`,
`.claude/settings.json`, etc. are deterministic across machines; the default
committed tier is `legacy` until a maintainer promotes a later tier after
hyperfine validation (W8, `T-100b`).

## G3 — In-process image optimization

`wagents.image_inputs` already exposes a batch-JSON-stdin CLI
(`_image_optimizer_command` in `hooks/wagents-hook.py`). G3 adds
`wagents.image_inputs.optimize_image_batch_inprocess(batch)` — the same
Pillow-backed resize/compress logic invoked as a plain Python call — and the
dispatcher tries the in-process path first, falling back to the existing
`uv run` subprocess only if the in-process import fails (e.g. Pillow not
installed in the trusted system `python3`'s `sys.path`, which is expected
under the "no `wagents` package installed" dispatcher constraint documented
at the top of `hooks/wagents-hook.py`). Degraded-mode timing is logged via
the same `WAGENTS_HOOK_TIMING` sidecar with a `degraded: "subprocess-fallback"`
field so G8's regression check can see when the in-process path is not
active in a given environment.

## G4 — Cross-event dedupe

### Overlap matrix

| Event A | Event B | Overlap | Dedupe strategy |
|---------|---------|---------|------------------|
| Cursor `PreToolUse` (Bash) | Cursor `BeforeShellExecution` | Both guard shell commands for the same tool call on harnesses that emit both events | `dedupe_logical_policy_across_events()` drops the later duplicate `logical_policy` render within one `bundle_group`-eligible harness config when both events resolve to the same policy function and the harness fires both events for the same tool call. |
| Cursor `PostToolUse` | Cursor `AfterFileEdit` | Both run post-edit context checks for file-edit tools | Keep `AfterFileEdit` (more specific) and drop the `PostToolUse` context duplicate for edit-only tool matchers. |
| Codex `PreToolUse` | Codex `PermissionRequest` | Both guard destructive shell/protected files at different approval stages | Not deduped — `PermissionRequest` only fires when Codex's own approval flow is invoked, so both events are needed for full coverage. |

`wagents/hooks/render.py::dedupe_logical_policy_across_events(hook_registry,
harness)` returns a filtered hook list (never mutates the registry) applied
before rendering, gated by an explicit per-harness allowlist of
event-pairs so no accidental behavior loss occurs for events without a
verified overlap.

## G5 — Optional hook worker (default off)

`hooks/wagents-hook-worker.py` implements a line-delimited NDJSON protocol:
each request line is `{"policy_id" | "bundle": [...], "harness": str,
"payload": {...}}`; each response line is `{"stdout": str, "exit_code":
int}`. The worker keeps the dispatcher module (`hooks/wagents-hook.py`)
imported once and re-executes the request against `POLICIES`/`run_bundle`
per line, so repeated invocations skip Python interpreter startup. It is
**disabled by default** (`WAGENTS_HOOK_PERF_TIER=worker` opt-in only) because
warm-process reuse across tool calls requires a per-session forwarder the
harness must keep alive, which is a bigger architectural commitment than
bundling; G5 ships the protocol and a hyperfine soft gate (100x no-op ≥3x
faster than cold-spawn) without making it the rendered default for any
harness.

### Worker concurrency model

`_serve_socket()` in `hooks/wagents-hook-worker.py` runs a **serial accept
loop**: each `server.accept()` blocks until the current connection is fully
handled (`_serve_socket_connection` reads one NDJSON line, dispatches through
`_run_request`, writes the response, closes the connection) before the next
client is accepted. There is no thread pool and no concurrent request
handling inside the daemon.

When multiple harness hook invocations arrive in parallel (e.g. overlapping
Cursor `PreToolUse` events or concurrent tool calls), each forwarder process
connects to the same Unix socket independently; the kernel and `listen()`
backlog queue those connections until the worker accepts them one at a time.
This is intentional for the current design:

- **Enforce-chain semantics** require ordered, deterministic policy evaluation
  within a single bundle request; serializing whole requests avoids shared
  mutable dispatcher state races without adding locks.
- **Latency trade-off** is acceptable at the `worker` tier because the win is
  skipping repeated Python interpreter startup, not parallelizing policy work
  across connections.
- **Harness-side parallelism** still exists: each hook spawn is its own client
  process; only the warm worker daemon serializes service.

Revisit a thread pool or per-connection worker threads **only** when
maintainer hyperfine runs and `WAGENTS_HOOK_TIMING=1` traces show sustained
queue wait (connection accepted but handler not yet running) dominating p95
latency under realistic multi-event bursts. Until that evidence exists, keep
the single-threaded accept loop to preserve simplicity and enforce ordering.

## G6 — Harness-specific wins

- **Copilot**: `hooks/post-edit-quality.sh` runs `auto-format.sh` and
  `lint-check.sh` concurrently (`&` + `wait`) instead of Copilot's existing
  sequential `postToolUse` array, merging their context output into one
  message. `.github/hooks/policy.json` `postToolUse` collapses to a single
  entry for the two dispatcher-independent shell scripts (the
  `research-evidence-ledger` dispatcher row is unaffected).
- **Grok**: `render_grok_hooks()` in `wagents/platforms/grok.py` dedupes
  consecutive same-event rows that resolve to an identical `_grok_policy_id`
  before rendering (this can happen when both `codex` source rows and a
  Cursor-sourced row alias to the same dispatcher policy).
- **Research stop-verifier**: when `research-stop-verifier` is part of an
  enforce bundle, `_policy_stop_verifier` runs in-process against the
  already-normalized bundle payload instead of the bundle spawning a second
  subprocess for the Stop event.
- **Gemini**: `render_gemini_hooks()` already multiplies `timeout` by 1000
  for milliseconds; G6 confirms/tests this holds for bundle-collapsed
  entries so ms-timeout math is not lost when bundling.

## G7 — Sync efficiency

`scripts/sync_agent_stack.py` computes a sha256 of `config/hook-registry.json`
(plus the harness's rendered command template inputs) and skips re-rendering
a harness's hook projection when the hash is unchanged from the last
successful `--apply`/`--check` run recorded in
`~/.cache/wagents/sync-hook-hash.json`. `wagents apm materialize` gets the
equivalent bundle-parity check so `.apm/hooks/*.json` never silently drifts
from the fleet render. The skills/harness discovery registry parser gains an
`lru_cache` keyed on file mtime+size so repeated `wagents skills sync`
invocations in one process do not re-parse `config/hook-registry.json`
per harness.
### Owned hook destinations vs merge paths (RV-NEW-002)

`sync_hook_projection()` applies only when the destination file is a
hook-only JSON artifact that wagents fully owns (Cursor repo `hooks.json`,
Copilot `.github/hooks/policy.json`, Codex hooks JSON for repo/home with
distinct `codex-repo` / `codex-home` fingerprint namespaces). Harnesses
that merge hooks into larger settings documents (Claude, Gemini, Grok) keep
the existing full read-merge-write path so unrelated managed keys are not
skipped incorrectly.

## G8 — Ship

Promote the bundle contract into `openspec/specs/hooks-runtime-performance/`
and document `WAGENTS_HOOK_PERF_TIER` in the hooks hub docs page. The
promoted spec's regression gate is **relative** p95 latency regression
≤10% versus the `legacy`-tier baseline captured in this design doc's
appendix, not an absolute sub-50ms target — absolute targets are
machine-dependent and would produce false CI failures on slower runners.
