# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec status | `uv run wagents openspec status --change replace-package-version-check-mcp --format json` | `isComplete` is true | Confirms proposal, affected surfaces, design, validation matrix, tasks, and spec delta are present. |
| OpenSpec validation | `uv run wagents openspec validate` | All repo changes and specs pass | Required because this change modifies OpenSpec artifacts. |
| MCP registry projection | `just mcphub-generate-check` | Generated MCPHub settings match the registry | Confirms the replacement slug projects from source. |
| MCP settings invariants | `bash scripts/mcphub/validate-settings.sh` | exit 0 | Confirms auth and group structure remain valid. |
| Runtime smoke | `just mcphub-smoke` | package-version-check-mcp initializes through MCPHub | Uses local MCPHub runtime; failures should be classified separately from registry source correctness. |
| Repo harness sync | `uv run python scripts/sync_agent_stack.py --targets repo --check` | Generated repo harness surfaces are current | Do not hand-edit generated projections. |
| Asset validation | `uv run wagents validate` | pass | Covers skills, agents, catalog quarantine, and MCP-adjacent source validation. |
| Docs generation | `uv run wagents docs generate --no-installed --check` | Generated docs artifacts are current | Required because docs embed registry and research-skill references. |
| Docs build | `uv run wagents docs build` | Static docs build completes | Final link/build assurance for public docs. |

## Blockers

- None currently known for source-level validation.

## Deferred Checks

- Home sync is deferred unless the maintainer explicitly requests it.
- Live credentialed GitHub rate-limit behavior is deferred because optional credentials are user-owned environment values.
