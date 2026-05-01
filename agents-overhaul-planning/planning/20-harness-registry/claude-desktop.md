# Claude Desktop Harness Plan

## Support tier

`planned-from-shared-artifacts`

## Repo artifacts

- `mcp/`
- `config/`
- `skills/`

## Preferred extension lane

Agent Skills where surfaced by client; otherwise Desktop Extensions/MCP

## Secondary lane

local MCP Desktop Extensions

## Official / documented surfaces to model

- MCP
- Desktop Extensions

## Idiosyncratic considerations

- Desktop extension packaging is separate from Claude Code plugin packaging.
- Skill support depends on client surface; do not assume parity with Claude Code.

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
