# GitHub Copilot CLI Harness Fragment

## Support Posture

- Harness id: `github-copilot-cli`
- Owner lane: `agents-c04-copilot-harness`
- Tier target: `repo-present-validation-required`
- Current evidence: CLI/global config planning, agents/skills symlink surfaces, and no-fabricated-inventory rule.

## Projection Behavior

| Surface | Projection |
| --- | --- |
| Instructions | CLI-specific instruction source requires docs/source verification. |
| Skills | Only discovered CLI-supported skills; zero installs must render zero support. |
| MCP | CLI MCP support requires first-party docs or fixture evidence. |

## Fixture Requirements

Required fixtures: empty installed-skill inventory, CLI config render preview, MCP support docs-source check, and rollback.
