# Dispatch: agents-c04-cursor-harness

## Child OpenSpec Change

`agents-c04-cursor-harness`

## Mission

Define Cursor editor, Cursor Agent Web, and Cursor Agent CLI projections for skills, rules, MCP profiles, and rollback fixtures without collapsing desktop/editor behavior into cloud or CLI behavior.

## Allowed Files And Directories

- `.cursor/`
- `planning/20-harness-registry/cursor-*.md`
- `openspec/changes/agents-c04-cursor-harness/`
- lane-specific fixtures

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- generated support matrices

## Dependencies

- `agents-c01-registry-core`
- `agents-c02-skills-lifecycle`
- `agents-c03-mcp-audit`

## Expected Artifacts

- Cursor support-tier fragments
- projection fixtures
- rollback notes
- separate `cursor-editor`, `cursor-agent-web`, and `cursor-agent-cli` records
- web/CLI blind-spot ledger and docs-source checklist
- no default skill-projection claim for Cursor agent web/CLI until verified

## Validation Commands

- `uv run wagents openspec validate`
- adapter fixture validation

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

## Expanded Surface Requirements

Use `planning/20-harness-registry/00-expanded-harness-surface-map.md` and `planning/20-harness-registry/01-harness-projection-contract.md` as inputs. Cursor Editor may have repo-observed `.cursor/` fixtures; Cursor Agent Web and Cursor Agent CLI start as `planned-research-backed` blind-spot surfaces until docs or fixtures verify behavior.
