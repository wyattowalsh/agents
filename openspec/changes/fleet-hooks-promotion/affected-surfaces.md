# Affected Surfaces

## Registry & policy

- `config/hook-registry.json` — mega-bundle groups, Copilot dispatcher commands, image matcher
- `config/tooling-policy.json` — `hook_perf.tier` promotion (W5)
- `wagents/hooks/policies/destructive_shell_guard.py` (new)
- `wagents/hooks/policies/protected_file_guard.py` (new)
- `wagents/hooks/policies/__init__.py`
- `hooks/wagents-hook.py` — POLICIES entries for Copilot guards

## Render & sync projections

- `.cursor/hooks.json`, `.github/hooks/*.json`, `.claude/apm-hooks.json`, `.apm/hooks/*.json`
- `scripts/sync_agent_stack.py` output (repo targets)

## Tooling & CI

- `scripts/hooks/hook_perf_inventory.py` — `--tier`
- `scripts/hooks/hook_assurance.py` (new)
- `.github/workflows/ci.yml` — `hook-perf` job
- `docs/public/generated-reports/hook-perf-baseline-*.json`

## Tests & docs

- `tests/hooks/test_render_bundle_matchers.py`
- `tests/hooks/test_bundle_dispatch.py`
- `tests/hooks/test_policies_modules.py`
- `tests/hooks/test_hook_assurance.py` (new)
- `tests/hooks/test_hook_perf_inventory_tier.py` (new)
- `docs/runbooks/hook-performance.md` (new)
- `docs/src/content/docs/hooks/index.mdx`

## OpenSpec

- `openspec/changes/fleet-hooks-promotion/` (this change)
- Archive target: `openspec/changes/fleet-hooks-performance/` (W7)
