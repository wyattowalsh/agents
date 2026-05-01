# Perplexity Desktop Harness Plan

## Support tier

`repo-present-experimental-contracts-unverified`

## Repo artifacts

- `.perplexity/skills`

## Preferred extension lane

skill-like docs/instructions if client supports them; otherwise no generated config writes

## Secondary lane

Perplexity MCP server as service integration, not Desktop extension contract

## Official / documented surfaces to model

- Perplexity MCP service docs; Desktop extension contract not verified

## Idiosyncratic considerations

- Distinguish Perplexity API/MCP integration from Perplexity Desktop extension capability.

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
