# Python Library Preferences

Use this reference only when starting new Python work or choosing a default for
an unconstrained project. These are guided defaults, not mandatory replacements.

## Decision Rule

1. Prefer the repo's established stack when one exists.
2. Use this table only when the user asks for a recommendation or the project has no stronger convention.
3. Check `references/exceptions.md` before replacing a legacy or corporate-mandated stack.
4. Present trade-offs when the preference conflicts with local code, team skill, or deployment constraints.

## Preferred Defaults

| Purpose | Prefer | Usually instead of | Notes |
|---------|--------|--------------------|-------|
| Logging | `loguru` | ad hoc print logging | Keep stdlib `logging` when library compatibility or central logging config requires it. |
| Retries | `tenacity` | manual retry loops | Require bounded attempts, backoff, and retryable exception scope. |
| Progress bars | `tqdm` | print progress loops | Avoid noisy progress bars in non-interactive CI output. |
| Web APIs | `fastapi` | new Flask apps | Keep Flask for existing blueprint/middleware-heavy apps. |
| CLI tools | `typer` | new argparse/click CLIs | Keep `argparse` for zero-dependency scripts and `click` for advanced existing command groups. |
| DB migrations | `alembic` | manual SQL migration files | Pair with explicit migration review and rollback notes. |
| DB ORM | `sqlmodel` | raw SQLAlchemy for simple CRUD | Keep SQLAlchemy for advanced ORM/core patterns already in use. |
| UI/demos | `gradio` | new Streamlit demos | Keep local product UI frameworks when the demo is part of the app. |
| Numerics | `numpy` | manual math loops | Avoid adding heavy dependencies for trivial scalar math. |
| MCP servers | `fastmcp` | raw MCP protocol | Follow repo MCP conventions for `server.py`, `fastmcp.json`, and `uv`. |

## Anti-Patterns

- Do not rewrite working code solely to match this table.
- Do not present a preference as a hard rule.
- Do not add a library before checking whether the task can use existing dependencies.
