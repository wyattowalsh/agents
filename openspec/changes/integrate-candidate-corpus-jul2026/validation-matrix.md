# Validation Matrix

| Surface | Command | Expected Result |
| --- | --- | --- |
| Corpus coverage | `uv run python scripts/generate_candidate_corpus_shards.py --check-coverage` | 293 raw, 289 unique, 293 records, 289 decisions |
| Promotion packet coverage | `uv run python scripts/promote_candidate_corpus.py --check-coverage` | 293 raw packets, 289 unique packets, 289 gate rows, 0 commands |
| Focused tests | `uv run pytest tests/test_candidate_corpus.py -q` | pass |
| Lint | `uv run ruff check scripts/generate_candidate_corpus_shards.py scripts/promote_candidate_corpus.py tests/test_candidate_corpus.py` | pass |
| Research packet graph | `uv run pytest tests/test_candidate_corpus.py -q -k full_integration_research_task_graph_covers_every_lane` | 293 raw lanes, 289 unique lanes, 7,879 checks, 0 live-install eligible |
| Packet schema gate | `uv run pytest tests/test_candidate_corpus.py -q -k full_integration_progress_and_packet_schema_are_trust_gated` | required packet fields present; post-overlay progress is complete with remaining rows terminal-gated |
| Promotion packet gate | `uv run pytest tests/test_candidate_corpus.py -q -k promotion_research_packets_cover_every_raw_and_unique_target` | every U### and N### packet is covered and non-installable |
| Install preview gate | `uv run pytest tests/test_candidate_corpus.py -q -k promotion_gate_matrix_and_install_preview_keep_live_installs_blocked` | 0 repo-promotion ready, 0 live-install ready, 289 blocked, 0 commands |
| Read-only dispatch queue | `uv run pytest tests/test_candidate_corpus.py -q -k subagent_wave_queue_covers_every_raw_entry_read_only` | all 293 raw entries covered by read-only waves |
| Promotion readiness gate | `uv run pytest tests/test_candidate_corpus.py -q -k promotion_readiness_queue_blocks_live_install_until_trust_gates` | 0 repo-promotion ready, 0 live-install ready, 289 blocked |
| Promotion wave assignment | `uv run pytest tests/test_candidate_corpus.py -q -k promotion_wave_plan_assigns_every_unique_target_once` | every unique target assigned exactly once; W00 no-mutation |
| Asset validation | `uv run wagents validate` | pass |
| Docs generation | `uv run wagents docs generate --no-installed` | pass |
| README generation | `uv run wagents readme && uv run wagents readme --check` | pass |
| Install preview | `uv run wagents skills sync --dry-run` | pass with zero candidate install commands |
| Docs lint | `uv run wagents docs lint` | warnings only |
| Docs build | `uv run wagents docs build` | pass |
| Targeted OpenSpec | `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@latest validate integrate-candidate-corpus-jul2026 --strict --json` | pass |
| Full OpenSpec | `uv run wagents openspec validate` | pass for all active changes and specs |
| Deep source audit | `uv run python scripts/audit_candidate_deep_sources.py --check` | pass for 289 normalized targets; no candidate code executed |
| Final overlay check | `uv run python scripts/promote_candidate_corpus.py --final-check` | pass for 293 raw entries, 289 unique targets, 288 deep-audited targets, 1 terminal blocker, 1038 promoted overrides, and 1038 live installs |
| Promotion overlay | `uv run python scripts/apply_candidate_corpus_promotions.py --check` | pass for 1038 reviewed overrides, 1038 install commands, and completed progress state |

## Post-Overlay Notes

The promotion packet matrix and `live-install-command-preview.json` remain the
pre-overlay trust-gate handoff artifacts. The reviewed installation evidence is
recorded in `promotion-overrides.json`, `applied-promotion-overrides.json`,
`catalog-authoring-summary.json`, and `full-integration-state.md`.

## Finalization Notes

- Full `uv run wagents openspec validate` passes after adding narrow deltas for
  the sibling `add-open-websearch-mcp-skill` and
  `replace-package-version-check-mcp` changes.
- MCPHub registry generation remains required after any future MCP registry
  changes.
