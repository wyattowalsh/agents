# Gemini CLI Harness Plan

## Support tier

`repo-present-validation-required`

## Repo artifacts

- `GEMINI.md`
- `instructions/`
- `skills/`

## Preferred extension lane

Gemini extensions + commands + context files; skill wrapper scripts where possible

## Secondary lane

MCP servers in gemini-extension.json/settings

## Official / documented surfaces to model

- extensions
- custom commands
- context files
- MCP
- settings

## Idiosyncratic considerations

- Tool collision prefixes and include/exclude merging must be modeled.
- Extension configs can be overridden by workspace/user settings.

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
