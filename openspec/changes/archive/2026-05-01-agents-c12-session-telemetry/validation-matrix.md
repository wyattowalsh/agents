# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/80-observability/00-session-telemetry-contract.md openspec/changes/agents-c12-session-telemetry` | No whitespace errors. |
| Future redaction fixtures | `uv run pytest <telemetry fixture tests>` | Required before telemetry implementation. |
