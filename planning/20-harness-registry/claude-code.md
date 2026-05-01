# Claude Code Harness Fragment

## Support Posture

- Harness id: `claude-code`
- Owner lane: `agents-c04-claude-harness`
- Tier target: `validated` after fixture pass
- Current evidence: repo instructions, Claude plugin manifest, skills packaging support, hooks/settings conventions, and OpenSpec wrappers.

## Projection Behavior

| Surface | Projection |
| --- | --- |
| Instructions | `CLAUDE.md` and imported repo/global instructions. |
| Skills | Skills CLI or native plugin projection from canonical `skills/`. |
| MCP | Project/user MCP settings with one owner per server. |
| Plugins | `.claude-plugin/` marketplace adapter. |
| Hooks | Claude settings hooks from canonical hook registry. |

## Fixtures And Rollback

Required fixtures: instruction precedence, skill package dry-run, plugin manifest schema check, MCP merge preview, hook render preview, and rollback to previous settings snapshot.

## Caveats

Generated docs and root instruction files are downstream outputs and must not be hand-edited by this lane.
