# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/20-harness-registry/claude-code.md planning/20-harness-registry/claude-desktop.md openspec/changes/agents-c04-claude-harness` | No whitespace errors. |
| Asset validation | `uv run wagents validate` | Asset metadata passes. |
