# Validation Matrix

| Surface | Command | Expected Result | Notes |
| --- | --- | --- | --- |
| OpenSpec change | `uv run wagents openspec validate` | change + specs pass | **Wave 0 gate G0** |
| OpenSpec JSON | `uv run wagents openspec validate --format json` | `ok: true` | Preferred for automation |
| Asset validate (later) | `uv run wagents validate` | pass | Wave 2; not required to invent Python in W0 |
| Inventory + ensure tests (later) | `uv run pytest tests/test_installed_inventory.py tests/test_cursor_skill_ensure.py -q` | green | Gate G1a |
| Planner / recon / pin tests (later) | `uv run pytest tests/test_sync_desired_skills.py tests/test_skills_sync_pin_gate.py tests/test_harness_reconciliation.py -q` | green | Gate G1b |
| Ruff (later) | `uv run ruff check wagents/skill_coverage.py wagents/installed_inventory.py wagents/cli.py wagents/platforms/cursor.py scripts/generate_harness_reconciliation.py` | clean | After code lands |
| Cursor dry-run (later) | `uv run wagents skills sync --dry-run -a cursor --format json` | emits store/projection buckets; no OOM (≠137) | **No `--apply`** |
| Cleanup dry-run (later) | `uv run wagents skills cleanup --dry-run --format json` | healthy same-realpath; lazy hash | **No `--apply`** |
| Cross-agent smoke phase1 (later) | `/cross-agent-install-smoke` phase1 | green | Wave 2; phase2 only with `INSTALL_SMOKE=1` + temp HOME |

## Blockers

- Wave 0 evidence path: hooks on this machine may fail-closed on Shell; if
  `openspec validate` cannot run in-session, re-run from an operator shell and
  treat green JSON as G0.
- Live apply remains human-gated after Wave 2 — not a Wave 0 validation item.

## Deferred Checks

- Home mass projection ensure (apply gate only).
- Optional Crush/OpenCode projection policy (Phase D).
- Recon packet regen claiming Cursor `projection_missing` → 0 (post-apply only).

## Hard Stop Reminder

This change’s evidence path SHALL NOT run `skills sync --apply`, live
`npx skills add`, mass home symlink writes, or cleanup `--apply`.
