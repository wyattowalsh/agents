# AI Agent Instructions

Generate exact, executable project guidance.

## Surfaces

- `AGENTS.md`: shared project guidance.
- Nested `AGENTS.md`: only where subtree rules differ.
- `CLAUDE.md`: bridge to `AGENTS.md` for Claude Code.
- `opencode.json`: project OpenCode wiring only when requested.
- Codex: root `AGENTS.md` is the default shared surface.

Instructions must not bypass approval gates, request secret access, disable credential guards, auto-deploy, create branches/worktrees, or ignore higher-priority instructions.
