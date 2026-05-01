# Cherry Studio Harness Plan

## Support tier

`repo-present-validation-required`

## Repo artifacts

- `.cherry/presets`

## Preferred extension lane

presets/assistants + MCP UI presets; skill-like prompts where possible

## Secondary lane

MCP through Cherry Studio UI/built-in uv/bun

## Official / documented surfaces to model

- MCP UI
- assistant/agent presets
- built-in MCP environment

## Idiosyncratic considerations

- Cherry Studio may use built-in uv/bun rather than system uv/bun.
- Auto-install MCP is beta and should require explicit consent.

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
