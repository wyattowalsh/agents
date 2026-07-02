<!--
Agent change PR template. Delete sections that do not apply, but keep the
checklist — reviewers use it to confirm frontmatter, tool scope, and
cross-platform bridge parity.
-->

## Summary

<!-- What agent(s) changed and why, in 1-3 sentences. -->

## Type of change

- [ ] New agent definition (`agents/<name>.md`)
- [ ] Existing agent: system prompt/body change
- [ ] Existing agent: frontmatter change (`tools`, `model`, `permissionMode`, `mcpServers`, `memory`)
- [ ] OpenCode-only runtime overlay change (`instructions/opencode-agents-overlay.md`)

## Frontmatter checklist

- [ ] `name` matches filename (kebab-case)
- [ ] `description` is non-empty and describes when to invoke this agent
- [ ] `tools`/`disallowedTools` scoped to the minimum needed (no blanket "all tools" unless justified)
- [ ] No OpenCode-only keys (`mode`, `temperature`, `color`, `permission`) leaked into the portable `agents/<name>.md` frontmatter

## Validation run locally

- [ ] `uv run wagents validate`
- [ ] `uv run python scripts/sync_agent_stack.py --check --targets repo` (if this agent has platform-specific bridge behavior)
- [ ] `uv run wagents docs generate --no-installed` (if the agent has a docs page)
- [ ] `uv run pytest` (relevant subset)

## Cross-platform bridge notes

<!-- Does this agent behave the same across Claude Code, Codex, Cursor, OpenCode, Grok? Any harness-specific caveats? -->

## Security / permission notes

<!-- New MCP servers, elevated tool access, or credential handling? -->
