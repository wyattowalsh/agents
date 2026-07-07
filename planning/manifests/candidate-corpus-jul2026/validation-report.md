# Candidate Corpus July 2026 Validation Report

- Raw candidates processed: 293
- Unique normalized targets: 289
- Added count: 1213
- Catalog authoring rows added: 1213
- Installable curated rows: 1038
- Live install additions: 1038
- Live install unique skill names: 1038
- Adapted count: 1038
- Reference-only count: 175
- Skipped/deduped selector collisions: 0
- Duplicates deduped: 4 raw duplicate URLs plus selector-name collisions in the promotion overlay
- Raw research lanes: 293
- Unique target synthesis lanes: 289
- Research leaf checks tracked: 7879
- Raw promotion research packets: 293
- Unique promotion research packets: 289
- Source-list evidence: 289 list-only source probes recorded; 1038 installable rows were promoted after additional live selector checks and local installs.
- GitHub metadata status: ok=292, unavailable=1
- Auth requirements: 49 source targets require auth or credential-boundary review; promoted auth-bearing skills use placeholder-only docs and remain user-invoked.
- Full integration phase: `promotion-overlay-installed`
- Live install status: `live-installs-recorded`

## Observed Generated Evidence

- Generator emitted manifest, matrix, packet, report, and catalog-authoring artifacts from local inputs.
- Promotion overlay converted reviewed, installed Skills CLI selectors into curated external authoring rows.
- No third-party source trees were vendored into `skills/`.
- Credentialed/account-backed tools remain explicit user-invoked skills or disabled docs examples; no secrets were committed.

## Command Checklist

- `uv run python scripts/apply_candidate_corpus_promotions.py --check` passed for 1038 promotion overrides.
- `uv run wagents validate` passed.
- `uv run wagents catalog index --check` passed.
- `uv run wagents docs generate --no-installed --check` passed.
- `uv run wagents readme --check` passed.
- `uv run pytest tests/test_candidate_corpus.py tests/test_site_model.py tests/test_skill_index.py tests/test_catalog_rows.py tests/test_rendering.py -q` passed.
- `uv run pytest tests/test_candidate_corpus.py tests/test_rendering.py tests/test_site_model.py tests/test_docs_reports.py -q` passed with 102 tests.
- `uv run ruff check scripts/apply_candidate_corpus_promotions.py wagents/site_model.py wagents/catalog_rows.py wagents/rendering.py tests/test_candidate_corpus.py tests/test_site_model.py tests/test_rendering.py` passed.
- `uv run ruff check scripts/apply_candidate_corpus_promotions.py scripts/promote_candidate_corpus.py tests/test_candidate_corpus.py tests/test_rendering.py tests/test_site_model.py tests/test_docs_reports.py wagents/catalog_rows.py wagents/rendering.py wagents/site_model.py` passed.
- `uv run wagents docs build` passed; Astro generated `docs/dist/` and reported all internal links valid.
- `scripts/mcphub/validate-settings.sh` passed.
- `uv run python scripts/generate_mcphub_settings.py --check` passed.
- `uv run wagents skills sync --dry-run --format json` passed in dry-run mode.
- `git diff --check` passed.
