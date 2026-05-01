# Dispatch: agents-c04-opencode-gemini-harness

## Child OpenSpec Change

`agents-c04-opencode-gemini-harness`

## Mission

Define OpenCode, Gemini CLI, and Antigravity-adjacent projection behavior while preserving OpenCode model-neutral repo policy.

## Allowed Files And Directories

- `.opencode/`
- `.opencode-plugin/`
- `.gemini/`
- `.antigravity/`
- `opencode.json`
- `planning/20-harness-registry/opencode.md`
- `planning/20-harness-registry/gemini-cli.md`
- `planning/20-harness-registry/antigravity.md`
- `openspec/changes/agents-c04-opencode-gemini-harness/`

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- `GEMINI.md`
- `instructions/opencode-global.md` unless docs lane coordinates
- generated support matrices

## Dependencies

- `agents-c01-registry-core`
- `agents-c02-skills-lifecycle`
- `agents-c03-mcp-audit`

## Expected Artifacts

- OpenCode/Gemini/Antigravity projection fragments
- plugin placement notes
- rollback fixtures
- OpenCode model-neutral policy fixture
- Gemini CLI instruction/MCP/skill projection fragment
- Antigravity first-party-vs-repo-observed caveat ledger

## Validation Commands

- `uv run wagents openspec validate`
- adapter fixture validation

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

## Expanded Surface Requirements

Use `planning/20-harness-registry/00-expanded-harness-surface-map.md` and `planning/20-harness-registry/01-harness-projection-contract.md` as inputs. Preserve OpenCode model-neutral repo policy and keep Antigravity claims below `validated` until first-party docs or observed fixtures distinguish it from Gemini-compatible assumptions.
