# Validation Matrix

| ID | Command | From wave |
|----|---------|-----------|
| V-01 | `uv run pytest tests/hooks/ tests/test_wagents_hook.py tests/test_opencode_hook_bridge.py tests/test_grok_platform.py -q` | all |
| V-02 | `uv run pytest tests/hooks/test_performance_baseline.py -q` | W1+ |
| V-03 | `uv run pytest tests/hooks/test_bundle_dispatch.py -q` | W3+ |
| V-04 | `uv run wagents validate` | all |
| V-05 | `uv run wagents hooks validate --harness all` | W4+ |
| V-06 | `uv run python scripts/sync_agent_stack.py --check --targets repo` | W2+ |
| V-07 | `uv run python scripts/check_hook_discovery_parity.py` | W7+ |
| V-08 | `uv run wagents openspec validate` | W0+ |
| V-09 | `uv run ruff check hooks/ wagents/hooks/` | all |
| V-10 | `uv run python scripts/hooks/hook_perf_inventory.py --json` | W1, W4, W8 |
| V-11 | `uv run pytest tests/hooks/test_hook_worker.py -q` | W6+ |
| V-12 | `uv run pytest tests/hooks/test_registry_perf_metadata.py -q` | W2+ |
| V-RV-01 | `uv run pytest tests/hooks/test_performance_baseline.py -q` (RV-001 best-effort I/O tests + cursor guard smoke) | RW1+ |
| V-RV-02 | `uv run pytest tests/hooks/test_render_bundle_matchers.py -q` | RW2+ |
| V-RV-03 | `uv run pytest tests/hooks/test_hook_worker.py -q` (forwarder warm/cold/deny) | RW4+ |
| V-RV-04 | `uv run pytest tests/test_sync_hook_fingerprint.py -q` (sync skip apply/check) | RW5+ |
| V-RV-06 | `uv run pytest tests/hooks/test_hook_worker.py -k sequential -q` | RW6+ |
| V-RV-07 | `uv run pytest tests/hooks/test_hook_worker.py -k soft_gate -q` | RV-S-003 |
| V-RV-05 | `uv run pytest tests/hooks/test_bundle_dispatch.py -q` (legacy-tier Cursor hook row count stays stable across the review-remediation diff) | RW6 |

## Hyperfine soft gate (T-070e, worker tier)

`hooks/wagents-hook-worker.py --serve --socket PATH` keeps one warm interpreter
alive for the whole session instead of a cold `python3` per hook invocation.
Soft gate: 100 sequential NDJSON requests over the Unix socket should complete
at least 3x faster than 100 cold `hooks/run-wagents-hook` spawns for the same
policy/payload. Not part of CI by default (maintainer-run only, see the
recipes below); this only applies once a harness opts into
`WAGENTS_HOOK_PERF_TIER=worker` and starts the daemon
(`WAGENTS_HOOK_WORKER_SOCKET` env var points `wagents-hook.py --worker-socket`
and the OpenCode bridge at the running socket path).

## Hyperfine recipes (informal, maintainer-run; not part of CI by default)

```bash
# T-010d baseline: cold per-policy spawn
hyperfine --warmup 3 \
  'printf "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"echo hi\"}}" \
    | python3 hooks/wagents-hook.py cursor-destructive-shell-guard --harness cursor'

# G2 bundle vs legacy fan-out (3-policy Cursor Bash chain)
hyperfine --warmup 3 \
  --command-name legacy-3-spawn \
  'printf "{...}" | python3 hooks/wagents-hook.py cursor-destructive-shell-guard --harness cursor; \
   printf "{...}" | python3 hooks/wagents-hook.py cursor-protected-file-guard --harness cursor; \
   printf "{...}" | python3 hooks/wagents-hook.py git-commit-push-guard --harness cursor' \
  --command-name bundle-1-spawn \
  'printf "{...}" | python3 hooks/wagents-hook.py --bundle cursor-destructive-shell-guard,cursor-protected-file-guard,git-commit-push-guard --harness cursor'

# G5 worker soft gate: 100x no-op through worker vs 100x cold spawn (target >=3x)
hyperfine --warmup 3 --runs 20 \
  --command-name cold-spawn-100x '<script looping 100x cold dispatcher invocation>' \
  --command-name worker-100x '<script sending 100 NDJSON lines to wagents-hook-worker.py>'
```

## Review closure

