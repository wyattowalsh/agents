# Gemini CLI Harness Fragment

## Support Posture

- Harness id: `gemini-cli`
- Owner lane: `agents-c04-opencode-gemini-harness`
- Tier target: `validated` after fixture pass
- Current evidence: `GEMINI.md`, `.gemini/`, global Gemini settings surfaces, and Skills/OpenSpec wrapper planning.

## Projection Behavior

| Surface | Projection |
| --- | --- |
| Instructions | `GEMINI.md` imports repo `AGENTS.md` and global policy. |
| Skills | Skills CLI/symlink support where discovery confirms. |
| MCP | Gemini MCP settings from canonical registry. |
| OpenSpec | Wrapper skills and commands generated from canonical OpenSpec source. |

## Fixtures And Rollback

Required fixtures: instruction import check, MCP render preview, skills discovery/no-fabrication check, generated OpenSpec artifact freshness, and rollback.
