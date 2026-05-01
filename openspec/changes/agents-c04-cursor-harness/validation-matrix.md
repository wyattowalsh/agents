# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/20-harness-registry/cursor-editor.md planning/20-harness-registry/cursor-agent-web.md planning/20-harness-registry/cursor-agent-cli.md openspec/changes/agents-c04-cursor-harness` | No whitespace errors. |