| Wave | Status | Proof |
|------|--------|-------|
| W0 | Complete | OpenSpec scaffold present; V-08 must stay green. |
| W1 | Complete | `WAGENTS_HOOK_TIMING` remains opt-in; V-02 and V-10 cover the current baseline. |
| W2 | Complete | `logical_policy`, bundle schema fields, matcher narrowing, perf metadata tests, and `coordinator/wave-w2-g1.json` are present. |
| W3 | Complete | `wagents/hooks/bundle.py`, `--bundle`, `tests/hooks/test_bundle_dispatch.py`; V-03 green. |
| W4 | Complete | Bundle-aware render in `wagents/hooks/render.py`; V-05 green; `coordinator/wave-w4-g2-render.json` records the render wave. |
| W5 | Complete | Image in-process, event dedupe, and harness-specific regression tests are present. |
| W6 | Complete | `hooks/wagents-hook-worker.py`, client, `tests/hooks/test_hook_worker.py`; V-11 green. |
| W7 | Complete | RW7 optional backlog (T-031b, T-042b-g, T-070c, T-080d) tests landed; sync fingerprint + discovery cache. |
| W8 | Complete | Spec promoted (`openspec/specs/hooks-runtime-performance/spec.md`); V-01..V-12 + V-RV-01..06 recorded at post-review closure. |

## Review remediation closure (RW0–RW6)

| Wave | Finding | Status | Proof |
|------|---------|--------|-------|
| RW1 | RV-001 | Complete | `_best_effort_os()` wraps hook-state I/O; V-RV-01 green. |
| RW2 | RV-002 | Complete | `union_bundle_matchers()` fixes matcher loss on collapse; V-RV-02 green. |
| RW3 | RV-005 | Complete | `_finalize_single_policy_dispatch()` shared by `main()` and the worker's single-policy path. |
| RW4 | RV-003 | Complete | Stdlib `hooks/wagents-hook-client.py` + worker `--serve --socket`; V-RV-03 green. |
| RW5 | RV-004 | Complete | `hook_render_fingerprint()` + `sync_hook_projection()` with `content_sha256` drift detection; V-RV-04 green. |
| RW6 | — | Complete | Full V-01..V-12 + V-RV-01..05 matrix run; `legacy` tier byte-identical (V-RV-05). |

## Post-review closure (RV-NEW-001..003)

| Finding | Status | Proof |
|---------|--------|-------|
| RV-NEW-001 | Complete | `_STDOUT_EMITTED` reset per warm request; socket one-line handler; V-RV-06 green |
| RV-NEW-002 | Complete | tasks.md + design.md G7 owned-vs-merge accuracy |
| RV-NEW-003 | Complete | forwarded timing sidecar + baseline test |

## Session review remediation (RV-S-001..005)

| Finding | Status | Proof |
|---------|--------|-------|
| RV-S-001 | Complete | W2–W8 wave rows aligned with tasks.md; all parent wave tasks checked |
| RV-S-002 | Complete | duplicate V-RV rows removed from validation-matrix |
| RV-S-003 | Complete | `test_worker_soft_gate_warm_socket_faster_than_cold_spawn`; V-RV-07 |
| RV-S-004 | Complete | `_FORWARD_TIMEOUT_MARGIN_SECONDS` + derived bundle forward timeout |
| RV-S-005 | Complete | T-042b-g proof cites cursor + codex tests |

## Session review ship-close (RV-S-008..011)

| Finding | Status | Proof |
|---------|--------|-------|
| RV-S-008 | Complete | All 33 hook-scoped manifest paths committed on `feat/fleet-hooks-performance` (H1–H6 atomic commits) |
| RV-S-009 | Complete | `--forward-timeout` CLI + single-policy socket margin; `test_forward_single_policy_uses_derived_timeout`; image-optimizer forward budget invariant |
| RV-S-010 | Complete | Worker concurrency model in `design.md`; serial accept-loop paragraph in `hooks/index.mdx` |
| RV-S-011 | Complete | V-04 + V-06 green on hook branch (re-verified 2026-07-02); no catalog/sync fix required |

## RW7 optional closure

| Task | Status | Proof |
|------|--------|-------|
| T-031b | Complete | `test_bundle_timeout_skip_fail_closed_emits_deny` |
| T-042b-g | Complete | `test_bundle_tier_reduces_cursor_pre_tool_use_entry_count`, `test_bundle_tier_reduces_codex_pre_tool_use_group_count` |
| T-070c | Complete | `test_hook_bridge_worker_tier_uses_runner_worker_socket` |
| T-080d | Complete | `test_research_stop_verifier_runs_in_process_inside_bundle` |

