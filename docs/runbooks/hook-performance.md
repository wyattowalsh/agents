# Hook performance runbook

Maintainer workflow for fleet hook spawn budgets and tier promotion.

## Inventory

```bash
# Legacy-tier spawn totals (rollback reference)
uv run python scripts/hooks/hook_perf_inventory.py --json

# Active bundle-tier totals (matches config/tooling-policy.json hook_perf.tier)
uv run python scripts/hooks/hook_perf_inventory.py --tier bundle --json
```

Committed baselines: `docs/public/generated-reports/hook-perf-baseline-legacy.json` and `hook-perf-baseline-bundle.json`.

## Assurance

```bash
uv run python scripts/hooks/hook_assurance.py --json
```

Fails when Cursor/Codex PreToolUse spawns exceed budget (3) or Copilot exceeds 2 under the active tier.

## Promotion (repo)

1. Update `config/tooling-policy.json` → `hook_perf.tier`.
2. `uv run python scripts/sync_agent_stack.py --apply --targets repo`
3. `uv run wagents apm materialize`
4. Regenerate bundle baseline JSON and run `scripts/hooks/hook_assurance.py`.

OpenSpec: `openspec/changes/fleet-hooks-promotion/` (bundle promotion v2), `openspec/changes/fleet-hooks-performance/` (implementation program).

Optional latency checks: hyperfine per `openspec/changes/fleet-hooks-performance/validation-matrix.md` when `hyperfine` is installed locally or in CI.
