# OpenAI Codex Harness Plan

## Support tier

`repo-present-validation-required`

## Repo artifacts

- `AGENTS.md`
- `.codex-plugin/`
- `instructions/`

## Preferred extension lane

AGENTS.md + skill-compatible docs/scripts + optional MCP docs server

## Secondary lane

MCP for developer docs/live APIs

## Official / documented surfaces to model

- AGENTS.md
- sandboxed tasks
- MCP config

## Idiosyncratic considerations

- Codex task evidence should include terminal logs/test outputs.
- Agent changes require human review before merge.

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
