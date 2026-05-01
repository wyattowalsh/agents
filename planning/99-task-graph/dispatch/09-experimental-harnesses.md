# Dispatch: agents-c04-experimental-harnesses

## Child OpenSpec Change

`agents-c04-experimental-harnesses`

## Mission

Classify experimental harnesses such as Perplexity Desktop, Cherry Studio, and any retained Crush-specific surfaces without overstating support.

## Allowed Files And Directories

- `.perplexity/`
- `.cherry/`
- `planning/20-harness-registry/perplexity-desktop.md`
- `planning/20-harness-registry/cherry-studio.md`
- `openspec/changes/agents-c04-experimental-harnesses/`

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- generated support matrices

## Dependencies

- `agents-c01-registry-core`

## Expected Artifacts

- experimental support-tier fragments
- caveats and validation gaps
- no default-install claims
- Perplexity Desktop docs/source lookup task and blind-spot record
- Cherry Studio MCP import/export fixture plan
- retain/experimental/unsupported decision for Crush if registry core keeps it in scope

## Validation Commands

- `uv run wagents openspec validate`

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

## Expanded Surface Requirements

Use `planning/20-harness-registry/00-expanded-harness-surface-map.md` and `planning/20-harness-registry/01-harness-projection-contract.md` as inputs. Experimental harnesses must not appear in generated support matrices as validated until source docs, local surface evidence, fixtures, and rollback paths exist.
