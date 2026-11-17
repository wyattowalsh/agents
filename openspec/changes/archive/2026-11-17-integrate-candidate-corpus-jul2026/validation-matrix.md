# Validation Matrix

| Surface | Command | Expected Result |
| --- | --- | --- |
| Corpus coverage | `uv run python scripts/generate_candidate_corpus_shards.py --check-coverage` | 293 raw, 289 unique, 293 records, 289 decisions |
| Promotion packet coverage | `uv run python scripts/promote_candidate_corpus.py --check-coverage` | 293 raw packets, 289 unique packets, 289 gate rows, 0 commands |
| Focused tests | `uv run pytest tests/test_candidate_corpus.py -q` | pass |
| Lint | `uv run ruff check scripts/generate_candidate_corpus_shards.py scripts/promote_candidate_corpus.py tests/test_candidate_corpus.py` | pass |
| Research packet graph | `uv run pytest tests/test_candidate_corpus.py -q -k full_integration_research_task_graph_covers_every_lane` | 293 raw lanes, 289 unique lanes, 7,879 checks, 0 live-install eligible |
| Packet schema gate | `uv run pytest tests/test_candidate_corpus.py -q -k full_integration_progress_and_packet_schema_are_trust_gated` | required packet fields present; 289 targets integrated, zero unintegrated, and install eligibility remains separate |
| Promotion packet gate | `uv run pytest tests/test_candidate_corpus.py -q -k promotion_research_packets_cover_every_raw_and_unique_target` | every U### and N### packet is covered and non-installable |
| Install preview gate | `uv run pytest tests/test_candidate_corpus.py -q -k promotion_gate_matrix_and_install_preview_keep_live_installs_blocked` | 289 integrated, 121 trust-cleared installable, 168 non-installable, 4 active install blocks, 0 commands |
| Read-only dispatch queue | `uv run pytest tests/test_candidate_corpus.py -q -k subagent_wave_queue_covers_every_raw_entry_read_only` | all 293 raw entries covered by read-only waves |
| Promotion readiness gate | `uv run pytest tests/test_candidate_corpus.py -q -k promotion_readiness_queue_blocks_live_install_until_trust_gates` | 0 repo-promotion ready, 0 live-install ready, 289 blocked |
| Promotion wave assignment | `uv run pytest tests/test_candidate_corpus.py -q -k promotion_wave_plan_assigns_every_unique_target_once` | every unique target assigned exactly once; W00 no-mutation |
| Stable ownership partition | `uv run pytest tests/test_candidate_corpus.py -q -k integration_target_builder_covers_every_real_identity` | exact 121 existing installable, 6 existing inspection-required, 158 generated reference, and 4 generated hard-quarantine targets |
| Stable reference count | `uv run pytest tests/test_candidate_corpus.py -q -k every_unique_target_has_a_real_integration_identity` | exactly 162 generated stable references with `sync_kind: none` and no install command |
| Candidate-id retirement | `uv run pytest tests/test_candidate_corpus.py -q -k integration_target_catalog_rows_replace_staging_rows` | zero `candidate-corpus-*` authoring rows, catalog index rows, and generated detail pages |
| Installability separation | `uv run pytest tests/test_candidate_corpus.py -q -k promotion_validator_rejects_packet_installability_drift` | source-level integration coverage does not create install commands |
| Quarantine registry | `uv run pytest tests/test_candidate_corpus.py tests/test_validate_repo.py -q -k quarantine` | four stable records allow docs-only attribution and reject install/default enablement |
| Asset validation | `uv run wagents validate` | pass |
| Docs generation | `uv run wagents docs generate --no-installed` | pass |
| README generation | `uv run wagents readme && uv run wagents readme --check` | pass |
| Install preview | `uv run wagents skills sync --dry-run` | pass with zero candidate install commands |
| Docs lint | `uv run wagents docs lint` | warnings only |
| Docs build | `uv run wagents docs build` | pass |
| Targeted OpenSpec | `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@latest validate integrate-candidate-corpus-jul2026 --strict --json` | pass |
| Full OpenSpec | `uv run wagents openspec validate` | pass for all active changes and specs |
| Deep source audit | `uv run python scripts/audit_candidate_deep_sources.py --check` | pass for 289 normalized targets; no candidate code executed |
| Final overlay check | `uv run python scripts/promote_candidate_corpus.py --final-check` | pass for 293 raw entries, 289 unique targets, 289 deep-audited targets, and installable selector evidence tracked independently from stable source ownership |
| Promotion overlay | `uv run python scripts/apply_candidate_corpus_promotions.py --check` | pass with stable 121/6/158/4 coverage, 162 generated references, and zero candidate public rows |
| Non-skill assurance | `uv run python scripts/record_candidate_non_skill_assurance.py --check` | 289 unique targets, 63/63 runtime artifacts verified, zero failed artifacts, hard quarantines inactive |
| Candidate MCP generation | `uv run python scripts/generate_mcphub_settings.py --check` | generated MCPHub settings match the registry and every candidate MCP remains disabled |
| Plugin/MCP schema | `uv run pytest -q tests/test_distribution_metadata.py tests/test_generate_mcphub_settings.py` | plugin registry schema and disabled MCP projection pass |
| Runtime evidence tests | `uv run pytest -q tests/test_candidate_corpus.py -k 'non_skill or final_records_and_progress'` | coverage, pins, auth-name safety, quarantine, record pointers, and progress binding pass |

## Post-Overlay Notes

The promotion packet matrix and `live-install-command-preview.json` remain the
pre-overlay trust-gate handoff artifacts. The reviewed installation evidence is
recorded in `promotion-overrides.json`, `applied-promotion-overrides.json`,
`catalog-authoring-summary.json`, and `full-integration-state.md`.
Post-overlay runtime evidence also includes `harness-install-assurance.json` and
`non-skill-install-assurance.json`; configured or installed artifacts are not
treated as enabled unless those records say so.

## Finalization Notes

- Full `uv run wagents openspec validate` passes after adding narrow deltas for
  the sibling `add-open-websearch-mcp-skill` and
  `replace-package-version-check-mcp` changes.
- MCPHub registry generation remains required after any future MCP registry
  changes.
- `uv run pytest -q tests/test_mcphub_loopback_bind.py` validates loopback
  injection, child-preload cleanup, wildcard rejection, and the pinned launcher.
- `just mcphub-doctor` must report a loopback-only listener after a managed
  restart; wildcard or non-loopback listeners are a hard failure.
- Runtime assurance uses safe version/help probes only. Axiom MCP and GEO MCP
  are verified by installed package/config inventory because even `--help`
  starts their stdio servers; Refine is probed with the non-live `help`
  positional command.
- Stable-id reconciliation and generated public surfaces completed with zero
  public candidate-prefixed rows; the remaining four install blocks are the
  intentional quarantine boundary.
