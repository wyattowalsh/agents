# Validation Matrix: External Repo Intake

| Surface | Command | Expected Result |
|---|---|---|
| OpenSpec | `uv run wagents openspec validate` | All OpenSpec changes and specs pass. |
| JSON artifacts | `uv run python - <<'PY' ...` count checks | Ledger and queue contain 93 repos, review tasks contain 651 tasks, quarantine handoff contains 4 records, and reconciliation has no duplicates or missing IDs. |
| C10 diff hygiene | `git diff --check -- <c10 paths>` | No whitespace errors in staged C10 files. |
| Existing registry tests | `uv run pytest tests/test_distribution_metadata.py::test_mcp_and_quarantine_planning_manifests_cover_required_gates` | Existing C15-adjacent manifest gates still pass. |

## Known External Blockers

- Full `uv run wagents validate` currently fails on unrelated `skills/chrome-devtools*` frontmatter before this lane's changes.
- `test_platform_overhaul_registries_validate_against_schemas` currently fails on unrelated dirty `config/plugin-extension-registry.json` schema drift before this lane's changes.
