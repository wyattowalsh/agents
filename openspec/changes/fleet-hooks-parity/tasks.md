# Tasks

Mirrors the Fleet Hooks Master v3 hyperfine task graph. Format per node:
`ID — lane — files — done_when`. `[P]` marks independently parallelizable nodes.

**Status (2026-06):** G0–G6 implementation landed in the working tree. Remaining
unchecked items are explicit deferrals (home sync, matcher pack, copilot render
test, `subagent_stop_synth` policy, manual Cursor UI). Guard-expansion close-out:
[`fleet-hooks-guard-expansion/`](../fleet-hooks-guard-expansion/) (RV-001–RV-010 + C-010/C-020).

## G0 — Foundation (in scope)

- [x] T-000a — L0 — `openspec/changes/fleet-hooks-parity/proposal.md` — change exists.
- [x] T-000b — L0 — `openspec/changes/fleet-hooks-parity/tasks.md` — tasks mirror the graph.
- [x] T-000c — L0 — `openspec/changes/fleet-hooks-parity/design.md` — lane model + file locks documented.
- [x] T-001a — L0 — `config/schemas/hook-registry.schema.json` — schema validates the registry.
- [x] T-001b — R — `config/hook-registry.json` — registry conforms; no semantic change.
- [x] T-001c — L0 — design.md fields (`logical_policy`, `projection`, `harness_overrides`) — documented.
- [x] T-REF-01a — C — `wagents/hooks/render.py` — renderer extracted from apm + sync.
- [x] T-REF-01b — C — `wagents/apm.py` imports render — no inline render.
- [x] T-REF-01c — C — `scripts/sync_agent_stack.py` imports render — no inline render.
- [x] T-REF-03a — C — `wagents/hooks/merge.py` — strip + merge single source.
- [x] T-REF-03b — C — remove dup in `base.py`, `sync_agent_stack.py` — one implementation.
- [x] T-002a — L0 — `config/schemas/external-hooks-registry.schema.json` — schema exists.
- [x] T-002b — L0 — `config/external-hooks-registry.json` — Plannotator row.

## G1 — Cursor P0 (PR-0)

- [x] T-010a — A — `render.py` `_cursor_flat_entry()` (authoritative flat helper).
- [x] T-010b — A — `cursor.py` `render_hooks` flat list per event.
- [x] T-010c — A — cloud event subset map in cursor adapter.
- [x] T-011a — C — `apm.py` imports `render_cursor_hooks` flat shape.
- [x] T-012a — L0 — `config/plannotator-hooks.policy.json` unified policy.
- [x] T-012b — L0 — migrate from `config/grok-plannotator-hooks.json`.
- [x] T-012c — A — `config/cursor-global-hooks.json` template.
- [x] T-013a — A — `cursor.sync_home()` writes `~/.cursor/hooks.json`.
- [x] T-013b — A — merge user custom hooks preserve.
- [x] T-014a — S — extend `HOOK_COMMAND_MARKERS` if needed.
- [x] T-014b — S — clean `.claude/settings.json` contamination.
- [x] T-015a — T — fix `test_cursor_adapter_render_hooks_uses_native_event_names`.
- [x] T-015b — T — `tests/hooks/test_render_cursor.py` snapshots.
- [x] T-016a — L0 — `sync --check --targets repo` idempotent.
- [ ] T-016b — L0 — `sync --apply --targets home` (user-approved; deferred).

## G2 — Registry Tier A (PR-1) — Lane R serial

- [x] T-020a [P] — R-spec — format/lint harness spec patch.
- [x] T-020b — R — `hook-registry.json` format/lint → cursor,codex,claude,gemini.
- [x] T-021a [P] — R-spec — orphan script entries spec.
- [x] T-021b — R — register verify-stop, idle, task-completed.
- [x] T-022a — R — claude+gemini dedicated guard rows.
- [x] T-022b — R — add github-copilot to research-stop-verifier.
- [ ] T-026a [P] — R-spec — matcher pack design (Shell, MCP, Read, Write) — deferred.
- [ ] T-026b — R — registry `matchers` + render normalization — deferred.

## G3a — Adapters batch 1 (PR-2) — parallel

- [x] T-030a [P] — A — `codex.py` new events projected.
- [x] T-030b — T — `tests/hooks/test_render_codex.py`.
- [x] T-032a [P] — A — `claude.py` PermissionRequest, SubagentStop, SessionStart.
- [x] T-032b — T — `tests/hooks/test_render_claude.py`.
- [x] T-033a [P] — A — `gemini.py` SessionStart + guards.
- [x] T-033b — D — harness-surface-registry antigravity note.
- [x] T-033c — T — `tests/hooks/test_render_gemini.py`.

