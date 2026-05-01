# Validation Matrix: Docs And Instructions Truth

| Surface | Command | Expected Result |
|---|---|---|
| OpenSpec | `uv run wagents openspec validate` | All OpenSpec changes and specs pass. |
| C08 tracked diff hygiene | `git diff --check -- <c08 paths>` | No whitespace errors in tracked C08 Markdown changes. |
| C08 staged diff hygiene | `git diff --cached --check` | No whitespace errors after C08 files are staged. |
| README freshness | `uv run wagents readme --check` | Detects whether root README is stale without editing it. |
| Docs generation | Not run in this pass | Deferred until generated docs are explicitly scheduled because it rewrites docs output. |

## Known External Blockers

- Shared generated docs and root docs are already dirty from unrelated work, so this pass records consolidation rules but does not refresh generated docs.
- `README.md`, `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` remain forbidden shared outputs without explicit scheduling.
