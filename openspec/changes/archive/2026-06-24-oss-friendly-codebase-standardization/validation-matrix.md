# Validation Matrix

| Surface | Command | Expected Result | Notes |
| --- | --- | --- | --- |
| Worktree | `git status --short --branch` | Current branch and dirty state are known | Preserve unrelated dirty files. |
| OpenSpec | `uv run wagents openspec validate` | Pass | Required because this change touches generated docs, validation behavior, and public asset formats. |
| Asset validation | `uv run wagents validate` | Pass | Covers skill and agent frontmatter. |
| Site model and docs tests | `uv run pytest tests/test_site_model.py tests/test_docs.py` | Pass | Add focused tests for new public skill row fields and generated docs output. |
| External skill parser | Parser-focused pytest | Pass | Use existing parser tests if present or a new focused module. |
| Distribution metadata | `uv run pytest tests/test_distribution_metadata.py` | Pass | Protect supported agent and harness coverage. |
| README generation | `uv run wagents readme --check` | Pass | Required when generated README text or links change. |
| CI-parity docs generation | `uv run wagents docs generate --no-installed` | Pass | Matches current CI public docs behavior. |
| Installed-inventory diagnostics | `uv run wagents docs generate --include-installed` | Pass or documented local issue | Optional local check for redacted local inventory display. |
| Local path exposure | `rg '/Users/|/home/|/private/' docs/src/content/docs docs/public/generated-skill-indexes` | No unclassified public display leaks | Any match must be reviewed and classified. |
| Docs type/content check | `cd docs && pnpm exec astro check` | Pass | Required for Astro/Starlight generated docs changes. |
| Docs production build | `cd docs && pnpm build` | Pass | Proves production docs build readiness. |
| Package dry-run | `uv run wagents package --dry-run` or targeted package dry-runs | Pass if packaging metadata changes | Use targeted dry-runs if full dry-run is too broad. |
| External sync preview | `uv run wagents skills sync --dry-run` | Pass | Do not use `--apply` without explicit user intent. |
| Formatting and type checks | Ruff and ty commands from CI | Pass | Run when Python source changes. |
| Patch hygiene | `git diff --check` | Pass | No whitespace or patch formatting issues. |

## Deferred Checks

- Do not run live external skill installs.
- Do not apply `wagents skills sync --apply`.
- Do not promote external skills into repo-owned `skills/`.
- Do not edit or print local secrets.
- Do not delete uncertain dirty-tree files.
