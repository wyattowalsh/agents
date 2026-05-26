# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec | `uv run wagents openspec validate --format json` | Pass | Validates this change and the wider OpenSpec set. |
| Runtime plugin metadata | `uv run pytest tests/test_distribution_metadata.py` | Pass | Confirms required runtime plugins and OCX exclusions. |
| Sync behavior | `uv run pytest tests/test_sync_agent_stack.py` | Pass | Confirms OpenCode plugin merging remains deterministic. |
| Repo assets | `uv run wagents validate` | Pass | Validates skill, agent, MCP, and related repo metadata. |
| OpenCode surfaces | `uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level both --harness opencode` | JSON output with expected project/global surfaces | Missing `.opencode/agents/*` remains acceptable for this change. |
| README generation | `uv run wagents readme --check` | Pass after generator source update | README is generated; update `wagents/cli.py` instead of hand-only edits. |
| OCX CLI | `ocx --version` | Version prints | Confirms OCX is available without adding it to `opencode.json`. |
| OCX receipts | `ocx verify` | All components verified | Confirms existing copied component hashes still match receipts. |
| npm metadata | `npm view <package> version dist-tags.latest repository.url --json` | Package metadata resolves | Confirms package names and latest versions at implementation time. |

## Blockers

- None for the scoped repo-managed implementation.

## Evidence Captured

- `opencode-rules` latest npm version: `0.6.4`.
- `opencode-terminal-progress` latest npm version: `0.5.0`.
- `ocx` latest npm version and installed version: `2.0.9`.
- OCX receipt verification passed without component updates.
