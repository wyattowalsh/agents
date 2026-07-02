# Tool Result Compression (Opt-In)

Tracked `mcp/mcphub/mcp_settings.json` ships with compression **disabled**:

```json
"toolResultCompression": {
  "enabled": false,
  "minTokens": 2000,
  "maxOutputTokens": 1200,
  "strategy": "auto"
}
```

## When to enable locally

Enable only when long-running sessions show multi-kB tool payloads (repomix, docling, chrome-devtools, trafilatura) and context cost is painful. Hub-side compression trims results with `[mcphub:compressed-tool-result …]` markers.

## How to opt in (local only)

1. Edit **local** `.env.mcphub` (never commit).
2. Set MCPHub/system env vars per upstream MCPHub docs for `toolResultCompression.enabled=true` if your installed MCPHub version reads env overrides; otherwise toggle in a **local-only** settings overlay the maintainer documents in `docs/ai-tools/mcphub.md`.
3. Keep `minTokens: 2000` and `maxOutputTokens: 1200` conservative defaults.
4. Restart MCPHub: `just mcphub-down && just mcphub-up`.

## When to disable

- Debugging structured JSON tool results
- Investigating alleged truncation bugs
- Comparing raw vs compressed behavior — turn off for that session

Do **not** commit `enabled: true` in tracked `mcp_settings.json` without an OpenSpec change and maintainer approval.