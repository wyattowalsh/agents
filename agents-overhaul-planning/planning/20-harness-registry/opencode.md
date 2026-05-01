# OpenCode Harness Plan

## Support tier

`repo-present-validation-required`

## Repo artifacts

- `.opencode/`
- `.opencode-plugin/`
- `opencode.json`
- `opencode-setup/`

## Preferred extension lane

OpenCode skills + plugins + instructions

## Secondary lane

MCP for live systems

## Official / documented surfaces to model

- skills
- agents
- plugins
- MCP
- config scopes
- instructions

## Idiosyncratic considerations

- OpenCode discovers .claude/skills and .agents/skills in addition to .opencode/skills.
- Config precedence/merge order must be tested with fixtures.

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
