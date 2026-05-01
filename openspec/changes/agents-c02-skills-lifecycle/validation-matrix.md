# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec validity | `uv run wagents openspec validate` | All OpenSpec changes and specs pass. |
| Asset metadata | `uv run wagents validate` | Skills and agents validate after any unrelated dirty skill issues are resolved. |
| Planning diff hygiene | `git diff --check -- planning/40-skills-ecosystem openspec/changes/agents-c02-skills-lifecycle` | No whitespace errors in lane-owned files. |
| Future skill fixture gate | `uv run wagents package <skill> --dry-run` | Required before any skill promotion. |
| Future script fixture gate | `uv run pytest <lane fixture tests>` | Required before script-backed capabilities are promoted. |

No external skill install or vendoring command is part of this lane completion.
