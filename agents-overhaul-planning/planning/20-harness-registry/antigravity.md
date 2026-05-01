# Antigravity Harness Plan

## Support tier

`repo-present-experimental-contracts-unverified`

## Repo artifacts

- `.antigravity/rules`

## Preferred extension lane

rules/instructions only until official stable extension docs are verified

## Secondary lane

none until authoritative MCP/skills/plugin contract confirmed

## Official / documented surfaces to model

- rules/instructions: validation required

## Idiosyncratic considerations

- Official stable extension/plugin contracts were not verified in this research pass.

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
