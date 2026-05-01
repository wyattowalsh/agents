# Claude Desktop Harness Fragment

## Support Posture

- Harness id: `claude-desktop`
- Owner lane: `agents-c04-claude-harness`
- Tier target: `repo-present-validation-required`
- Current evidence: desktop MCP config merge path and shared Chrome DevTools one-owner policy.

## Projection Behavior

| Surface | Projection |
| --- | --- |
| Instructions | Desktop prompt behavior remains a blind spot. |
| Skills | No default skill projection claim. |
| MCP | Global Claude Desktop MCP config merge with backup/rollback. |
| Plugins | Not claimed by this repo. |

## Fixtures And Rollback

Required fixtures: MCP merge preview, redacted auth/env output, no-skill-projection assertion, rollback snapshot, and idempotent re-run.

## Caveats

Claude Desktop must stay MCP/config-first until first-party evidence proves additional projection surfaces.
