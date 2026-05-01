# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/20-harness-registry/opencode.md planning/20-harness-registry/gemini-cli.md planning/20-harness-registry/antigravity.md openspec/changes/agents-c04-opencode-gemini-harness` | No whitespace errors. |
| Model-neutral guard | `uv run pytest tests/test_sync_agent_stack.py` | Required before code/config sync changes, not run for this planning pass. |
