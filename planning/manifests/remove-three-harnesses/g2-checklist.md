# Gate G2 — SSOT + early Crush smoke

- [x] site_model.SUPPORTED_AGENTS and curated target validation dropped all three
- [x] platforms adapters unregistered; gemini/antigravity/copilot.py deleted
- [x] sync_agent_stack: no Gemini/Antigravity/Copilot writers; AITK uses `render_flat_mcp(..., harness="crush")`
- [x] Crush smoke: type stdio (mcphub_group_harness, mcphub_group_nlm)
- [x] mcp-registry: crush in chrome-devtools repo_mcp; removed harnesses stripped from exclude/ownership
- [x] hooks registries cleaned
- [x] AGENTS.md §2.4/§6 updated
- [x] OpenCode auth plugins intact
- [x] candidate wrappers preserved

Smoke:
```
agents ('claude-code', 'codex', 'crush', 'cursor', 'grok', 'opencode')
retired targets absent True
crush types {'stdio'}
```
