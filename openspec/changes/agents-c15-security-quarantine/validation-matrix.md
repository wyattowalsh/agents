# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/50-config-safety/10-security-quarantine-checklist.md openspec/changes/agents-c15-security-quarantine` | No whitespace errors. |
| Register schema | `uv run pytest tests/test_distribution_metadata.py::test_mcp_and_quarantine_planning_manifests_cover_required_gates` | Existing quarantine manifest remains schema-covered. |
