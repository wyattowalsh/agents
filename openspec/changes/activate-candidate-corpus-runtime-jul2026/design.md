# Design: Candidate Corpus Runtime Activation

## Decisions

1. The historical intake change remains immutable evidence; this successor owns
   runtime activation and usability assurance.
2. One root orchestrator is the sole repo/home writer. Read-only workers author
   and review packets but never mutate shared state.
3. Artifact identity, not source URL, is the execution unit. Shared packages
   install once while every entrypoint receives its own behavior receipt.
4. Runtime proof requires identity, install, semantic use, failure/denial use,
   fresh process, rollback absence, reinstall, and promoted final state.
5. Skills require exact selector and applicable-harness receipts. Aggregate
   inventory counts and Skills CLI dry runs are planning evidence only.
6. MCPHub is the MCP control plane. Candidate servers begin disabled, pass an
   isolated protocol canary, then receive intentional enabled projection.
7. Quarantine uses immutable, no-secret, network-bounded disposable fixtures.
   Isolation alone does not cure licensing or satisfy usability.
8. Credentials remain operator-owned. Receipts store names, scopes, redacted
   fingerprints, positive/negative probe status, and logout/revocation only.
9. Completion is recomputed from accepted leaf receipts. A `complete` field in a
   generated input is never itself evidence.
10. Existing dirty bytes are the transaction baseline. Any preimage mismatch or
    undeclared write halts the writer and rolls back owned paths.
11. Runtime enumeration is open until package manifests and executable entrypoints
    reconcile. The historical 63-artifact report, the first 64-artifact successor
    draft, and aggregate source classifications are not closure evidence.
