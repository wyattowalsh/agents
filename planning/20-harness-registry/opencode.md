# OpenCode Harness Fragment

## Support Posture

- Harness id: `opencode`
- Owner lane: `agents-c04-opencode-gemini-harness`
- Tier target: `validated` after fixture pass
- Current evidence: `opencode.json`, `.opencode/`, plugin arrays, DCP config, MCP launcher override, credential guard, and OpenCode skills.

## Projection Behavior

| Surface | Projection |
| --- | --- |
| Instructions | `instructions/opencode-global.md` via docs/instruction sync; do not edit here. |
| Skills | Repo and global skill paths where supported. |
| MCP | OpenCode MCP registry with local Chrome DevTools launcher preservation. |
| Plugins | Runtime plugins in `opencode.json`, TUI-only plugins in user TUI config. |
| DCP | Model-neutral `config/opencode-dcp.jsonc`. |

## Fixture Requirements

Required fixtures: model-neutral config check, plugin placement check, DCP model-neutral check, MCP launcher preservation, credential guard blocklist, and rollback.
