# Docs Site Hierarchy Review

Date: 2026-06-29

Scope: sidebar navigation emission (`wagents/docs.py` to `docs/src/generated-sidebar.mjs`) and its relationship to the on-disk content tree under `docs/src/content/docs/`. This review is nav-only: the content folder layout was not restructured.

This tracked manifest records the durable review outcome. The related goal scratch file under `goals/docs-site-design-overhaul/review-hierarchy.md` is intentionally local-only because `/goals/` is ignored by this repository.

## Content Tree Inventory

Current generated tree under `docs/src/content/docs/`:

| Metric | Count |
| --- | ---: |
| MDX files | 792 |
| Directories | 9 |
| Max MDX path depth | 4 segments |

Root MDX pages:

- `index.mdx`
- `start-here.mdx`
- `cli.mdx`
- `contributing.mdx`
- `harness-support.mdx`

Top-level directories:

| Directory | MDX count | Role |
| --- | ---: | --- |
| `agents/` | 9 | Portable agent docs plus index |
| `mcp/` | 2 | MCP docs plus index |
| `skills/` | 367 | Catalog hub, install page, custom and external detail pages |
| `skill-research/` | 382 | Hidden research evidence pages |
| `hooks/` | 23 | Hook registry docs, URL-reachable but removed from sidebar |
| `harness-config/` | 4 | Harness config docs, URL-reachable but removed from sidebar |

Skills subtree:

```text
skills/
|-- install.mdx
`-- catalog/
    |-- index.mdx
    |-- custom/
    |   |-- index.mdx
    |   `-- <50 skill>.mdx
    `-- external/
        |-- index.mdx
        `-- <313 skill>.mdx
```

Depth distribution:

| Depth | Files | Examples |
| ---: | ---: | --- |
| 1 | 5 | `index.mdx`, `start-here.mdx`, `cli.mdx` |
| 2 | 421 | `agents/orchestrator.mdx`, `skill-research/research.mdx`, `hooks/index.mdx` |
| 3 | 1 | `skills/catalog/index.mdx` |
| 4 | 365 | `skills/catalog/custom/review.mdx`, `skills/catalog/external/vitest.mdx` |

## Complexity Sources Removed

Before simplification, the sidebar duplicated catalog discovery in several ways:

- Explicit custom skill lanes listed many individual `skills/catalog/custom/*` pages.
- User-invocable and convention labels created a second categorization layer beside the catalog pages.
- Hooks and Harness Config appeared as top-level sidebar groups even though they are support/reference surfaces.
- Deep catalog leaf pages were mirrored into shallow navigation, creating a large sidebar with poor scan value.

## Sidebar Simplification

The current generated sidebar keeps discovery surfaces broad and leaves catalog leaf discovery to Starlight autogeneration:

| Signal | Value |
| --- | ---: |
| `docs/src/generated-sidebar.mjs` lines | 43 |
| Explicit `skills/catalog/custom/*` slugs | 0 |
| User-Invocable / Convention sidebar labels | 0 |
| Top-level sidebar entries | 8 |
| Hooks / Harness Config top-level groups | 0 |

Target top-level sidebar:

- Home
- Start Here
- Skills
- Agents
- MCP
- CLI
- Contributing
- Harness Support

Skills sidebar entries:

- Catalog
- Install
- Custom, collapsed autogenerate from `skills/catalog/custom`
- External, collapsed autogenerate from `skills/catalog/external`

## Verification

Latest focused verification:

| Gate | Result |
| --- | --- |
| `uv run wagents docs generate --no-installed --check` | pass |
| `uv run pytest tests/test_docs.py tests/test_docs_link_hygiene.py tests/test_docs_compose.py -q --tb=short` | 54 passed |
| `uv run ruff check wagents/docs.py tests/test_docs.py tests/test_docs_link_hygiene.py` | pass |
| `uv run wagents validate` | pass |
| `cd docs && ./node_modules/.bin/astro check` | 0 errors, 0 warnings, 0 hints |
| `uv run wagents docs build` from clean docs output/cache | pass, internal links valid |

## Non-Goals

- No new routes such as `explore` or `discover`.
- No hand edits to generated catalog MDX under `docs/src/content/docs/skills/catalog/**`.
- No content tree restructuring; the change is limited to sidebar emission and generated docs output.
