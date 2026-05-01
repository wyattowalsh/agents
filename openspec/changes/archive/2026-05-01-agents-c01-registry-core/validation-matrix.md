# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec validity | `uv run wagents openspec validate` | All OpenSpec changes and specs pass. |
| Registry schema fixtures | `uv run pytest tests/test_distribution_metadata.py` | Registry-related structured manifests validate against canonical schemas. |
| Asset metadata | `uv run wagents validate` | Skills and agents validate after unrelated dirty asset issues are resolved. |
| Planning diff hygiene | `git diff --check -- config/schemas planning/20-harness-registry openspec/changes/agents-c01-registry-core` | No whitespace errors in lane-owned files. |
| Future docs consistency | `uv run wagents readme --check` | Required before publishing regenerated support claims. |

This lane freezes contracts only; it does not apply sync, mutate live config, or regenerate generated documentation.
