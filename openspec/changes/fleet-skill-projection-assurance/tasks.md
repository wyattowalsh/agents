# Tasks: fleet-skill-projection-assurance

## Wave 0 — Contract freeze (this change)

- [x] W0-R1 [P] — RO scout ownership MDX + harness-surfaces; lock tier table in design
- [x] W0-R2 [P] — RO scout `installed_inventory.py`; document false-pass + hash hotspots
- [x] W0-R3 [P] — RO scout `cli.py` sync planner; list integration seams
- [x] W0-R4 [P] — RO scout reconcile OpenSpec + recon script; decide sibling extend
- [x] W0-S0 — Author proposal, design, tasks, affected-surfaces, validation-matrix, delta specs
- [x] W0-V — `uv run wagents openspec validate` green (G0)

## Wave 1a — Foundation (after G0; exclusive writers)

- [ ] W1-INV [P] — `wagents/skill_coverage.py` + `wagents/installed_inventory.py`: tiers, presence API, lazy cleanup hash; unit proof store-only ≠ Cursor `projection_present`
- [ ] W1-CUR [P] — `ensure_cursor_authoritative_links` in `wagents/platforms/cursor.py`; conflict matrix; leave `_sync_skill_symlinks` untouched; add `tests/test_cursor_skill_ensure.py` if TEST lane not started

## Wave 1b — Consumers (after G1a)

- [ ] W1-SYNC — `wagents/cli.py`: dry-run buckets `store_missing` / `projection_ensure` / `projection_blocked` / `internal_projection`; apply wires ensure after CLI batches; preserve plugin/direct-path skips
- [ ] W1-RECON [P] — recon script + packet: `store_missing_by_agent`, `projection_missing_by_agent`; Cursor not false-0
- [ ] W1-DOCS [P] — hand docs only: secondary/store ≠ durable synced
- [ ] W1-TEST [P] — focused pytest cases from acceptance list

## Wave 2 — Validate / human apply gate

- [ ] W2-SYN — OpenSpec tasks checked; accounting complete
- [ ] W2-VAL [P] — validate / openspec / dry-run planner / recon regen / cross-agent smoke phase1
- [ ] W2-APPLY — **blocked** until explicit user approval

## Stop Rules (all waves until apply gate)

- Do not run `wagents skills sync --apply`
- Do not run live `npx skills add`
- Do not mass-write home skill symlinks
- Do not run cleanup `--apply`
- Do not edit production Python in Wave 0
