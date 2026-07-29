# Candidate Corpus July 2026 Validation Report

- Raw candidates processed: 293
- Unique normalized targets: 289
- Catalog authoring rows: 1424
- Installable promoted curated-external rows: 1266
- Recorded install evidence rows: 1266
- Installed path references verified: 4028/4028
- Missing installed `SKILL.md` files: 0
- Post-install harness commands remaining: 0
- Post-install desired rows missing across harnesses: 0
- Successor runtime artifacts discovered: 65
- Successor runtime artifacts accepted: 20
- Successor runtime artifacts incomplete: 45
- Requested full usability: `false`
- Non-skill normalized targets accounted for: 289/289
- Terminal non-install traceability rows: 158
- Integrated normalized targets: 289/289
- Unintegrated normalized targets: 0
- Integrated quarantine references: 4
- Active install blocks: 4
- Source-list evidence: 289 list-only source probes recorded; 1266 installable rows were promoted from reviewed override evidence.
- Deep source audit: 289 targets audited through GitHub API README/license/tree/package reads plus 0 terminal blocker; candidate code executed: false.
- Full integration phase: `corpus-integration-complete`
- New install command preview status: `no-live-install-commands-emitted`
- Status note: the recorded post-install dry-run covers 6 harnesses with 0 missing desired rows and 0 remaining commands.
- Gate summary: 121 covered, 0 ready for repo promotion, 0 ready for live install, 168 terminal native or hard-blocked.

## Observed Generated Evidence

- Generator emitted manifest, matrix, packet, report, and catalog-authoring artifacts from local inputs.
- Read-only generator and deep-source audit scripts did not execute candidate code.
- The promotion overlay records non-dry-run Skills CLI evidence; `harness-install-assurance.json` records the sanitized post-install reconciliation result, `non-skill-install-assurance.json` records historical package/config dispositions, and `runtime-activation-assurance.json` owns executable usability truth.
- Quarantined targets are permanent non-installable references with source-specific risk and license reasons; their active install blocks exclude them from sync.
- A maintainer-authorized install reconciliation was run; the committed assurance artifact is the subsequent dry-run result, not raw installer output.

## Runner-Owned Validation Checklist

> This overlay records required commands only. It does not execute them or claim outcomes; the runner owns any observed closeout results.

- Successor assurance source: `scripts/record_candidate_catalog_closure.py`.
- Successor assurance source: `scripts/run_candidate_cli_canaries.py`.
- Successor assurance source: `scripts/rehearse_candidate_cli_rollback.py`.
- Successor assurance source: `scripts/run_candidate_mcp_canaries.py`.
- Successor assurance source: `scripts/rehearse_candidate_mcp_rollback.py`.
- Successor assurance source: `scripts/run_candidate_plugin_canaries.py`.
- Successor assurance source: `scripts/rehearse_candidate_plugin_rollback.py`.
- Successor assurance source: `scripts/run_candidate_docs_assurance.py`.
- Successor assurance source: `scripts/record_candidate_final_closure.py`.
- Successor assurance source: `scripts/record_candidate_mcp_activation.py`.
- Successor assurance source: `scripts/record_candidate_runtime_activation.py`.
- `uv run python scripts/generate_candidate_corpus_shards.py --emit-all --no-network`
- Required closeout: `uv run python scripts/apply_candidate_corpus_promotions.py --check` for 1266 promotion overrides.
- Required closeout: `uv run python scripts/audit_candidate_deep_sources.py --check` for 289 normalized targets.
- Required closeout: `uv run python scripts/promote_candidate_corpus.py --final-check` for 293 raw entries, 289 unique targets, 289 deep-audited targets, 0 deep terminal blocker, 1266 promoted overrides, and 1266 recorded install evidence rows.
- Required closeout: focused candidate-corpus and docs generation tests.
- Required closeout: `uv run pytest -q tests/test_candidate_corpus.py tests/test_docs.py`.
- Required closeout: `uv run wagents docs generate --no-installed --check`.
- Required closeout: `uv run wagents catalog index --check --format json`.
- Required closeout: `uv run wagents validate`.
- Required closeout: `uv run wagents readme --check`.
- `harness-install-assurance.json` records 0 remaining commands after the authorized reconciliation run.
- Required closeout: `uv run wagents openspec validate`.
- Required closeout: strict OpenSpec validation for `integrate-candidate-corpus-jul2026`.
- Required closeout: `git diff --check`.

## Observed Closeout Results

- Full suite: `uv run pytest -q` -> 2183 passed, 1 skipped in 287.70s.
- Static gates: focused Ruff lint/format, shell syntax/ShellCheck, and `git diff --check` passed.
- Repo gates: `uv run wagents validate`, README freshness, catalog freshness, and docs-generation freshness passed.
- OpenSpec: the candidate change passed strict validation (1/1); global validation passed 63/64 and reports only the unrelated `add-reddit-mcp-buddy` no-delta failure.
- Docs build: 1852 generated pages, 2287 HTML files indexed, and all internal links valid.
- Harness reconciliation: 9/9 harnesses have 1600 desired rows present, with 0 missing, 0 pin-blocked, and 0 commands.
- MCPHub: doctor reports a loopback-only `127.0.0.1:46683` listener; authenticated `all`, `ddgs`, and `harness` smoke routes passed.
- Secret sweep: the final candidate/MCP/config scan found placeholder assignments only; no real credentials were persisted.
- Detailed machine-readable evidence: `validation-results.json`.
