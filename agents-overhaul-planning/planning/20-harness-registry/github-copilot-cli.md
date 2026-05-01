# GitHub Copilot CLI Harness Plan

## Support tier

`repo-present-validation-required`

## Repo artifacts

- `.agents/plugins`
- `.github/`
- `skills/`

## Preferred extension lane

Copilot CLI skills

## Secondary lane

MCP for live GitHub/stateful systems

## Official / documented surfaces to model

- skills
- custom agents
- MCP
- slash commands

## Idiosyncratic considerations

- GitHub MCP may be configured by default; avoid duplicating unsafe GitHub MCP entries.
- Personal and project skill directories can collide.

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
