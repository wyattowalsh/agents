# Affected Surfaces: Agents Platform Overhaul

## Source Of Truth

- `openspec/changes/agents-platform-overhaul/`
- `openspec/changes/agents-c*/`
- `planning/`
- `planning/manifests/`
- `planning/99-task-graph/dispatch/`
- `config/`
- `agent-bundle.json`
- `mcp.json`
- `opencode.json`
- `skills/`
- `agents/`
- `mcp/`
- `instructions/`
- `hooks/`
- `platforms/`
- `wagents/`
- `tests/`

## Shared Or Generated Surfaces

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
- `docs/`
- generated support matrices
- downstream OpenSpec-generated local command/skill artifacts under `.claude/`, `.cursor/`, `.opencode/`, `.github/`, `.agent/`, `.crush/`, `.codex/`, and `.gemini/`

## Merge Conflict Controls

- Child teams must not edit `README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, parent `openspec/changes/agents-platform-overhaul/tasks.md`, or generated support matrices directly.
- Child teams must write fragments, child OpenSpec artifacts, fixtures, and manifests under their assigned paths.
- Docs consolidation must happen after schema freeze and registry/manifests are stable.
- External repository work must remain intake-only until audit and conformance gates pass.

## Local Plan-Mode Note

The initial implementation was started while runtime plan mode still allowed only Markdown edits. Non-Markdown manifests and schema files are part of the intended foundation but require implementation mode outside plan-mode restrictions.
