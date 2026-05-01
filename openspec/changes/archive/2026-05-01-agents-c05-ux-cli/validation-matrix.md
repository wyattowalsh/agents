# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/90-ui-ux/00-cli-output-contracts.md openspec/changes/agents-c05-ux-cli` | No whitespace errors. |
| Future golden snapshots | `uv run pytest <cli snapshot tests>` | Required before CLI output implementation changes. |
