# Dispatch: agents-c04-copilot-harness

## Child OpenSpec Change

`agents-c04-copilot-harness`

## Mission

Define GitHub Copilot Web and CLI projections without fabricating installed-skill support claims.

## Allowed Files And Directories

- `platforms/copilot/`
- `.github/instructions/`
- `.github/prompts/`
- `.github/skills/`
- `planning/20-harness-registry/github-copilot-*.md`
- `openspec/changes/agents-c04-copilot-harness/`

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- `.github/copilot-instructions.md` unless docs lane explicitly coordinates
- generated support matrices

## Dependencies

- `agents-c01-registry-core`
- `agents-c02-skills-lifecycle`

## Expected Artifacts

- Copilot projection fragments
- support-tier caveats
- fixtures for instruction and skill projection
- separate GitHub Copilot Web/Coding Agent and CLI records
- explicit no-fabricated-installed-skills caveat
- CLI-specific MCP/config blind-spot ledger

## Validation Commands

- `uv run wagents openspec validate`
- adapter fixture validation

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

## Expanded Surface Requirements

Use `planning/20-harness-registry/00-expanded-harness-surface-map.md` and `planning/20-harness-registry/01-harness-projection-contract.md` as inputs. Keep GitHub Copilot Web/Coding Agent prompts/instructions separate from GitHub Copilot CLI config and MCP behavior.
