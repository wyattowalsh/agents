# Docs and AI Instructions CI

## Objective

Make README, docs, and AI instructions reflect registry truth.

## Files to validate

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`
- `.cursor/rules/**`
- `.opencode/**`
- `.antigravity/rules/**`
- `.perplexity/skills/**`
- `.cherry/presets/**`
- `instructions/**`
- `docs/**`

## Checks

- support matrix generated from harness registry.
- skill list generated from skill inventory.
- MCP list generated from MCP inventory.
- quickstart commands match CLI fixtures.
- no stable claims for experimental/unverified surfaces.
- OpenSpec active change links exist.

## Acceptance criteria

- `wagents docs generate` and `wagents docs check` or equivalent exist.
- CI fails if generated docs differ from committed docs.
