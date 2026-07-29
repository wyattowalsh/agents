# Validation matrix: cursor-grok-high-pin

| Check | Command | Expected |
| --- | --- | --- |
| Validate | `uv run wagents validate` | no new Cursor pin failures |
| Pytest | `uv run pytest` focused pin/sync/hook tests | pass |
| Ruff | `uv run ruff check` on touched Python | clean |
| Ty | `uv run ty check` (gated sources) | clean when applicable |
| OpenSpec | `uv run wagents openspec validate` | change + live cursor-harness ok |
| Sync dry | `uv run python scripts/sync_agent_stack.py --targets home --platforms cursor --check` | allowlisted rule + managed agents; no orphan deletes |
| Sync apply | same with `--apply` after dry-run review | home rule + agents match pin |
| Hooks | render / fixture: Task rewrite fail-open; subagentStart deny non-allowlist | pass |
| Local CLI | inspect `~/.cursor/cli-config.json` | `exploreSubagentModel: "inherit"` |
| Local IDE | manual picker check | Grok 4.5 High (not Fast) |
| Local DB | RO only — do not write `state.vscdb` | optional key-length verify when idle |
