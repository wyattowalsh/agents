# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/40-skills-ecosystem/10-skill-registry-intake.md openspec/changes/agents-c13-skill-registry-intake` | No whitespace errors. |
| Future candidate schema | `uv run python -m json.tool <candidate queue>` | Required before JSON candidate queue promotion. |
