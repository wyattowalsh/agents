# External Skill Evaluation

## Objective

Evaluate external skills/plugins before adoption.

## Evaluation rubric

| Dimension | Questions |
|---|---|
| Spec compatibility | Does it have valid SKILL.md? Are scripts/references/assets structured? |
| CLI robustness | Does it expose stable args, JSON output, exit codes, fixture mode? |
| Security | Does it execute shell commands? Access network? Touch secrets? |
| Supply chain | Is the source maintained, licensed, pinned, checksummed, signed? |
| Portability | Can Claude, Copilot, OpenCode, Cursor, and Codex use it? |
| Docs quality | Does it explain install, use, update, rollback, and risks? |
| Overlap | Does it duplicate an existing skill or MCP? |
| Testability | Can it run in CI without hidden services? |

## Output classification

- adopt.
- adapt.
- reference.
- watch.
- reject.
- replace-mcp.
