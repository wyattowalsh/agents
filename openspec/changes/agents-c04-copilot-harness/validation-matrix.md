# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/20-harness-registry/github-copilot-web.md planning/20-harness-registry/github-copilot-cli.md openspec/changes/agents-c04-copilot-harness` | No whitespace errors. |
| No fabricated skills | `uv run pytest tests/test_distribution_metadata.py::test_harness_fixture_support_covers_every_harness_without_tier_promotion` | Harness support remains fixture-grounded. |
