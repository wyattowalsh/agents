# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec | `uv run wagents openspec validate` | Pass | Confirms the change artifacts are valid. |
| Asset validation | `uv run wagents validate` | Pass | Confirms repo asset definitions remain valid. |
| Sync check | `uv run python scripts/sync_agent_stack.py --targets repo,home --check` | Pass or only expected diffs after apply | Confirms generated repo and home surfaces are in sync. |
| Harness surfaces | `uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level both --harness claude-code claude-desktop chatgpt codex github-copilot-web github-copilot-cli opencode gemini-cli antigravity perplexity-desktop cherry-studio cursor` | Completes with documented blind spots only | Local discovery cannot prove app-only or cloud-hosted UI settings. |
| Whitespace | `git diff --check` | Pass | Catches trailing whitespace and patch issues. |

## Blockers

- None expected after build mode is active.

## Deferred Checks

- Do not claim proof for app-only or cloud-hosted blind spots that harness discovery cannot inspect locally.
