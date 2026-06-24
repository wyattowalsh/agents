# Affected Surfaces

## Source Of Truth

- `AGENTS.md` — repository asset standards, supported agents, source-of-truth and generated-surface guidance.
- `instructions/global.md` and platform overlays — shared and platform-specific agent policy if public contributor guidance needs instruction updates.
- `skills/` — repo-owned skill source files and optional skill-local references, scripts, templates, and evals.
- `agents/` — repo-owned agent definitions and metadata.
- `mcp.json`, `mcp/`, and `config/mcp-registry.json` — MCP source and registry surfaces.
- `config/external-skills.md` — curated external skill source of truth.
- `wagents/external_skills.py` — parser for curated external skill commands and trust/status metadata.
- `wagents/site_model.py` — generated docs data model, supported agents, install commands, distribution metadata, and skill index rows.
- `wagents/docs.py` — generated docs pages, sidebar data, and public skill catalog pages.
- `wagents/rendering.py` — generated per-skill and per-agent page rendering.
- `wagents/catalog.py` — catalog node parsing if additional skill metadata extraction is required.
- `docs/src/components/SkillCatalog.astro` — searchable/filterable skill catalog UI.
- `docs/src/content/docs/start-here.mdx`, `docs/src/content/docs/cli.mdx`, and new public contributor docs — onboarding and contributor workflow.
- `README.md` generator sources if generated README content changes.
- `agent-bundle.json`, `.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/marketplace.json`, and `opencode.json` — distribution and harness metadata.
- `.github/workflows/ci.yml` and `.github/workflows/release-skills.yml` — validation and release gates if required checks change.
- `tests/` — site model, docs generation, external skill parser, distribution metadata, and no-local-path regression tests.
- `openspec/changes/oss-friendly-codebase-standardization/` — change-control artifacts for this work.

## Generated Outputs

- `README.md` from `uv run wagents readme` when README generation changes.
- `docs/src/content/docs/skills/*.mdx`.
- `docs/src/content/docs/external-skills.mdx`.
- `docs/src/content/docs/skills/all.mdx`.
- `docs/src/content/docs/skills/installed.mdx`.
- `docs/src/content/docs/skills/install.mdx`.
- `docs/src/generated-site-data.mjs`.
- `docs/src/generated-skill-indexes.mjs`.
- `docs/src/generated-sidebar.mjs`.
- `docs/public/generated-skill-indexes/*.json`.

## Local Or Private Inputs

- Installed skill inventory discovered from local harnesses.
- Local MCPHub config and tunnel credentials.
- Live user harness configs under home directories.

These may be inspected as evidence, but public docs and tracked generated indexes must not expose secrets or user-specific absolute paths as primary source labels.

## Tests

- `tests/test_site_model.py`
- `tests/test_docs.py`
- External skill parser tests, existing or new.
- `tests/test_distribution_metadata.py`
- Existing validation, README, docs, and package tests impacted by generator changes.

## Validation Commands

- `git status --short --branch`
- `uv run wagents openspec validate`
- `uv run wagents validate`
- `uv run pytest tests/test_site_model.py tests/test_docs.py`
- Parser-focused pytest for `wagents/external_skills.py`
- `uv run pytest tests/test_distribution_metadata.py`
- `uv run wagents readme --check`
- `uv run wagents docs generate --no-installed`
- Optional local-only inventory check: `uv run wagents docs generate --include-installed`
- `rg '/Users/|/home/|/private/' docs/src/content/docs docs/public/generated-skill-indexes`
- `cd docs && pnpm exec astro check`
- `cd docs && pnpm build`
- `uv run wagents package --dry-run` or targeted package dry-runs if packaging metadata changes
- `uv run wagents skills sync --dry-run`
- `git diff --check`
