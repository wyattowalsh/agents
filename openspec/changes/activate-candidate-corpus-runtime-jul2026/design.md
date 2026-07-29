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
12. Every receipt writer uses one key-owned optimistic transaction API and one
    shared commit lock. Disjoint keys merge; same-key drift fails closed.
13. Successful rollback journals and transcripts are immutable and
    transaction-scoped. Failed attempts never overwrite accepted evidence.
14. Receipt document v1 is diagnostic/migration input only. Normal writers
    require schema-valid v2 and never synthesize missing legacy proof.
15. Catalog accounting and runtime usability are separate states. Final
    completion requires fresh accepted receipts, all closure gates, no blockers,
    and a receipt-store digest matching the assurance snapshot.
16. `already_present` is discovery evidence only. It can establish that a
    selector is visible to a harness, but it never supplies behavioral,
    fresh-process, rollback, or promoted-final proof.
17. Every selector-to-harness binding owns a distinct content-addressed
    five-phase proof chain: discovery; behavior with positive and negative
    assertions; fresh-process use; rollback with absence, restoration,
    unchanged-state, and final-state proof; and promoted-final acceptance. Each
    leaf binds the exact selector, harness, current input digest, and installed
    content digest.
18. Required capabilities are derived from the portable catalog and sync
    metadata current at receipt time. Proved capabilities are derived only from
    accepted behavioral leaves; the untested set is computed as
    `required_capabilities - proved_capabilities` and is never a hardcoded
    empty collection.
19. ReceiptStore v2, owned-key compare-and-swap, immutable evidence, and
    freshness checks remain mandatory. Candidate behavioral receipts are not
    regenerated until the ordinary CLI/plugin process-group cleanup regressions
    pass, so a timed-out descendant cannot contaminate later evidence.
20. Independent review uses externally issued session and task provenance when
    a trusted harness issuer is available. The source validator rejects
    self-authored issuer identities. Without a trusted issuer, repo-source
    validation may pass while live review closure remains
    `BLOCKED-EXTERNAL`.
21. Distinct actor and run strings are structural checks, not independence
    proof. This change does not claim DSSE, SLSA, or in-toto compliance and does
    not introduce an ad hoc PKI.
22. RV-002 is source-closed. Its registry `enabled: true` state,
    registry/generated/live presence and identity equality, and authenticated
    reachability plus unauthenticated-denial regressions stay as preservation
    gates; this change adds no RV-002 implementation.
23. Enabled Codex plugins are reconstructed from pinned Git objects rather than
    mutable worktree bytes. Projection accepts regular blobs only, preserves
    executable modes, rejects symlinks and submodules, and creates no empty
    directories. The resulting digest must match marketplace source, isolated
    install, and live cache content.
24. Rollback success is a two-record transaction. The immutable final journal
    remains `commit-pending`; only an immutable passed marker written after the
    receipt-store CAS can make it acceptable. The marker binds the exact sorted
    artifact set, journal digest, receipt revision, receipt-store transaction,
    and receipt-document digest. CAS or rehearsal failures use separate failure
    evidence and never satisfy acceptance.
25. Runtime readers open transcripts, journals, and markers relative to the
    managed evidence root with no-follow descriptor traversal, read each file
    once, and reject symlink traversal or in-read mutation.
