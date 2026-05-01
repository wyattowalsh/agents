---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Risk Register

| Risk | Severity | Probability | Mitigation | Owner |
|---|---:|---:|---|---|
| External skills execute untrusted scripts | High | Medium | provenance, audit skill scripts, sandbox execution, trusted tiers | Security Team |
| MCP config creates broad live-system access | High | High | MCP reserved for live-state use cases, allowlists, per-agent permissions | MCP Team |
| User-level config drift across harnesses | Medium | High | transaction snapshots, dry-run diffs, rollback | UX/CLI Team |
| Docs and generated registries diverge | Medium | High | docs truth CI, generated pages, stale checks | Docs Team |
| Harness APIs change without warning | Medium | Medium | support tiers, version matrix, nightly docs check | Harness Teams |
| OpenSpec assets duplicate planning docs | Medium | Medium | explicit separation: OpenSpec for change/spec governance, planning for program docs | OpenSpec Team |
| Over-parallelized PRs conflict | Medium | Medium | file ownership manifest and PR clusters | Orchestrator |
| Marketplace indexes include low-quality MCPs | High | High | discovery-only policy; promotion gates require upstream docs | MCP Curation |
| Secrets leak through generated configs | Critical | Low | env var references only, no secret material in manifests, secret scans | Security Team |
| Agent instructions get too large | Medium | Medium | progressive disclosure, skill router, generated summaries | AI Instructions Team |
