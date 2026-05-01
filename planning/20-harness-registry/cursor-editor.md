# Cursor Editor Harness Fragment

## Support Posture

- Harness id: `cursor-editor`
- Owner lane: `agents-c04-cursor-harness`
- Tier target: `validated` after fixture pass
- Current evidence: `.cursor/` rules, commands, skills, and MCP config surfaces.

## Projection Behavior

| Surface | Projection |
| --- | --- |
| Rules/instructions | `.cursor/rules/` generated from canonical instruction fragments. |
| Commands | `.cursor/commands/` where supported. |
| Skills | `.cursor/skills/` from canonical skills only. |
| MCP | Cursor MCP config from canonical registry. |

## Fixtures And Rollback

Required fixtures: rule precedence, skill projection dry-run, MCP render preview, generated/canonical freshness, and rollback.
