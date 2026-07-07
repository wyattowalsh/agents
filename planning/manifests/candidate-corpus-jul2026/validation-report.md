# Candidate Corpus July 2026 Validation Report

- Raw candidates processed: 293
- Unique normalized targets: 289
- Catalog authoring rows: 1213
- Installable promoted curated-external rows: 1038
- Recorded install evidence rows: 1038
- Installed path references verified: 3115/3115
- Missing installed `SKILL.md` files: 0
- New live install commands emitted: 0
- Remaining reference or terminal-gated rows: 175
- Source-list evidence: 289 list-only source probes recorded; 1038 installable rows were promoted from reviewed override evidence.
- Deep source audit: 288 targets audited through GitHub API README/license/tree/package reads plus 1 terminal blocker; candidate code executed: false.
- Full integration phase: `promotion-overlay-installed`
- Live install status: `no-live-install-commands-emitted`
- Status note: validation emitted no new installer commands; the promotion overlay verifies 1038 previously recorded install evidence rows and 3115 installed `SKILL.md` path references.
- Gate summary: 120 covered, 0 ready for repo promotion, 0 ready for live install, 169 blocked.

## Observed Generated Evidence

- Generator emitted manifest, matrix, packet, report, and catalog-authoring artifacts from local inputs.
- Read-only generator and deep-source audit scripts did not execute candidate code.
- The promotion overlay records prior non-dry-run Skills CLI install commands; validation verifies installed `SKILL.md` roots without re-running installers.

## Command Checklist

- `uv run python scripts/generate_candidate_corpus_shards.py --emit-all --no-network`
- `uv run python scripts/apply_candidate_corpus_promotions.py --check` passed for 1038 promotion overrides.
- `uv run python scripts/audit_candidate_deep_sources.py --check` passed for 289 normalized targets.
- `uv run python scripts/promote_candidate_corpus.py --final-check` passed for 293 raw entries, 289 unique targets, 288 deep-audited targets, 1 deep terminal blocker, 1038 promoted overrides, and 1038 recorded install evidence rows.
- `uv run -- wagents docs generate --no-installed --check`
- `uv run -- wagents catalog index --check --format json`
- `uv run wagents validate`
- `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@latest validate integrate-candidate-corpus-jul2026 --strict --json`
- `uv run ruff check scripts/audit_candidate_deep_sources.py scripts/promote_candidate_corpus.py scripts/apply_candidate_corpus_promotions.py scripts/generate_candidate_corpus_shards.py scripts/audit_candidate_source_lists.py tests/test_candidate_corpus.py tests/test_docs.py tests/test_docs_catalog.py tests/test_skill_index.py tests/test_skills_catalog_schemas.py wagents/docs.py wagents/docs_catalog.py wagents/skill_index.py`
- `PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_candidate_corpus.py tests/test_docs.py tests/test_docs_catalog.py tests/test_skill_index.py tests/test_skills_catalog_schemas.py tests/test_harness_config_docs.py` passed with 126 tests.
- Full pytest inventory collection found 1985 tests across 129 files. The monolithic command was signal-terminated with rc 143, so final coverage used sequential file-by-file pytest: files 1-16 passed, file 17 was skip-only, and files 17-129 passed or were explicitly skip-only.
- `uv run wagents docs lint` completed with 0 errors and 19 soft warnings.
- `uv run wagents docs build` completed, generated 2096 HTML files, and validated all internal links.
- `scripts/mcphub/validate-settings.sh && uv run python scripts/generate_mcphub_settings.py --check`
- `uv run wagents skills sync --dry-run --format json` completed with `inventory_count: 1535`.
