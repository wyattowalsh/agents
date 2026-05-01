# Validation Matrix: Agents Platform Overhaul

## Foundation Validation

| Surface | Command | Expected Result |
|---|---|---|
| OpenSpec changes | `uv run wagents openspec validate` | All root OpenSpec specs and changes pass. |
| Agent assets | `uv run wagents validate` | Existing skills and agents validate. |
| README generation | `uv run wagents readme --check` | README remains up to date until docs generation surfaces intentionally change. |
| Python tests | `uv run pytest` | Required when Python implementation or tests are touched. |
| Python lint | `uv run ruff check .` | Required when Python implementation or tests are touched. |
| Typecheck | `make typecheck` | Required when Python implementation or typed CLI surfaces are touched. |
| Registry schemas | schema validation tests | Required once non-Markdown schema files are added. |
| Docs generation | docs generation/checks | Required once docs-generation sources or docs artifacts change. |

## Current Read-Only Baseline

- `uv run wagents validate`: passed before foundation edits.
- `uv run wagents readme --check`: passed before foundation edits.
- `uv run wagents openspec validate`: passed before foundation edits for existing root OpenSpec assets.
- `uv run wagents openspec doctor`: passed and reported generated downstream OpenSpec artifacts present.

## Known Blockers

- Runtime plan mode allowed only Markdown edits during the first implementation attempt, blocking JSON schemas, JSON manifests, write-producing generation, and git commit.
- The requested `find .. -name AGENTS.md -print` preflight timed out after 120 seconds. Bounded repo-local discovery found `AGENTS.md` and `skills/nerdbot/AGENTS.md`.
