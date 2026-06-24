# Validation Matrix

- Generated repo instruction surfaces: run `uv run python scripts/sync_agent_stack.py --targets repo --apply`; expect Codex/Copilot mirrors to refresh from canonical sources.
- Sync drift: run `uv run python scripts/sync_agent_stack.py --targets repo --check`; expect no repo instruction sync drift for managed targets.
- Asset formats: run `uv run wagents validate`; expect skills, agents, and repo assets to validate.
- OpenSpec artifacts: run `uv run wagents openspec validate`; expect OpenSpec changes and specs to validate.
- Generated README freshness: run `uv run wagents readme --check`; expect README to be fresh, or pre-existing unrelated drift to be reported.
- Stale include removal: run `rtk grep '@RTK\.md' 'instructions' '.github/copilot-instructions.md' 'AGENTS.md'`; expect no matches.
- Secret bypass persistence: run `rtk grep 'OPENCODE_ALLOW_SECRET_FILES=1.*zshrc|zshrc.*OPENCODE_ALLOW_SECRET_FILES=1' 'instructions' '.github/copilot-instructions.md' 'AGENTS.md'`; expect no matches.

## Known Constraints

- The worktree is already heavily dirty. Validation may report unrelated drift from pre-existing changes; preserve and report it rather than reverting.
