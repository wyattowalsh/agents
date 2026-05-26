# Proposal

## Problem

The shared instruction corpus contains rules that conflict with safer runtime policy: automatic commits are required even when the user did not request a commit, OpenCode secret-guard bypass guidance recommends a persistent shell-profile override, and generated Codex/Copilot surfaces inherit an unresolved `@RTK.md` include. The change affects shared instructions and generated downstream harness surfaces, so a direct edit without OpenSpec tracking would make instruction provenance and validation unclear.

## Intent

Tighten the canonical instruction stack so repo-managed guidance preserves user intent, protects secrets, avoids unsafe automatic git behavior, and keeps generated platform instructions in sync with the canonical source.

## Scope

- Update `instructions/global.md` with safer precedence, trust-boundary, orchestration, git, commit, and docs-lookup guidance.
- Remove the unresolved `@RTK.md` include from canonical and generated instruction surfaces.
- Update `instructions/opencode-global.md` so secret-guard bypass guidance is scoped and temporary, not shell-profile persistent.
- Regenerate repo-managed downstream instruction surfaces from `scripts/sync_agent_stack.py`.
- Update `AGENTS.md` instruction architecture notes and token-budget summary to match the new source behavior.

## Out Of Scope

- Creating branches, worktrees, commits, or pull requests.
- Reverting unrelated dirty worktree changes.
- Changing OpenCode model defaults, plugin configuration, or MCP topology.
- Hand-editing generated Codex/Copilot outputs after regeneration.

## Generated Surfaces To Refresh

- `instructions/codex-global.md` from `render_codex_global_instructions()`.
- `.github/copilot-instructions.md` and repo-local instruction mirrors from `uv run python scripts/sync_agent_stack.py --targets repo --apply`.
