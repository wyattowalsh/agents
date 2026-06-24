# Proposal

## Problem

Agents currently have broad guidance to preserve state and ask clarifying questions, but there is no explicit repository-wide rule against adding migration, legacy, fallback, alias, dual-path, or compatibility logic by default. That gap causes unnecessary complexity when the current repository state and user request are the v1 ground truth and version control is already the rollback path for unshipped behavior.

## Intent

Add one concise canonical instruction that defaults agents to clean current-state implementations and requires concrete evidence before adding compatibility logic.

## Scope

- Update `instructions/global.md` with a `Compatibility Discipline` section.
- Propagate the canonical instruction through existing repo and home sync surfaces, especially OpenCode.
- Preserve existing dirty worktree changes unrelated to this instruction update.

## Out Of Scope

- Changing generated surfaces by hand.
- Adding new harness sync behavior or new instruction bridge files.
- Changing model, plugin, MCP, or runtime settings.

## Affected Users And Tools

- Repo maintainers and agents using `instructions/global.md` directly.
- Claude Desktop, Claude Code, ChatGPT, Codex, GitHub Copilot web/CLI, OpenCode, Gemini, Antigravity, Perplexity Desktop, Cherry Studio, Cursor, and Cursor agent surfaces that consume generated or synced instruction bridges.

## Generated Surfaces To Refresh

- Repo harness instruction/config surfaces from `scripts/sync_agent_stack.py --targets repo --apply`.
- Home harness instruction/config surfaces from `scripts/sync_agent_stack.py --targets home --apply`.

## Risks

- Generated surfaces may change beyond the new instruction if local sync state is stale.
- Some app-only or cloud-hosted harness surfaces remain discovery blind spots and cannot be proven by local file sync alone.
