# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/20-harness-registry/perplexity-desktop.md planning/20-harness-registry/cherry-studio.md openspec/changes/agents-c04-experimental-harnesses` | No whitespace errors. |
| Blind-spot docs | `uv run wagents readme --check` | README remains fresh until docs consolidation is scheduled. |
