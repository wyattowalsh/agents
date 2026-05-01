# ChatGPT Harness Plan

## Support tier

`planned-research-backed`

## Repo artifacts

- `AGENTS.md`
- `docs/`
- `instructions/`

## Preferred extension lane

Custom GPT instructions + Actions/OpenAPI; Apps SDK where preview accepted

## Secondary lane

MCP via Apps SDK developer mode / app model

## Official / documented surfaces to model

- Custom GPTs
- Actions
- Apps SDK
- tools
- knowledge

## Idiosyncratic considerations

- GPT can use either apps or actions but not both at the same time.
- Public GPTs with actions require privacy policy URL.
- Apps SDK is preview; treat as experimental.

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
