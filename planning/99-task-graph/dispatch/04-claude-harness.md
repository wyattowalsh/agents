# Dispatch: agents-c04-claude-harness

## Child OpenSpec Change

`agents-c04-claude-harness`

## Mission

Define Claude Code and Claude Desktop projection behavior for skills, MCP, instructions, plugins, hooks, and rollback fixtures.

## Allowed Files And Directories

- `.claude-plugin/`
- `planning/20-harness-registry/claude-*.md`
- `planning/30-adapters/`
- `openspec/changes/agents-c04-claude-harness/`
- lane-specific fixtures

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- generated support matrices

## Dependencies

- `agents-c01-registry-core`
- `agents-c02-skills-lifecycle`
- `agents-c03-mcp-audit`

## Expected Artifacts

- Claude support-tier records/fragments
- golden config fixtures
- rollback validation notes
- separate Claude Code and Claude Desktop surface records
- Claude Desktop MCP-first caveat with no default skill-projection claim
- Claude Code plugin/skills/hooks/MCP projection fixture plan

## Validation Commands

- `uv run wagents openspec validate`
- adapter fixture validation

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

## Expanded Surface Requirements

Use `planning/20-harness-registry/00-expanded-harness-surface-map.md` and `planning/20-harness-registry/01-harness-projection-contract.md` as inputs. Keep Claude Code and Claude Desktop separate: Claude Code may own skills/plugins/hooks where fixture-backed; Claude Desktop is MCP/config-first until first-party docs or fixtures prove more.
