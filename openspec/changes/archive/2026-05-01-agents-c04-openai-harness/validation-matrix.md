# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/20-harness-registry/chatgpt.md planning/20-harness-registry/codex.md openspec/changes/agents-c04-openai-harness` | No whitespace errors. |
| Registry tests | `uv run pytest tests/test_distribution_metadata.py::test_harness_surface_registry_splits_cloud_desktop_cli_and_editor_variants` | Harness split assumptions remain covered. |
