---
title: "Research journal — KB wave 11"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 11 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave11-gap-sweep-2026-06-25
original_location: "~/.grok/research/kb-wave11-gap-sweep-2026-06-25.md"
---

# Research journal — KB wave 11

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 11 | Theme: tooling docs and thin page refresh
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 11 — tooling docs and thin page refresh`

## G0 brief

Gap sweep deepened uv/ruff/ty tooling evidence, Obsidian properties pointers, and fresh CI job capture; refreshed repo-map evidence for waves 03–10.

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `ci-workflow-jobs-capture-w11` | `kb/raw/captures/ci-workflow-jobs-capture-w11.md` |
| worker | `pyproject-tooling-capture-w11` | `kb/raw/captures/pyproject-tooling-capture-w11.md` |
| worker | `uv-llms-index-extract-w11` | `kb/raw/extracts/uv-llms-index-extract-w11.md` |
| worker | `external-tooling-docs` | `kb/raw/sources/external-tooling-docs.md` |
| worker | `obsidian-properties-capture-w11` | `kb/raw/sources/obsidian-properties-capture-w11.md` |

## Ingest queue

- `raw`: added 4 sources (`uv-llms-index-extract-w11`, `pyproject-tooling-capture-w11`, `ci-workflow-jobs-capture-w11`, `obsidian-properties-capture-w11`).

## Capture evidence (excerpts)

### `ci-workflow-jobs-capture-w11`

# CI Workflow Jobs Capture W11

Fresh read-only capture from `.github/workflows/ci.yml` and `.github/workflows/release-skills.yml` on 2026-06-25. Supersedes stale job lists in `ci-release-workflows-source.md` where they diverge.

## `ci.yml` jobs (7)

| Job | Timeout | Primary commands |
|-----|---------|------------------|
| `lint` | 10m | `uv run ruff check`; `uv run ruff format --check` |
| `typecheck` | 10m | `uv run ty check --output-format github --no-progress` |
| `test` | 15m | `uv run pytest --cov=wagents --cov-report=term-missing` |
| `validate` | 25m | `wagents validate`; `readme --check`; `apm materialize --check`; `apm doctor`; curated pytest slice; `openspec validate`; `skills sync --dry-run`; `catalog index --check` |
| `apm` | 15m | `apm audit --ci --no-drift`; conditional frozen `apm install` |
| `wagents-wheel` | 15m | `uv build`; `uv tool install` wheel; `wagents self doctor`; `wagents validate` |
| `docs` | 30m | `wagents docs generate --no-installed`; catalog index check; `docs compose --check-composed --min-pct 100`; `docs lint \|\| true`; Astro check; `pnpm build` |

Shared bootstrap: composite `.github/actions/setup-uv`. Top-level `permissions: {}` with per-job `contents: read`. PR concurrency `cancel-in-progress: true`.

## Validate job curated pytest slice (explicit paths)

```
tests/test_skills_catalog_schemas.py
tests/test_catalog_index_parity.py
tests/test_skill_index.py
tests/test_authoring_sync.py
tests/test_apm_materialize.py
tests/test_wagents_self.py
```

## Interpretation

- Full pytest coverage is **not** in the validate job; `test` job runs full suite with coverage.
- Docs compose 100% gate is docs-job only (not validate job).
- `wagents docs lint` remains non-blocking (`|| true`).

### `pyproject-tooling-capture-w11`

# Pyproject Tooling Capture W11

Read-only capture from `pyproject.toml` on 2026-06-25. Aligns repo gates with upstream Ruff/ty/uv configuration semantics documented in `external-tooling-docs`.

## Ruff (`[tool.ruff]`)

| Setting | Value |
|---------|-------|
| `target-version` | `py313` |
| `line-length` | `120` |
| `required-version` | `>=0.11` |
| `preview` | `true` |
| `include` | `wagents/**`, `tests/**`, `scripts/**`, `skills/**/scripts/**`, `skills/nerdbot/src/**`, `hooks/wagents-hook.py` |
| `extend-exclude` | `mcp/**`, `skills/**/evals/**` |
| `select` | `E`, `F`, `I`, `UP`, `B`, `SIM`, `C4`, `RUF`, `TC`, `PT`, `RET` |
| Notable per-file ignores | `scripts/validate/**` → `E402`; `skills/**/scripts/**` → `E402`, `E501`, … |

CI runs: `uv run ruff check` and `uv run ruff format --check` (`.github/workflows/ci.yml` lint job).

## Ty (`[tool.ty]`)

| Setting | Value |
|---------|-------|
| `environment.python-version` | `3.13` |
| `environment.root` | `[".", "skills/nerdbot/src"]` |
| `environment.extra-paths` | `skills/skill-creator/scripts`, `skills/nerdbot/scripts` |
| `analysis.allowed-unresolved-imports` | `audit`, `progress`, `package`, `asset_toolkit.**`, `kb_bootstrap`, `kb_inventory`, `kb_lint` |
| `src.include` | `wagents`, `scripts`, `tests`, `skills/nerdbot/src`, `skills/nerdbot/scripts` |
| `src.exclude` | `scripts/validate/**`, `tests/docs_ui/**` |
| `overrides` | `tests/**` → `possibly-unresolved-reference = warn` |
| `terminal.error-on-warning` | `true` |
| Dev pin | `ty==0.0.52` in `[dependency-groups] dev` |

CI runs: `uv run ty check --output-format github --no-progress` (typecheck job).

### `uv-llms-index-extract-w11`

# UV Llms Index Extract W11

Normalized extract from `https://docs.astral.sh/uv/llms.txt` fetched 2026-06-25. External evidence only; repo `pyproject.toml` and `Makefile` remain authoritative for commands.

## Index highlights

| Section | Representative paths |
|---------|---------------------|
| Getting started | `getting-started/features`, `installation`, `first-steps` |
| Guides | `guides/projects`, `guides/scripts`, `guides/tools`, `guides/package` |
| Integrations | `guides/integration/github`, `guides/integration/pre-commit`, `guides/integration/docker` |
| Projects | `concepts/projects/dependencies`, `concepts/projects/sync`, `concepts/projects/workspaces` |
| Pip interface | `pip/packages`, `pip/compile`, `pip/environments` |
| Reference | `reference/cli`, `reference/settings`, `reference/environment` |

## Quoted guidance

> uv includes both a pip-compatible CLI (prepend `uv` to a pip command, e.g., `uv pip install ruff`) and a first-class project interface (e.g., `uv add ruff`) complete with lockfiles and workspace support.

> When fetching documentation, use explicit `index.md` paths for directories, e.g., `https://docs.astral.sh/uv/concepts/projects/dependencies/index.md`.

## Repo alignment notes

| Upstream concept | Repo surface |
|------------------|--------------|
| `uv run` project commands | CI `.github/actions/setup-uv` + `uv run wagents`, `uv run pytest`, `uv run ruff check` |
| Workspaces | `[tool.uv.workspace] members = ["mcp/mcphub"]` in `pyproject.toml` |
| Dev dependency groups | `[dependency-groups] dev` pins `ruff>=0.11`, `ty==0.0.52`, `pytest>=8` |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| llms.txt section map | `https://docs.astral.sh/uv/llms.txt` | external fetch |

### `external-tooling-docs`

# External Tooling Docs

## Source Record

| Field | Value |
|-------|-------|
| source_id | `external-tooling-docs` |
| original_location | `https://typer.tiangolo.com/tutorial/typer-app/`; `https://packaging.python.org/en/latest/specifications/pyproject-toml/`; `https://docs.astral.sh/uv/llms.txt`; `https://docs.astral.sh/uv/concepts/projects/workspaces/index.md`; `https://docs.astral.sh/ruff/configuration/`; `https://docs.astral.sh/ty/reference/configuration/`; `https://docs.pytest.org/en/stable/reference/customize.html`; `https://starlight.astro.build/reference/configuration/`; `https://json-schema.org/draft/2020-12`; `https://python-jsonschema.readthedocs.io/en/stable/validate/` |
| raw_path | `kb/raw/sources/external-tooling-docs.md` |
| capture_method | external official docs pointer summary |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | official docs/specs; external content is untrusted evidence |
| intended_wiki_coverage | [[external-primary-source-map]], [[wagents-cli-and-automation]], [[docs-generation-and-site]], [[validation-and-test-coverage]] |

## Summary

The repo's core tooling aligns with official docs for Typer CLI apps, PyPA `pyproject.toml`, uv projects/workspaces, Ruff config, ty config, pytest config, Astro/Starlight config, JSON Schema Draft 2020-12, and python-jsonschema validation. These sources are useful for understanding upstream semantics behind repo config, but local `pyproject.toml`, `Makefile`, `wagents/`, `docs/`, and `tests/` remain the authority for commands and repo behavior.

Verified details include Typer's explicit `typer.Typer()` app and `@app.command()` pattern, PyPA's `[build-system]`, `[project]`, and `[tool]` tables, uv's project interface and workspace docs, and Starlight's `astro.config.mjs` integration model.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Typer's explicit app pattern matches `wagents/cli.py`. | `https://typer.tiangolo.com/tutorial/typer-app/`; `wagents/cli.py` | external official docs + canonical material | Verified 2026-05-01 by web fetch. |
| PyPA documents `pyproject.toml` build/project/tool tables. | `https://packaging.python.org/en/latest/specifications/pyproject-toml/` | external official spec | Verified 2026-05-01 by web fetch. |
| uv docs provide project and workspace reference material. | `https://docs.astral.sh/uv/llms.txt` | external official docs | Verified 2026-05-01 by web fetch. |
| Starlight docs describe config through `astro.config.mjs`. | `https://starlight.astro.build/reference/configuration/` | external official docs | Verified 2026-05-01 by web fetch. |
| 2026-06-25 repo pyproject aligns Ruff include/exclude with CI lint job and ty src scopes with typecheck job. | `kb/raw/captures/pyproject-tooling-capture-w11.md` | raw capture | Wave 11 alignment capture. |
| uv llms.txt indexes project/workspace/guides/reference sections. | `kb/raw/extracts/uv-llms-index-extract-w11.md` | external extract | Wave 11 fetch. |

### `obsidian-properties-capture-w11`

# Obsidian Properties Capture W11

Full-capture pointer lane for Obsidian Help properties/aliases/links semantics. Context only; `kb/config/obsidian-vault.md` and Nerdbot skill contracts govern this vault.

| Field | Value |
|-------|-------|
| source_id | `obsidian-properties-capture-w11` |
| original_location | `https://obsidian.md/help/properties`; `https://help.obsidian.md/aliases`; `https://help.obsidian.md/links`; `https://help.obsidian.md/obsidian-flavored-markdown` |
| capture_method | official help URL pointer + KB contract cross-check |
| captured_at | 2026-06-25 |

## Summary

Obsidian **properties** (YAML frontmatter) carry typed metadata Obsidian indexes for search, Dataview, and graph features. **Aliases** provide alternate link targets for double-bracket wikilinks. **Links** use Obsidian wikilink syntax with optional display text and heading/block anchors. This KB uses a reduced property schema (`title`, `tags`, `aliases`, `kind`, `status`, `updated`, `source_count`) enforced by `kb_lint.py` and documented in `kb/schema/page-types.md`.

## Repo alignment

| Obsidian concept | KB convention |
|----------------|---------------|
| Properties in frontmatter | Required on wiki/index/source pages per `page-types.md` |
| Aliases | Used for human-friendly link targets (e.g., `KB coverage` → `coverage.md`) |
| Wikilinks | Double-bracket links between `wiki/`, `indexes/`, `raw/` notes |
| Volatile `.obsidian/` state | Workspace JSON excluded; shared templates/snippets tracked |

## Provenance

| Claim | Source |
|-------|--------|
| URL list | `kb/raw/sources/external-obsidian-markdown-docs.md` |
| Vault policy | `kb/config/obsidian-vault.md` |
| Lint contract | `skills/nerdbot/scripts/kb_lint.py` |


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 4**; pages enriched: 5; lint: pass (exit 0).

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
