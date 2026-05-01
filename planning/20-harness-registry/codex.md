# Codex Harness Fragment

## Support Posture

- Harness id: `codex`
- Owner lane: `agents-c04-openai-harness`
- Tier target: `validated` after fixture pass
- Current evidence: Codex plugin manifest, repo marketplace adapter, Codex config, and OpenSpec-compatible instructions.

## Projection Behavior

| Surface | Projection |
| --- | --- |
| Instructions | `AGENTS.md` and Codex-specific config/instruction bridge. |
| Skills | Skills CLI/plugin adapter where discovery confirms support. |
| MCP | Codex MCP config from canonical registry. |
| Plugins | `.codex-plugin/` and `.agents/plugins/marketplace.json`. |

## Fixtures And Rollback

Required fixtures: plugin manifest validation, MCP render preview, no fabricated skill inventory, config merge idempotence, and rollback to previous config.
