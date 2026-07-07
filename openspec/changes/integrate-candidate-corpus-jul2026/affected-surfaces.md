# Affected Surfaces

## Source Of Truth

- `planning/manifests/candidate-corpus-jul2026/raw-urls.txt`
- `scripts/generate_candidate_corpus_shards.py`
- `scripts/promote_candidate_corpus.py`
- `tests/test_candidate_corpus.py`
- `docs/src/authoring/skills/candidate-corpus-*.mdx`
- `openspec/changes/integrate-candidate-corpus-jul2026/*`

## Generated Or Derived Manifest Outputs

- `planning/manifests/candidate-corpus-jul2026/normalized-urls.json`
- `planning/manifests/candidate-corpus-jul2026/records/*.json`
- `planning/manifests/candidate-corpus-jul2026/*-matrix.json`
- `planning/manifests/candidate-corpus-jul2026/research-task-graph.json`
- `planning/manifests/candidate-corpus-jul2026/research-packet-schema.json`
- `planning/manifests/candidate-corpus-jul2026/raw-research-packets.json`
- `planning/manifests/candidate-corpus-jul2026/unique-target-research-packets.json`
- `planning/manifests/candidate-corpus-jul2026/subagent-wave-queue.json`
- `planning/manifests/candidate-corpus-jul2026/promotion-readiness-queue.json`
- `planning/manifests/candidate-corpus-jul2026/promotion-gate-matrix.json`
- `planning/manifests/candidate-corpus-jul2026/live-install-command-preview.json`
- `planning/manifests/candidate-corpus-jul2026/promotion-wave-plan.json`
- `planning/manifests/candidate-corpus-jul2026/promotion-wave-plan.md`
- `planning/manifests/candidate-corpus-jul2026/full-integration-progress.json`
- `planning/manifests/candidate-corpus-jul2026/full-integration-state.md`
- `planning/manifests/candidate-corpus-jul2026/existing-integration-coverage.json`
- `planning/manifests/candidate-corpus-jul2026/*report.md`
- `planning/manifests/candidate-corpus-jul2026/*decision*.md`
- `planning/manifests/candidate-corpus-jul2026/catalog-authoring-summary.json`
- `docs/public/generated-registries/skills-catalog-index.json`
- `docs/src/content/docs/skills/catalog/external/candidate-corpus-*.mdx`
- `docs/src/content/docs/skills/catalog/external/index.mdx`
- `docs/src/content/docs/skills/catalog/index.mdx`
- `README.md`

## Promotion Overlay Surfaces

- `docs/src/authoring/skills/*.mdx` includes promoted installable rows plus
  terminal non-syncing reference rows.
- `planning/manifests/candidate-corpus-jul2026/promotion-overrides.json`
  records reviewed install commands, selectors, attribution, and local install
  evidence.
- `planning/manifests/candidate-corpus-jul2026/applied-promotion-overrides.json`
  records the applied overlay rows.
- `planning/manifests/candidate-corpus-jul2026/catalog-authoring-summary.json`
  records 1038 installable rows and 175 terminal reference rows.
- `config/mcp-registry.json`, `mcp.json`, and
  `mcp/mcphub/mcp_settings.json` include disabled-by-default MCP/tool entries
  with placeholder-only auth.
- No third-party source trees were vendored into `skills/`.
- Default MCPHub groups remain credential-safe; credentialed services are not
  auto-enabled.
