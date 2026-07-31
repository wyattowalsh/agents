# Pre-commit Optimization Runbook

Defines hook scopes, fast-vs-slow classification, and skip/trigger rules for
local pre-commit loops in this repo, so docs-heavy or skill-only edits do not
pay for the full validation matrix on every commit.

## Hook scopes

| Scope | Files | Typical hooks |
|-------|-------|----------------|
| Python source | Gated by `[tool.ruff].include` / `[tool.ty.src]` in `pyproject.toml` (`wagents/`, `scripts/`, `tests/`, `skills/nerdbot`, and among MCP only `mcp/source-url-health`) | `ruff check`, `ruff format --check`, `ty check` |
| Skills / agents | `skills/**`, `agents/**` | `wagents validate`, frontmatter/eval checks |
| Docs | `docs/**`, `*.mdx` | `wagents docs lint`, link checks (no full Astro build locally) |
| Config / registries | `config/*.json`, `openspec/**` | JSON schema checks, `wagents openspec validate` |
| Workflows | `.github/workflows/*.yml` | `actionlint` (skip on non-workflow commits) |

## Fast vs. slow hooks

**Fast (run on every commit, sub-second to a few seconds):**

- `ruff check` / `ruff format --check` (scoped to staged files)
- `wagents validate` (frontmatter-only checks, no docs build)
- JSON/YAML syntax checks

**Slow (skip on unrelated paths, run explicitly or in CI):**

- `uv run ty check` (config-driven / gated ty check)
- `uv run wagents docs build` (full Astro build + Playwright smoke)
- `actionlint` (only meaningful when `.github/workflows/*.yml` changed)
- `SKILL_PORTABLE_CI=1 uv run pytest tests/test_skill_portability.py ...` (packaging matrix)

## Skip/trigger rules

- If the diff touches **only** `docs/src/content/docs/**/*.mdx` or
  `docs/src/authoring/skills/**/*.mdx`, skip Python type-checking and the
  full Astro build; run `wagents docs lint` and `wagents docs generate --check`
  instead.
- If the diff touches **only** `skills/<name>/SKILL.md` or
  `skills/<name>/evals/*.json`, skip the packaging/portability matrix; run
  `wagents validate` and `wagents eval validate --format json` scoped to that
  skill.
- If the diff touches `.github/workflows/*.yml`, always run `actionlint`
  regardless of other skip rules — workflow syntax errors are cheap to catch
  locally and expensive to catch in CI.
- If the diff touches `config/hook-registry.json` or `wagents/hooks/**`,
  always run `uv run wagents hooks validate --harness all` — these are
  enforce-tier security guards and must never be skipped.

## Guarantees that never get skipped

Regardless of scope, these must run before every commit that touches
tracked source:

1. `uv run ruff check` on changed Python files
2. `uv run wagents validate` (structural frontmatter validation)
3. `git diff --check` (trailing whitespace / conflict markers)

## Local inner loop

Use the `just verify-fast` recipe (validate + lint + a fast pytest subset) as
the default pre-push check, and `just verify-all` (adds docs build + full
`ci-check`) before opening a PR that touches docs, workflows, or generated
surfaces. See `docs/runbooks/asset-authoring-workflow.md` for the full
authoring-to-merge sequence.
