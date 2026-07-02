# Tasks

Canonical task graph for the Fleet Hooks Performance v2 program. Format:
`ID — lane — [P] — done_when`. `[P]` marks tasks that may run in parallel with
sibling `[P]` tasks in the same wave once the wave's serial prerequisites land.

## W0 — OpenSpec scaffold (gate: `uv run wagents openspec validate`)

- [x] T-000a `proposal.md`
- [x] T-000b `affected-surfaces.md`
- [x] T-000c `design.md`
- [x] T-000d `validation-matrix.md`
- [x] T-000e `tasks.md` (this file)
- [x] T-000f `specs/hooks-runtime-performance/spec.md`
- [x] T-000g `coordinator/wave-w0-scaffold.json`
- [x] T-001a `uv run wagents openspec validate` green

## W1 / G0 — Baseline (behavior-neutral)

- [x] T-010a — D — `WAGENTS_HOOK_TIMING=1` jsonl sidecar in `hooks/wagents-hook.py`
- [x] T-010b [P] — T — `tests/fixtures/hooks/*.json` payload fixtures
- [x] T-010c [P] — T — `tests/hooks/test_performance_baseline.py`
- [x] T-010d [P] — L0 — hyperfine recipes in `validation-matrix.md`
- [x] T-010e [P] — `scripts/hooks/hook_perf_inventory.py` (spawn count per event)
- [x] T-010f — L0 — baseline appendix in `design.md`
- [x] T-011a — `coordinator/wave-w1-baseline.json`

## W2 / G1 — Quick wins + registry prereqs

**R lane (serial first):**

- [x] T-020a — backfill `logical_policy` on every registry row
- [x] T-020b — schema: `bundle_group`, `bundle_mode`
- [x] T-021a [P] — matcher pack design note in `design.md`
- [x] T-021b — narrow `image-input-optimizer-guard` matcher off `.*`
- [x] T-021c [P] — remove `Bash` from protected-file matcher where a shell hook already covers it; Codex/Cursor retain shell tokens because protected-path shell writes are not covered by destructive-shell guards
- [x] T-021d [P] — T — `tests/hooks/test_registry_perf_metadata.py`

**D/C/P parallel after T-021b:**

- [x] T-022a-d [P] — D — `sys.modules` policy cache, argv fast-path, `lru_cache`s, `_candidate_paths` memo
- [x] T-023a-c [P] — D — `WAGENTS_HOOK_AUDIT` sampling, git-context cache, image fast-exit before subprocess
- [x] T-024a [P] — C — `load_image_optimizer_config` cache
- [x] T-024b — P — all rendered commands use `{hook_runner}` consistently
- [x] T-024c [P] — T — matrix + perf snapshot tests
- [x] T-025a — `uv run python scripts/sync_agent_stack.py --check --targets repo`
- [x] T-025b — `coordinator/wave-w2-g1.json`

## W3 / G2 core — Bundle API (serial SA-D)

- [x] T-030a — spec: bundle contract + timeout algorithm in `design.md`
- [x] T-030b — `wagents/hooks/bundle.py`
- [x] T-030c — `wagents-hook.py --bundle`
- [x] T-030d — `run-wagents-hook` forwards `--bundle`
- [x] T-031a [P] — T — `tests/hooks/test_bundle_dispatch.py`
- [x] T-031b [P] — T — extend `tests/hooks/test_enforce_fail_closed.py` for bundle fail-closed
- [x] T-031c [P] — T — extend `tests/hooks/test_opencode_bridge_integration.py` for bundle path

## W4 / G2 fleet — Render + fleet projection

- [x] T-040a — P — `collapse_bundle_entries()` in `render.py`
- [x] T-040b — P — `dedupe_logical_policy_across_events()` design hook (implemented in W5, allowlist stub here)
- [x] T-041a [P] — A — codex adapter bundle-aware render
- [x] T-041b [P] — A — cursor adapter bundle-aware render
- [x] T-041c [P] — A — claude adapter bundle-aware render
- [x] T-041d [P] — A — gemini adapter bundle-aware render (ms timeout preserved)
- [x] T-041e [P] — A — copilot guard entries bundle-aware render
- [x] T-041f [P] — A — grok fleet projection bundle-aware render
- [x] T-042a — B — `wagents-hook-bridge.ts` `--bundle` support
- [x] T-042b-g [P] — T — per-harness render snapshot tests + bridge bundle test
- [x] T-043a — `uv run python scripts/sync_agent_stack.py --check --targets repo`
- [x] T-043b — `coordinator/wave-w4-g2-render.json`

