# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| JSON configs | `jq empty opencode.json ~/.config/opencode/opencode.json ~/.config/opencode/tui.json` | All configs parse | Validates repo and live OpenCode JSON. |
| Distribution tests | `uv run pytest tests/test_distribution_metadata.py` | Pass | Covers runtime plugin inventory and TUI-only exclusion rules. |
| Agent assets | `uv run wagents validate` | Pass | Ensures changed instructions/docs did not break asset validation. |
| OpenSpec | `uv run wagents openspec validate` | Pass | Ensures this change is structurally valid. |
| Whitespace | `git diff --check` | Pass | Catches trailing whitespace and patch issues. |
| OpenCode startup | `opencode --print-logs --log-level DEBUG models anthropic` | No plugin load failures | Langfuse env warnings may be expected if keys are unset. |

## Blockers

- None known.

## Deferred Checks

- Do not create scheduler jobs during validation.
- Do not add CodeMCP workflow plugins or run broad CodeMCP setup unless the user explicitly re-approves local workflow-state artifacts.
