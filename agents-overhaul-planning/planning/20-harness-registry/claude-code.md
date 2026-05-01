# Claude Code Harness Plan

## Support tier

`repo-present-validation-required`

## Repo artifacts

- `.claude/`
- `.claude-plugin/`
- `CLAUDE.md`
- `skills/`
- `instructions/`

## Preferred extension lane

Agent Skills + Claude Code plugin

## Secondary lane

MCP for live systems

## Official / documented surfaces to model

- skills
- plugins
- subagents
- hooks
- MCP
- settings scopes
- memory

## Idiosyncratic considerations

- Subagents must explicitly receive/preload skills; do not rely on inherited parent skill context.
- Plugin subagents have constraints that differ from user/project subagents.
- Hooks are powerful and require explicit safety review.

## Required registry fields

- config scopes and path resolution.
- supported skill/plugin/MCP surfaces.
- install command strategy.
- environment variables and secret handling.
- generated file ownership.
- conformance fixture paths.
- rollback behavior.

## Required implementation tasks

- Validate actual repo artifacts for this harness.
- Add or update generated setup docs.
- Add golden fixtures for projected config/instructions.
- Add drift detection for manually edited files.
- Add support-tier badge to generated matrix.
- Add security notes for any tool execution or MCP usage.

## Acceptance criteria

- Harness doc references only verified surfaces or explicitly labels unverified/experimental surfaces.
- Adapter tests pass for this harness.
- Generated docs include install, update, validate, rollback, and troubleshooting steps.