**Done when:** Cursor Bash chain renders ≤2 spawns and OpenCode Bash renders 1
spawn under `WAGENTS_HOOK_PERF_TIER=bundle`; deny matrix tests stay green.

## W5 — G3 (image) / G4 (dedupe) / G6 (harness-specific), parallel

### G3 — Image in-process

- [x] T-050a — C — `optimize_image_batch_inprocess()` in `wagents/image_inputs.py`
- [x] T-050b — D — dispatcher tries in-process path with subprocess fallback + degraded timing log
- [x] T-050c [P] — B — skip image bundle policy when OpenCode native image handling is active
- [x] T-050d [P] — T — image in-process tests
- [x] T-050e [P] — T — baseline regression test (no behavior change on deny/allow)

### G4 — Event dedupe

- [x] T-060a — overlap matrix in `design.md`
- [x] T-060b — P — `dedupe_logical_policy_across_events()` implementation
- [x] T-060c — P — wire into Cursor/Codex render paths behind the allowlist
- [x] T-060d [P] — T — cursor dedupe snapshot test
- [x] T-060e [P] — T — codex no-dedupe snapshot test
- [x] T-060f [P] — S — sync check after dedupe wiring

### G6 — Harness-specific

- [x] T-080a [P] — Copilot `hooks/post-edit-quality.sh` parallel format+lint
- [x] T-080b [P] — Copilot `.github/hooks/policy.json` postToolUse collapse
- [x] T-080c [P] — Grok deny/render dedupe in `render_grok_hooks()`
- [x] T-080d [P] — research `stop_verifier` in-process when bundled
- [x] T-080e [P] — Gemini ms timeout preserved at render for bundled entries
- [x] T-080f [P] — T — copilot render test
- [x] T-080g [P] — T — research stop-verifier in-process test

## W6 / G5 — Worker (optional, default off)

- [x] T-070a — worker NDJSON protocol documented in `design.md`
- [x] T-070b — `hooks/wagents-hook-worker.py`
- [x] T-070c — forwarder support (`hooks/wagents-hook-client.py` + `wagents-hook.py --worker-socket` opt-in; see RW4/RV-003)
- [x] T-070d [P] — T — `tests/hooks/test_hook_worker.py`
- [x] T-070e [P] — hyperfine soft gate note in `validation-matrix.md` (100x no-op ≥3x faster)

## W7 / G7 — Sync efficiency

- [x] T-090a — registry sha256 skip re-render in `scripts/sync_agent_stack.py` (see RW5/RV-004 `sync_hook_projection()`)
- [x] T-090b [P] — APM bundle-render parity check
- [x] T-090c [P] — T — parity test for APM bundle rendering
- [x] T-090d [P] — discovery registry parse cache (`lru_cache` keyed on mtime+size)
- [x] T-090e — gate: `uv run python scripts/sync_agent_stack.py --check --targets repo` green

## W8 / G8 — Ship

- [x] T-100a — hooks hub docs perf section + `WAGENTS_HOOK_PERF_TIER` documented
- [x] T-100b — promote spec: relative p95 regression ≤10% gate in `openspec/specs/hooks-runtime-performance/spec.md`
- [x] T-100c — note `uv run wagents docs generate --no-installed` follow-up (not run in this change; docs source updated)
- [x] T-100d [P] — optional CI `hook-perf` job stub (non-blocking, manual trigger)
- [x] T-100e — full validation matrix (V-01 through V-12 + V-RV-01..06) run and recorded

## Review Remediation (v2) — RV-001..RV-005

