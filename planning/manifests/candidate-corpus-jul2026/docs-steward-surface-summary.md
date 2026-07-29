# Docs-Steward Surface Summary

Generated docs-steward packets cover:

- `README`: 293 candidates
- `catalog-authoring`: 293 candidates
- `catalog-generated`: 293 candidates
- `skill-research`: 293 candidates
- `mcp-tools`: 27 candidates
- `auth-matrix`: 293 candidates
- `install-docs`: 293 candidates
- `openspec`: 293 candidates
- `runbooks`: 50 candidates
- `decision-log`: 293 candidates
- `changelog`: 293 candidates
- `reports`: 293 candidates
- `generated-drift`: 293 candidates

Zero-count docs-steward surfaces omitted from covered lists:
- `agents-instructions`: 0 candidates

The authorized runtime overlay regenerates catalog, README, MCP registry, install, plugin ownership, auth, changelog, validation, and review surfaces from source. Future source changes require the same source-driven regeneration; generated pages are never hand-edited.

Successor runtime assurance is source-owned by:

- `scripts/record_candidate_catalog_closure.py`
- `scripts/run_candidate_cli_canaries.py`
- `scripts/rehearse_candidate_cli_rollback.py`
- `scripts/run_candidate_mcp_canaries.py`
- `scripts/rehearse_candidate_mcp_rollback.py`
- `scripts/run_candidate_plugin_canaries.py`
- `scripts/rehearse_candidate_plugin_rollback.py`
- `scripts/run_candidate_docs_assurance.py`
- `scripts/record_candidate_final_closure.py`
- `scripts/record_candidate_runtime_activation.py`

Full integration tracking lives in `existing-integration-coverage.json`, `promotion-wave-plan.json`, `research-task-graph.json`, `research-packet-schema.json`, `raw-research-packets.json`, `unique-target-research-packets.json`, `promotion-gate-matrix.json`, `live-install-command-preview.json`, `github-metadata-audit.json`, `promotion-readiness-queue.json`, `subagent-wave-queue.json`, `safe-wave-source-list-evidence.json`, `harness-install-assurance.json`, `non-skill-install-assurance.json`, `runtime-activation-receipts.json`, `runtime-activation-assurance.json`, `docs-closure-evidence.json`, `review-closure-evidence.json`, `auth-matrix.json`, `compliance-auth-matrix.json`, `full-integration-progress.json`, and `full-integration-state.md`. Runtime configuration and public documentation are tracked through `config/mcp-registry.json`, `config/plugin-extension-registry.json`, `docs/ai-tools/mcphub.md`, and the generated tools, install, MCP registry, and catalog pages.
