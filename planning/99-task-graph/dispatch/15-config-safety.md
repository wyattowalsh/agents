# Dispatch: agents-c06-config-safety

## Child OpenSpec Change

`agents-c06-config-safety`

## Mission

Define transaction-safe config preview/apply/rollback, backup snapshots, redaction, sandboxing, policy-as-code, and supply-chain controls.

## Allowed Files And Directories

- `config/`
- `hooks/`
- `planning/50-config-safety/`
- `openspec/changes/agents-c06-config-safety/`
- transaction fixtures/tests

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- live user config outside repo

## Dependencies

- `agents-c01-registry-core`
- `agents-c03-mcp-audit`
- `agents-c15-security-quarantine`

## Expected Artifacts

- transaction model
- redaction model
- sandbox profiles
- policy exception workflow
- global desktop config preview/apply/rollback rules
- per-harness secret redaction fixture requirements
- live user config no-touch policy for planning and dry-runs

## Validation Commands

- `uv run pytest`
- `uv run ruff check .`
- `make typecheck`
- `uv run wagents openspec validate`

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

## Expanded Surface Requirements

Use `planning/20-harness-registry/00-expanded-harness-surface-map.md` and `planning/20-harness-registry/01-harness-projection-contract.md` as inputs. Desktop/global surfaces such as Claude Desktop, ChatGPT, Copilot, Gemini, Antigravity, OpenCode, Perplexity Desktop, Cherry Studio, Cursor, and Crush require previews, backups, redaction, explicit approval, and rollback before apply.
