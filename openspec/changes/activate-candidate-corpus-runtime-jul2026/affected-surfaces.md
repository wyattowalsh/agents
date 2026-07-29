# Affected surfaces

- Candidate corpus source, runtime, harness, auth, docs, and validation manifests
- Candidate corpus generation, promotion, assurance, and report scripts
- Candidate catalog/binding closure and required-capability derivation
- Candidate activation predicate, artifact, graph, scheduler, and transaction code
- External skill authoring and generated catalog surfaces
- MCP, plugin, harness, sync, bundle, and quarantine registries
- MCPHub generated settings and harness projections
- OpenSpec, ADR/decision log, auth matrix, runbooks, changelog, and reports
- Candidate corpus, harness, MCP, plugin, transaction, docs, and validation tests
- `scripts/run_candidate_plugin_canaries.py` and `tests/test_candidate_plugin_canaries.py`
- `scripts/verify_candidate_plugin_provenance.py`, `wagents/candidate_plugin_provenance.py`,
  and `tests/test_candidate_plugin_provenance.py`
- `scripts/rehearse_candidate_plugin_rollback.py` and `tests/test_rehearse_candidate_plugin_rollback.py`
- `scripts/rehearse_candidate_cli_rollback.py`, `scripts/rehearse_candidate_mcp_rollback.py`,
  and their focused transaction tests
- `planning/manifests/candidate-corpus-jul2026/runtime-activation-receipts.json`
- `planning/manifests/candidate-corpus-jul2026/runtime-activation-assurance.json`
- `planning/manifests/candidate-corpus-jul2026/plugin-provenance-lock.json`
- `planning/manifests/candidate-corpus-jul2026/plugin-provenance-audit-evidence.json`
- `wagents/candidate_receipts.py` and candidate receipt/migration tests
- Candidate receipt, plugin-provenance, transaction, rollback-journal,
  rollback-commit-marker, rollback-failure-marker, and assurance JSON schemas
- `scripts/migrate_candidate_runtime_receipts.py`
- `scripts/record_candidate_catalog_closure.py`
- `scripts/record_candidate_final_closure.py`
- `tests/test_record_candidate_catalog_closure.py`
- `tests/test_record_candidate_final_closure.py`
- `tests/test_candidate_runtime_activation.py`
- `tests/test_record_candidate_mcp_activation.py`
- Candidate ordinary CLI/plugin process-group lifecycle regressions owned by
  `remediate-rv-skill-docs-contracts`
- Trusted harness issuer adapter or explicit unavailable-state metadata for
  independent review provenance
- Immutable transaction-scoped candidate runtime evidence