Closes all five `/review` findings on top of W0–W8 above. Coordinator manifests:
`coordinator/wave-rw0-scaffold.json` … `wave-rw6-close.json`. See
`validation-matrix.md` for `V-RV-01`..`V-RV-05`.

### RW0 — Scaffold (serial, gate: `uv run wagents openspec validate`)

- [x] T-RV-000a `coordinator/wave-rw0-scaffold.json` … `wave-rw6-close.json`
- [x] T-RV-000b this **Review Remediation** section
- [x] T-RV-000c `validation-matrix.md` `V-RV-01..05`
- [x] T-RV-000d `affected-surfaces.md` + stub `hooks/wagents-hook-client.py`
- [x] T-RV-000e `uv run wagents openspec validate` green

### RW1 — RV-001 (P0): best-effort hook-state I/O

- [x] T-RV-010a — D — `_best_effort_os()` wraps mkdir/open/write/chmod in
      `_record_decision`, `_write_state`, `_clear_state` (mirrors
      `_record_hook_timing`'s best-effort try/except); `decision_recorded = True`
      is set before the guarded block so stdout/exit code never change on I/O
      failure.
- [x] T-RV-010b [P] — T — `test_record_decision_write_failure_never_raises`
- [x] T-RV-010c [P] — T — `test_write_state_failure_never_raises`
- [x] T-RV-010d [P] — T — `test_clear_state_failure_never_raises`
- [x] T-RV-010e [P] — T — chmod failure edge case
- [x] T-RV-010f — INT — **V-RV-01**: `pytest tests/hooks/test_performance_baseline.py -q`

### RW2 — RV-002 (P1→P0 bundled): bundle matcher union

- [x] T-RV-020a — P — `union_bundle_matchers()` in `wagents/hooks/render.py`;
      wired into `_synthetic_bundle_hook()` so the collapsed entry's matcher is
      the union of every member's matcher instead of only `members[0]`'s.
- [x] T-RV-020b [P] — L0 — `design.md` fleet-projection section corrected
      (members are *not* identical by construction; union is required).
- [x] T-RV-020c [P] — T — `tests/hooks/test_render_bundle_matchers.py` unit tests
- [x] T-RV-020d [P] — T — Cursor `bundle-cursor-shell-file-guards` covers
      `terminal` + `Write`
- [x] T-RV-020e [P] — T — Codex `bundle-codex-shell-file-guards` union coverage
- [x] T-RV-020f [P] — T — `bundle-research-shell-guards` union coverage
- [x] T-RV-020g [P] — T — legacy tier row count stays stable
      (`test_bundle_dispatch.py`)
- [x] T-RV-020h [P] — T — worker-tier matcher union == bundle-tier matcher union
- [x] T-RV-020i — INT — **V-RV-02**: `pytest tests/hooks/test_render_bundle_matchers.py -q`

### RW3 — RV-005 (P3, serial after T-RV-010a): unify single-policy dispatch finalization

- [x] T-RV-030a — D — `_finalize_single_policy_dispatch(...)` in `wagents-hook.py`
- [x] T-RV-030b — D — wire into `main()`'s single-policy path
- [x] T-RV-030c — D — wire into worker `_run_request()`'s single-policy path
- [x] T-RV-030d [P] — T — Cursor allow-parity test through the worker path

### RW4 — RV-003 (P2) / T-070c: stdlib forwarder + worker socket

- [x] T-RV-040a — D — new stdlib-only `hooks/wagents-hook-client.py`
      (`default_socket_path()`, `forward_request()`)
- [x] T-RV-040b — D — worker `--serve --socket PATH` (`chmod 0600`, NDJSON per
      connection)
- [x] T-RV-040c — D — `wagents-hook.py --worker-socket PATH` with cold fallback
      when the socket is missing/unreachable
- [x] T-RV-040d [P] — P — render worker branch emits
      `{hook_runner} ... --worker-socket ...` instead of invoking the worker
      script directly
- [x] T-RV-040e [P] — B — OpenCode bridge uses the runner + `--worker-socket`
      flag; no more direct `python3 wagents-hook-worker.py` cold spawn
- [x] T-RV-040f [P] — T — warm socket integration test
- [x] T-RV-040g [P] — T — cold fallback test (missing socket)
- [x] T-RV-040h [P] — T — bundle deny transport through the socket (stdout
      JSON, exit 0)
- [x] T-RV-040i [P] — L0 — daemon docs + `WAGENTS_HOOK_WORKER_SOCKET` env var
      noted in `design.md`
- [x] T-RV-040j [P] — L0 — hyperfine T-070e note in `validation-matrix.md`
- [x] T-RV-040k — INT — **V-RV-03**: `pytest tests/hooks/test_hook_worker.py -q`
- [x] T-070c — forwarder support closes (superseded by T-RV-040a-c)

### RW5 — RV-004 (P3) / T-090a: content-aware sync fingerprinting

- [x] T-RV-050a — S — `RENDER_FINGERPRINT_VERSION` + `hook_render_fingerprint()`
      in `wagents/hooks/registry.py`
- [x] T-RV-050b — S — `sync_hook_projection()` helper records
      `{registry_fp, content_sha256, render_version}` per harness and only
      skips re-render when the fingerprint *and* the on-disk content hash match
- [x] T-RV-050c..i [P] — A — wired through `sync_hook_projection()` for
      fully-owned hook destinations only: `cursor` (repo `hooks.json`),
      `github-copilot` (`.github/hooks/policy.json`), `codex-repo` /
      `codex-home` (merged hooks JSON). Claude, Gemini, and Grok remain
      full read-merge-write settings paths (intentionally uncached).
- [x] T-RV-050j [P] — T — apply-then-check skips re-render test
- [x] T-RV-050k [P] — T — `--check` fails (re-renders) when the on-disk file is
      corrupted/hand-edited even though the registry is unchanged
- [x] T-RV-050m — INT — **V-RV-04** + V-06
- [x] T-090a — registry sha256 skip re-render closes (superseded by
      `sync_hook_projection()`)

### RW6 — Closure

- [x] T-RV-060a — INT — V-01..V-12 + V-RV-01..05 run and recorded
- [x] T-RV-060b [P] — L0 — T-070c, T-090a, and all RV-* tasks checked in this file
- [x] T-RV-060c [P] — L0 — validation-matrix review-closure row updated
- [x] T-RV-060d [P] — L0 — tier-promotion smoke checklist documented (manual;
      no auto-promote — `hook_perf.tier` stays `legacy`)


## Post-Review Closure (RV-NEW-001..003)

Follow-up from `/review` session after RW0–RW6 landed. Default tier stays
`legacy` until V-RV-06 passes and maintainer runs tier-promotion checklist.

### RV-NEW-001 — warm worker stdout reset (P1 worker-tier gate)

- [x] T-RV-081a — D — reset `dispatcher._STDOUT_EMITTED = False` at start of
      `_run_request()` in `hooks/wagents-hook-worker.py`
- [x] T-RV-081b [P] — T — `test_worker_socket_sequential_single_policy_allows`
- [x] T-RV-081c [P] — T — `test_worker_socket_allow_after_bundle_allow`
- [x] T-RV-081d — INT — **V-RV-06**: sequential warm-socket allow regression

### RV-NEW-002 — sync wiring docs accuracy (P3)

- [x] T-RV-082a — L0 — dedupe misleading RW5 task rows; document owned vs merge
      harness wiring in this file
- [x] T-RV-082b [P] — L0 — `design.md` G7 owned-vs-merge note (T-RV-080a)

### RV-NEW-003 — forwarded-path timing (P3)

- [x] T-RV-083a — D — `_record_hook_timing(..., forwarded=True)` on successful
      `--worker-socket` forwards in `hooks/wagents-hook.py`
- [x] T-RV-083b [P] — T — `test_timing_forwarded_path_records_forwarded_flag`

### RW7 — Optional parent backlog (non-blocking)

- [x] T-RV-070a [P] — T-031b bundle fail-closed tests
- [x] T-RV-070b [P] — T-042b-g per-harness bundle snapshots
- [x] T-RV-070c [P] — OpenCode bridge bundle + worker-socket test
- [x] T-RV-070d [P] — T-080d research stop-verifier in-process when bundled
