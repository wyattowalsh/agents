# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/50-config-safety/00-config-transaction-blueprint.md openspec/changes/agents-c06-config-safety` | No whitespace errors. |
| Future transaction fixtures | `uv run pytest <config safety fixture tests>` | Required before config apply code lands. |
