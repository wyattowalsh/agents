# Candidate Corpus July 2026 Validation Report

- Raw candidates processed: 293
- Unique normalized targets: 289
- Added count: 289
- Catalog authoring rows added: 289
- Live install additions: 0
- Adapted count: 0
- Reference-only count: 269
- Skipped count: 9
- Duplicates deduped: 4
- Raw research lanes: 293
- Unique target synthesis lanes: 289
- Research leaf checks tracked: 7879
- Raw promotion research packets: 293
- Unique promotion research packets: 289
- Live install command preview: 0 commands emitted
- Source-list evidence: 289 list-only probes recorded (236 found, 53 blocked/error/no-skills), 0 installs
- GitHub metadata status: ok=292, unavailable=1
- GitHub license labels detected: 9
- Existing integration coverage: covered-by-existing-installable-catalog=14, covered-by-existing-reference=1, needs-promotion-review=274
- Covered by existing installable catalog rows: 14
- Promotion waves: W00=14, W01=15, W02=28, W03=27, W04=22, W05=26, W06=21, W07=30, W08=101, W99=5
- Full integration phase: `research-graph-ready`
- Live install status: `no-new-live-installs-eligible`

## Observed Generated Evidence

- Generator emitted manifest, matrix, packet, report, and catalog-authoring artifacts from local inputs.
- Candidate code was not installed, executed, vendored, adapted, or enabled.
- Live install command preview emitted 0 commands.
- Trust gates remain open for blocked targets; existing installable catalog rows are credited without new live install commands.

## Command Checklist

- `uv run python scripts/generate_candidate_corpus_shards.py --check-coverage`
- `uv run python scripts/promote_candidate_corpus.py --write --check-coverage`
- `uv run pytest tests/test_candidate_corpus.py -q`
- `uv run ruff check scripts/generate_candidate_corpus_shards.py scripts/promote_candidate_corpus.py tests/test_candidate_corpus.py`
- `uv run wagents validate`
- `uv run wagents docs generate --no-installed`
- `uv run wagents readme`
- `uv run wagents readme --check`
- `uv run wagents skills sync --dry-run`
- `uv run wagents docs lint`
- `uv run wagents docs build`
- `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@latest validate integrate-candidate-corpus-jul2026 --strict --json`
- `uv run wagents openspec validate`
