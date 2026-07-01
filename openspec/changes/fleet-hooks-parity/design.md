# Design

## Goal

Establish the foundation (G0) for the fleet hooks program: one rendering source,
one merge/strip source, a schema-guarded hook registry, and a curated external
hooks registry. The gate is behavior-preserving — no harness hook output changes
in this change.

## Lane model (honest parallelism)

| Lane | Hot resources | Max concurrent | Rule |
|------|---------------|----------------|------|
| L0 Lead / OpenSpec | `openspec/changes/fleet-hooks-parity/` | 1 | Coordinator only |
| C Core extract | `wagents/hooks/*`, `apm.py`, `sync_agent_stack.py` imports | 1 | Serial; gate for scale |
| R Registry | `config/hook-registry.json` | 1 | Single writer; workers produce patch specs only |
| P Policies | `wagents/hooks/policies/<name>.py` | ≤12 | One file per policy after T-REF-02 |
| A Adapters | `wagents/platforms/<harness>.py` | 6 | codex, cursor, claude, gemini, grok, opencode |
| S Sync/Copilot | `scripts/sync_agent_stack.py` (copilot section) | 1 | Never parallel with C lane edits |
| T Tests | `tests/hooks/test_*.py` | ≤8 | Parallel after owning adapter lands |
| D Docs | generated MDX | 1 | After validate green |

**File locks for G0:** Lane C owns `wagents/hooks/render.py`, `wagents/hooks/merge.py`,
`wagents/apm.py`, `scripts/sync_agent_stack.py`, and `wagents/platforms/base.py`
import lines. Lane R owns `config/hook-registry.json`. L0 owns the OpenSpec dir and
the two new schema files plus `config/external-hooks-registry.json`. Because all
G0 edits touch shared core/registry files, G0 runs as a single serial writer
(max real concurrency = 1, with optional read-only research in parallel).

## Shared renderer (T-REF-01)

`wagents/hooks/render.py` is the single home for hook rendering. It exposes:

- `render_hook_command(entry, harness, *, repo_root)` — formats the command
  template with `repo_root`, `hook_runner`, and `harness`.
- `enabled_hooks_for_harness(registry, harness)` — filters hooks with a command
  that target the harness.
- `render_codex_hooks(registry, *, repo_root)` — Codex command-handler shape with
  `timeout`, `statusMessage`, and optional `commandWindows`.
- `render_copilot_hooks(registry, *, repo_root)` — GitHub Copilot CLI policy shape.
- `render_standard_hooks(registry, harness, *, repo_root)` — Claude Code and
  Gemini CLI base shapes (delegates to `render_codex_hooks` for `codex`).
- `render_claude_apm_hooks(registry, *, repo_root)` — Claude shape used for
  `.apm/hooks/claude-code.json`, with the wider SessionStart/PermissionRequest
  event map APM currently emits.
- `render_cursor_apm_hooks(registry, *, repo_root)` — Cursor shape used for
  `.apm/hooks/cursor.json`.

Callers translate their root convention to an explicit `repo_root` string:

- `scripts/sync_agent_stack.py` keeps thin wrappers `render_codex_hooks`,
  `render_standard_hooks`, `render_copilot_hooks`, `render_hook_command`, and
  `enabled_hooks_for_harness` that resolve `repo_root` from the `repo_relative`
  flag (preserving the public signatures used by tests) and delegate to
  `wagents.hooks.render`.
- `wagents/apm.py` calls the render module directly with `repo_root="."`
  (and `${workspaceFolder}` for the Cursor APM shape).

This removes the duplicated `_render_*_shape` functions from `apm.py` and the
inline render bodies from `sync_agent_stack.py` while keeping output byte-stable.

## Consolidated merge/strip (T-REF-03)

`wagents/hooks/merge.py` is the single source for:

- `HOOK_COMMAND_MARKERS`
- `strip_generated_hook_entries(hooks)`
- `merge_hook_groups(existing, generated)`

`wagents/platforms/base.py` and `scripts/sync_agent_stack.py` import these names
from the merge module (re-exporting `HOOK_COMMAND_MARKERS` so existing references
keep working). Platform adapters (`claude.py`, `gemini.py`) continue to import
`merge_hook_groups` from `base`, which now re-exports from the merge module.

## Hook registry schema (T-001)

`config/schemas/hook-registry.schema.json` models the **current** registry shape
and reserves forward-looking fields so later waves can adopt a policy-first model
without a schema rewrite:

- Top level: `version` (integer), `hooks` (array), optional `$schema`.
- Each hook (current fields): `id` (required), `logical_event` (required),
  `command` (required), `harnesses` (required, non-empty string array),
  `description`, `matcher`, `timeout`, `status_message`, `mode`
  (`context` | `enforce` | `audit`), `degraded_behavior`. Codex-only optional
  fields recognized by the renderer (`statusMessage`, `commandWindows`,
  `command_windows`) are permitted.
- **Reserved forward fields (documented for T-001c):**
  - `logical_policy` (string) — id of the harness-neutral policy a hook
    implements, decoupling intent from per-harness projection.
  - `projection` (object) — declarative per-event/per-harness projection hints
    that later replace the imperative renderer branches.
  - `harness_overrides` (object) — per-harness field overrides (timeout, matcher,
    mode) applied on top of the logical policy.

These three fields are optional in G0; the registry refactor in G2 will begin
populating them. `config/hook-registry.json` gains only a `$schema` pointer in
this change — no hook entry semantics change.

## External hooks registry (T-002)

`config/external-hooks-registry.json` (schema:
`config/schemas/external-hooks-registry.schema.json`) is the curated registry for
hooks owned by third parties, kept separate from repo-owned
`config/hook-registry.json`. The first row is **Plannotator** plan review, which
maps `enter_plan_mode`/`exit_plan_mode` events and is sourced from the existing
`config/grok-plannotator-hooks.json` policy. Fields: `id`, `name`, `description`,
`source`, `trust_tier`, `status`, `logical_events`, `matchers`, `policy_source`,
`harnesses`, `owner`, `risk_notes`, `notes`. G1 (T-012) will unify the Plannotator
policy into `config/plannotator-hooks.policy.json` and consume this registry.

## Validation

Both new config/schema pairs are added to the existing
`test_platform_overhaul_registries_validate_against_schemas` conformance test in
`tests/test_distribution_metadata.py`, so `uv run pytest` enforces conformance.
