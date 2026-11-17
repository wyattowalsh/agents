# Affected Surfaces

## Source

- `hooks/wagents-hook.py`
- `hooks/run-wagents-hook`
- `hooks/wagents-hook-worker.py` (new, optional/default-off)
- `hooks/wagents-hook-client.py` (new, stdlib-only forwarder for `--worker-socket`; RV-003)
- `wagents/hooks/bundle.py` (new)
- `wagents/hooks/render.py`
- `wagents/hooks/registry.py` (RV-004: `RENDER_FINGERPRINT_VERSION`, `hook_render_fingerprint()`)
- `wagents/hooks/merge.py`
- `wagents/image_inputs.py`
- `wagents/platforms/codex.py`
- `wagents/platforms/cursor.py`
- `wagents/platforms/claude.py`
- `wagents/platforms/gemini.py`
- `wagents/platforms/copilot.py`
- `wagents/platforms/grok.py`
- `wagents/platforms/opencode.py`
- `platforms/opencode/plugins/wagents-hook-bridge.ts`
- `config/hook-registry.json`
- `config/schemas/hook-registry.schema.json`
- `scripts/hooks/hook_perf_inventory.py` (new)
- `scripts/sync_agent_stack.py`
- `scripts/check_hook_discovery_parity.py`
- `skills/research/scripts/research_hook.py`
- `.github/hooks/policy.json` (post-edit-quality merge)
- `hooks/post-edit-quality.sh` (new)

## Tests

- `tests/hooks/test_performance_baseline.py` (new)
- `tests/hooks/test_bundle_dispatch.py` (new)
- `tests/hooks/test_hook_worker.py` (new)
- `tests/hooks/test_registry_perf_metadata.py` (new)
- `tests/hooks/test_render_bundle_matchers.py` (new, review-remediation RV-002)
- `tests/test_sync_hook_fingerprint.py` (new, review-remediation RV-004)
- `tests/hooks/test_render_cursor.py`
- `tests/hooks/test_render_codex.py`
- `tests/hooks/test_render_claude.py`
- `tests/hooks/test_render_gemini.py`
- `tests/hooks/test_enforce_fail_closed.py`
- `tests/hooks/test_opencode_bridge_integration.py`
- `tests/test_wagents_hook.py`
- `tests/test_opencode_hook_bridge.py`
- `tests/test_grok_platform.py`
- `tests/test_sync_agent_stack.py`
- `tests/fixtures/hooks/*.json` (new)

## Docs

- `docs/src/content/docs/hooks/index.mdx` (hub perf section)
- `openspec/specs/hooks-runtime-performance/spec.md` (promoted at W8)

## OpenSpec

- `openspec/changes/fleet-hooks-performance/` (this change)
- `openspec/changes/fleet-hooks-performance/coordinator/*.json` (wave manifests)

## Out of scope generated artifacts

- `.crush/`, `.agent/`, Antigravity, Cherry Studio surfaces (no hook support).
