# Dispatch: agents-c04-openai-harness

## Child OpenSpec Change

`agents-c04-openai-harness`

## Mission

Define ChatGPT and Codex projection behavior for canonical skills, MCP profiles, plugin manifests, and instructions.

## Allowed Files And Directories

- `.codex-plugin/`
- `.agents/plugins/`
- `planning/20-harness-registry/chatgpt.md`
- `planning/20-harness-registry/codex.md`
- `openspec/changes/agents-c04-openai-harness/`
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

- OpenAI/Codex support-tier fragments
- plugin projection fixtures
- MCP/instruction projection notes
- separate ChatGPT and Codex support records
- ChatGPT app/desktop/MCP connector blind-spot ledger
- Codex plugin/config/skills fixture plan

## Validation Commands

- `uv run wagents openspec validate`
- adapter fixture validation

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

## Expanded Surface Requirements

Use `planning/20-harness-registry/00-expanded-harness-surface-map.md` and `planning/20-harness-registry/01-harness-projection-contract.md` as inputs. Do not treat ChatGPT app/desktop connector behavior as equivalent to Codex plugin/config behavior without first-party docs or fixture evidence.
