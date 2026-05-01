# Cursor Editor Harness Plan

## Support tier

`repo-present-validation-required`

## Repo artifacts

- `.cursor/rules`
- `AGENTS.md`
- `mcp/`
- `skills/`

## Preferred extension lane

rules + AGENTS.md + skill-compatible CLI/docs

## Secondary lane

MCP configured project/global/nested

## Official / documented surfaces to model

- rules
- memories
- AGENTS.md
- MCP
- background agents

## Idiosyncratic considerations

- .cursorrules is deprecated.
- Background agents run remote isolated environments and require secret/prompt-injection safeguards.

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
