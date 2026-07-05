# MCP Fallback

## When to use MCP instead of CLI

Use MCPHub `trafilatura` when:

- The harness has no Bash / shell access
- `doctor.py` reports missing binary and install is not possible in-session
- The user explicitly prefers MCP tools

## MCP tool

- Server: `trafilatura` (stdio via MCPHub)
- Primary tool: `fetch_and_extract` — download and extract in one step

## Skill-first default

On shell-capable harnesses (Cursor, Claude Code, Codex, Grok, OpenCode), prefer:

```bash
uv run python scripts/extract_url.py --url 'https://…'
```

Document when MCP fallback is used so the user knows which path ran.

## Research skill integration

`/research` Wave 2 deep-reads should prefer `/trafilatura` on shell harnesses before `trafilatura` MCP. See `skills/research/references/source-selection.md`.