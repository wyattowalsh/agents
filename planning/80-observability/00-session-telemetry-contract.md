# Session Telemetry Contract

## Scope

This contract defines session replay, run graph, token/cost telemetry, redaction, and retention fields for future harness and UX work. It does not enable telemetry collection in this pass.

## Session Replay Artifact

A session replay artifact contains:

- Session id, harness id, repo id, and timestamp range.
- Ordered events with type, actor, tool, command class, and redacted summary.
- File paths touched, not file contents, unless explicitly captured by a fixture.
- Validation results and commit ids when work is landed.
- Links to external artifacts by path or URI, with secret-safe labels.

## Run Graph Model

Nodes:

- User request.
- Planning decision.
- Subagent dispatch.
- Tool call.
- File change.
- Validation result.
- Review finding.
- Commit.

Edges:

- Depends on.
- Produced by.
- Reviewed by.
- Validated by.
- Superseded by.

## Token And Cost Fields

Telemetry records should support:

- Model or provider label when user-owned config permits recording it.
- Prompt, completion, and tool-token buckets when available.
- Estimated cost fields with explicit `estimated` flag.
- Unknown values represented as `null`, never guessed.

## Redaction And Retention

- Secret values, raw env values, tokens, cookies, profile paths, and private message contents are excluded.
- Local retention defaults to shortest useful window for debugging.
- Long-lived telemetry requires explicit opt-in and documented deletion path.
- External export is disabled by default.