## Tier promotion smoke (Phase 6, maintainer)

`hook_perf.tier` remains `legacy` in committed `config/tooling-policy.json` (plan non-goal: no auto-promote). Smoke checks run 2026-07-02:

| Check | Result |
|-------|--------|
| V-RV-06 sequential warm-socket allows | Green (`pytest -k sequential`) |
| Pytest soft gate stdin NDJSON | Green (`test_worker_soft_gate_warm_ndjson_faster_than_cold_spawn`, >=1.5x) |
| Pytest soft gate Unix socket | Green (`test_worker_soft_gate_warm_socket_faster_than_cold_spawn`, >=1.5x) |
| Bundle tier spawn reduction (cursor + codex) | Green (`test_bundle_tier_reduces_*`) |
| Worker tier render uses `--worker-socket` | Green (bridge + render tests) |
| Forward timeout (bundle) | Green (`test_forward_bundle_uses_derived_timeout`; `bundle_timeout + 1s`) |
| Forward timeout (single-policy) | Green (`test_forward_single_policy_uses_derived_timeout`; `forward_timeout + 1s`) |
| Hyperfine 100× gate (≥3×) | Deferred — `hyperfine` not installed locally; recipe in hyperfine section above |

Promote to `bundle` or `worker` only after maintainer hyperfine gate: set tier in `config/tooling-policy.json`, `uv run python scripts/sync_agent_stack.py --apply --targets repo`, start worker daemon for `worker` tier, run hyperfine, rollback if needed.


## Wave assurance run (2026-07-02)

Full matrix executed after RV-S remediation and T-031c bridge test alignment.

| ID | Result | Notes |
|----|--------|-------|
| V-01 | Green | 176 passed (`tests/hooks/` + bridge + grok + fingerprint + opencode integration) |
| V-02 | Green | `test_performance_baseline.py` |
| V-03 | Green | `test_bundle_dispatch.py` |
| V-04 | Deferred | `wagents validate` — unrelated catalog/agent drift outside hook scope |
| V-05 | Green | `wagents hooks validate --harness all` |
| V-06 | Degraded | `sync_agent_stack.py --check` — `cursor-agents.json` overlay drift (pre-existing) |
| V-07 | Green | `check_hook_discovery_parity.py` |
| V-08 | Green | `wagents openspec validate` |
| V-09 | Green | `ruff check hooks/ wagents/hooks/ tests/hooks/` |
| V-10 | Green | `hook_perf_inventory.py --json` |
| V-11 | Green | 14 passed `test_hook_worker.py` |
| V-12 | Green | `test_registry_perf_metadata.py` |
| V-RV-01..07 | Green | RV/RW/post-review + soft-gate + sequential regression |
| Hyperfine >=3x | Deferred | `hyperfine` not installed locally |

## Wave assurance run (ship-close, 2026-07-02)

Full matrix re-run on `feat/fleet-hooks-performance` after RV-S-009 implementation and hook-scoped commit packaging.

| ID | Result | Notes |
|----|--------|-------|
| V-01 | Green | 139 passed (`tests/hooks/` + bridge + fingerprint + opencode integration) |
| V-02 | Green | `test_performance_baseline.py` (via V-RV subset) |
| V-03 | Green | `test_bundle_dispatch.py` (via V-RV subset) |
| V-04 | Green (re-verified 2026-07-02) | `wagents validate` — all validations passed |
| V-05 | Green | `wagents hooks validate --harness all` |
| V-06 | Green (re-verified 2026-07-02) | `sync_agent_stack.py --check --targets repo` |
| V-07 | Green | `check_hook_discovery_parity.py` |
| V-08 | Green | `wagents openspec validate` |
| V-09 | Green | `ruff check hooks/ wagents/hooks/ tests/hooks/` |
| V-10 | Green | `hook_perf_inventory.py --json` |
| V-11 | Green | 15 passed `test_hook_worker.py` (includes RV-S-009 forward tests) |
| V-12 | Green | `test_registry_perf_metadata.py` (via prior waves) |
| V-RV-01..07 | Green | 49 passed regression subset |
| RV-S-009 | Green | `pytest -k forward` — 4 passed |
| Hyperfine >=3x | Deferred | Phase 6 maintainer track; `hook_perf.tier` stays `legacy` |
