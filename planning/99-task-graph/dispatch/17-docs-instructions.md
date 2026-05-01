# Dispatch: agents-c08-docs-instructions

## Child OpenSpec Change

`agents-c08-docs-instructions`

## Mission

Own final generated docs and AI-instruction truth consolidation from manifests and fragments.

## Allowed Files And Directories

- `docs/`
- `instructions/`
- `planning/65-docs-and-instructions/`
- `openspec/changes/agents-c08-docs-instructions/`
- docs fixtures/tests

## Forbidden Shared Files

- `skills/`
- `mcp.json`
- `README.md`, `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` until registry/schema freeze is complete and consolidation is explicitly scheduled

## Dependencies

- `agents-c01-registry-core`
- all child lane fragments that feed docs truth

## Expected Artifacts

- docs artifact registry fragments
- AI instruction sync plan
- generated-doc ownership plan
- generated support-matrix ownership for all harness variants
- docs truth rule for desktop/cloud/CLI/editor split surfaces
- blind-spot labeling requirements for experimental harnesses

## Validation Commands

- `uv run wagents docs generate`
- `uv run wagents readme --check`
- `uv run wagents openspec validate`

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

## Expanded Surface Requirements

Use `planning/20-harness-registry/00-expanded-harness-surface-map.md` and `planning/20-harness-registry/01-harness-projection-contract.md` as inputs. Generated docs must distinguish Claude Code from Claude Desktop, ChatGPT from Codex, Copilot Web from CLI, Cursor Editor from Cursor Agent Web/CLI, and experimental desktop apps from validated harnesses.
