# ACP stdio (optional long-lived driver)

Use when the parent needs streaming multi-turn control without repeated cold starts. **Official** pattern from x.ai docs — not a repo wrapper.

```bash
grok agent stdio
```

Runs JSON-RPC over stdin/stdout. Parent spawns the process and sends `initialize`, `authenticate`, `session/new`, `session/prompt` per the x.ai headless scripting guide.

Full Node example: https://docs.x.ai/build/cli/headless-scripting (ACP section).

## When to prefer ACP over `-p`

- Many tune rounds on one session with streaming consumption
- IDE-style tool already speaks ACP

## When to prefer `-p`

- Fleet parallel waves (one subprocess per node)
- Simple bash dispatch from Codex/OpenCode
- Task graphs with independent worktrees

Always pass `--no-auto-update` on automation paths documented by x.ai for headless and ACP.