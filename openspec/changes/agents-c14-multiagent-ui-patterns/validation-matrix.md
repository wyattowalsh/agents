# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/90-ui-ux/10-multiagent-ui-patterns.md openspec/changes/agents-c14-multiagent-ui-patterns` | No whitespace errors. |
| Future UX implementation | `uv run pytest <ux fixture tests>` | Required before UI code changes. |
