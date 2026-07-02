# Validation Matrix

| ID | Command | Waves |
|----|---------|-------|
| V-01 | `uv run pytest tests/hooks/ -q` | all |
| V-08 | `uv run wagents openspec validate` | W0+ |
| V-10 | `uv run python scripts/hooks/hook_perf_inventory.py --json` | W1, W4 |
| V-13 | `uv run python scripts/hooks/hook_assurance.py --json` | W6+ |

Hyperfine gate (W7): compare bundle p95 vs `hook-perf-baseline-bundle.json`; fail when regression exceeds 10%.
