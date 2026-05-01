# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec validity | `uv run wagents openspec validate` | All OpenSpec changes and specs pass. |
| Inventory schema | `uv run pytest tests/test_distribution_metadata.py` | Repo-sync inventory and drift ledger fixtures match schema expectations. |
| Formatting | `uv run ruff check tests/test_distribution_metadata.py` | Distribution metadata tests remain lint-clean. |
| Asset metadata | `uv run wagents validate` | Skills and agents validate after unrelated dirty asset issues are resolved. |
| Planning diff hygiene | `git diff --check -- planning/00-overview planning/manifests openspec/changes/agents-c00-repo-sync` | No whitespace errors in lane-owned files. |

This lane does not perform live config sync, docs regeneration, or support-tier promotion.
