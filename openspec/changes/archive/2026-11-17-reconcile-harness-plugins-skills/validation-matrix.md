# Validation Matrix

| Check | Command | Expectation |
|-------|---------|-------------|
| Regenerate matrix | `uv run python scripts/generate_harness_reconciliation.py` | writes redacted manifest |
| Manifest invariants | `uv run pytest tests/test_harness_reconciliation.py -q` | green |
| Asset validation | `uv run wagents validate` | passes |
| Catalog index parity | `uv run wagents catalog index --check --format json` | ok true |
| OpenSpec validation | `uv run wagents openspec validate` | passes |
| Default desired skill sync | `uv run wagents skills sync --dry-run --format json` | zero missing commands |

## Manual inspection expectations

- Inspect `summary.by_action` for remaining non-synced actions.
- Inspect `summary.skills.include_installed_missing_by_agent.grok` for the four
  optional Anthropic skills that remain local-only.
- Inspect Gemini extension rows before claiming extension validation because the
  local Gemini MCP config currently requires repair.
