# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/10-architecture/11-knowledge-graph-context-adoption.md openspec/changes/agents-c11-knowledge-graph-context` | No whitespace errors. |
| Future fixtures | `uv run pytest <graph/context fixture tests>` | Required before any implementation promotion. |
