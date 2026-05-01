# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec validity | `uv run wagents openspec validate` | All OpenSpec changes and specs pass. |
| MCP planning diff hygiene | `git diff --check -- planning/35-mcp-audit openspec/changes/agents-c03-mcp-audit` | No whitespace errors in lane-owned files. |
| Existing MCP schema coverage | `uv run pytest tests/test_distribution_metadata.py::test_mcp_and_quarantine_planning_manifests_cover_required_gates` | Existing MCP/quarantine planning manifests remain valid. |
| Future smoke fixtures | `uv run pytest <mcp fixture tests>` | Required before any MCP support-tier promotion. |

No live MCP config apply or external install is part of this lane completion.
