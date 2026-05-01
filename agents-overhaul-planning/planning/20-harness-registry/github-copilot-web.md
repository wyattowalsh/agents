# GitHub Copilot Web Harness Plan

## Support tier

`planned-research-backed`

## Repo artifacts

- `.github/`
- `AGENTS.md`
- `instructions/`

## Preferred extension lane

repository instructions + AGENTS.md + skills/custom agents where available

## Secondary lane

GitHub MCP / Actions / Apps integration

## Official / documented surfaces to model

- repository instructions
- AGENTS.md
- custom instructions
- MCP
- agents/skills in Copilot ecosystem

## Idiosyncratic considerations

- Nearest AGENTS.md precedence matters for nested docs.
- Instructions are always-on; skills should remain task-scoped.

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
