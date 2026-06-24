# Proposal

## Problem

Generated and hand-maintained docs pages duplicated SKILL bodies, boilerplate chrome, and sidebar noise. Median custom skill pages exceeded useful scan depth and repeated dispatch tables above collapsed source disclosures.

## Intent

Reduce page verbosity via summary density defaults, collapsed metadata/source disclosures, catalog lane filters, and docs lint guardrails—without removing full SKILL.md from collapsed details.

## Scope

- `wagents/page_density.py`, `wagents/page_chrome.py`, `wagents/rendering.py` summary mode
- CLI accordion reference; custom catalog sidebar lanes
- `CatalogSkillFilter.astro`; HAND-maintained page dedupe
- `wagents docs lint` + verbosity baseline manifest
- Delta to `openspec/specs/docs-instructions/spec.md`

## Out Of Scope

- Removing collapsed full SKILL.md disclosures
- Rewriting all HAND pages in one pass
- External curated research enrichment (separate change)

## Validation

- `uv run wagents docs generate --no-installed`
- `uv run wagents docs lint` (warn mode in CI)
- `uv run pytest tests/test_page_density.py tests/test_rendering.py tests/test_docs.py tests/test_docs_lint.py`
- `uv run wagents docs build`