## G3b — Adapters batch 2 (PR-3) — parallel with G3a

- [x] T-031a [P] — A — `cursor.py` afterFileEdit, beforeReadFile, beforeShellExecution.
- [x] T-031b — A — cloud guard duplication map in design.md.
- [x] T-031c — A — subagentStart, beforeMCPExecution stubs.
- [x] T-031d — T — `tests/hooks/test_render_cursor.py` extend.
- [x] T-034a [P] — S — `sync_agent_stack.py` copilot render stop-verifier.
- [x] T-034b — S — `.github/hooks/policy.json` aligned.
- [ ] T-034c — T — `tests/hooks/test_render_copilot.py` — deferred (no dedicated file yet).
- [x] T-035a [P] — A — `grok.py` `render_grok_hooks()` fleet projection.
- [x] T-035b — A — `~/.grok/hooks/wagents-fleet.json` deny adapter.
- [x] T-035c — T — `tests/test_grok_platform.py` extend.
- [x] T-036a [P] — A — `platforms/opencode/plugins/wagents-hook-bridge.ts`.
- [x] T-036b — A — `opencode.py` sync fragment.
- [x] T-036c — D — OpenCode dedupe doc in design.md.

## G4 — Policies (PR-4) — parallel after T-REF-02

- [x] T-REF-02a — C — `wagents/hooks/policies/__init__.py` + registry.
- [x] T-REF-02b — C — move existing policies to modules (partial split; dispatcher retains legacy).
- [x] T-REF-02c — C — `wagents-hook.py` dispatcher + policy modules.
- [x] T-040a [P] — P — `policies/git_commit_push_guard.py`.
- [x] T-041a [P] — P — `policies/before_read_file_guard.py`.
- [x] T-042a [P] — P — `policies/stop_quality_gate.py`.
- [x] T-043a [P] — P — `policies/subagent_start.py`.
- [ ] T-043b — P — `policies/subagent_stop_synth.py` — deferred.
- [x] T-044a [P] — P — `policies/before_mcp_execution.py`.
- [x] T-045a [P] — P — `policies/stop_wagents_validate.py`.
- [x] T-046a [P] — P — `policies/grok_deny_adapter.py`.
- [x] T-047a — R — `hook-registry.json` Tier B rows enabled.
- [x] T-047b — T — `tests/test_wagents_hook.py` matrix.

## G5 — Validate (PR-5)

- [x] T-050a — C — `wagents hooks validate` `--harness` filter.
- [x] T-050b — C — `wagents hooks validate --harness all` exit 0.
- [x] T-050c — C — per-harness shape gates.
- [x] T-051a — C — `wagents/hooks/convert.py`.
- [x] T-051b — T — `tests/hooks/test_convert.py`.
- [x] T-052a — T — `tests/hooks/test_render_*` full matrix.
- [x] T-053a — T — policy integration fixtures.
- [x] T-054a — L0 — `sync_agent_stack.py --check` all platforms.
- [ ] T-055a — L0 — Cursor Settings → Hooks UI 0 errors (manual; see W4).
- [x] T-055b — L0 — cloud agent doc note in hooks hub.

## G6 — Docs + audit

- [x] T-060a — D — `wagents docs generate` Cursor section in hooks hub.
- [x] T-060b — D — `docs/src/content/docs/hooks/index.mdx` per-harness table.
- [x] T-061a — D — `hook-surface-registry.json` all CLI harnesses.
- [x] T-061b — D — `discover_surfaces` script discovers hooks.
- [x] T-062a — L0 — harness-master `/audit` dry-run 0 projection gaps.
- [x] T-063a — D — `scripts/check_hook_discovery_parity.py` CI script green.

## Verification (G0 gate)

- [x] Run `uv run pytest tests/test_sync_agent_stack.py tests/test_apm_materialize.py -q`.
- [x] Run `uv run pytest tests/test_distribution_metadata.py -q` (schema conformance).
- [x] Run `uv run ruff check` on changed Python files.
- [x] Run `uv run wagents validate`.
- [x] Run `uv run wagents openspec validate`.

## Stop Rules

- Do not run `sync --apply --targets home` against the user home directory.
- Do not commit unless hooks pass.
- Do not edit the source plan file.
