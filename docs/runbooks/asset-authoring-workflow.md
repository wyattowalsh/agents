# Asset Authoring Workflow Runbook

Standard sequence for authoring or updating a skill, agent, or MCP server in
this repo: `wagents new` → `wagents validate` → docs generation → tests →
package/install checks.

## 1. Scaffold

```bash
wagents new skill <name>          # -> skills/<name>/SKILL.md
wagents new agent <name>          # -> agents/<name>.md
wagents new mcp <name>            # -> mcp/<name>/ (server.py + pyproject.toml + fastmcp.json)
```

Use `--no-docs` on `wagents new skill` to skip the docs page scaffold for
internal-only skills (`metadata.internal: true`).

## 2. Author

- Follow the format rules in `AGENTS.md` §1 (required/optional frontmatter
  fields, body substitutions, naming conventions).
- For skills, add `skills/<name>/evals/evals.json` alongside the body —
  see the eval-adequacy risk tiers (`wagents eval adequacy --skill <name>`)
  to determine whether E4 (execution-based) signals are required.
- For agents, keep the frontmatter minimal and portable; OpenCode-only keys
  (`mode`, `temperature`, `color`, `permission`) belong in
  `instructions/opencode-agents-overlay.md`, not `agents/<name>.md`.
- For MCP servers, follow the FastMCP v3 conventions in `AGENTS.md` §2
  (`server.py` with `mcp = FastMCP("Name")`, `fastmcp.json`, `pyproject.toml`
  with `fastmcp>=2`, workspace member registration).

## 3. Validate structurally

```bash
uv run wagents validate            # frontmatter + schema checks across skills/agents
uv run wagents eval validate --format json   # eval JSON shape (skills only)
uv run wagents openspec validate   # if this change has an OpenSpec change directory
```

## 4. Generate docs

```bash
uv run wagents docs generate --no-installed   # regenerate MDX content pages
uv run wagents docs generate --check          # verify nothing is stale (CI parity)
uv run wagents readme                          # regenerate README if catalog inputs changed
```

Never hand-edit generated catalog pages, `docs/src/generated-sidebar.mjs`, or
`docs/public/generated-registries/skills-catalog-index.json`.

## 5. Test

```bash
uv run pytest                       # full suite, or a scoped subset for the changed area
uv run ruff check                   # lint changed Python
uv run ty check                     # type-check gated Python sources
```

For MCP servers, additionally run a FastMCP Inspector smoke test (handshake +
`list_tools`) and any server-specific pytest module under `tests/mcp/`.

## 6. Package / install checks

```bash
uv run wagents package <name> --dry-run    # skills: verify portability without creating a ZIP
uv run wagents skills sync --dry-run       # preview cross-harness install/sync commands
```

Do not run `wagents skills sync --apply` or live `npx skills add ...`
installs unless the maintainer explicitly requests them.

## 7. Open the PR

Use the matching change-type template
(`.github/PULL_REQUEST_TEMPLATE/{skill,agent,mcp,docs-infra}.md`) so
reviewers get consistent eval/docs/security evidence. See
`docs/runbooks/pre-commit-optimization.md` for which local checks to run
before pushing, based on the diff's scope.
