# Validation matrix: activate-candidate-corpus-runtime-jul2026

| Gate | Evidence | Expected |
| --- | --- | --- |
| Corpus | 293 raw, 289 normalized, four duplicate groups | exact |
| Artifact discovery | exact entrypoint-backed artifact graph | no unclassified executable surfaces |
| Selectors | source list plus exact path/hash receipts | at least 1,306, subject to discovery |
| Packages | install, use, failure, denial, rollback, reinstall | every artifact accepted |
| Skills | per-selector and per-applicable-harness receipts | no aggregate-only proof |
| MCP | initialize, tools/list, harmless call, restart, fresh discovery | enabled only after canary |
| Plugins | load, named behavior, disable/absence, re-enable | fresh-session pass |
| Auth | minimum scope, positive/negative use, revoke/logout | no stored secret values |
| Quarantine | lawful isolated use, global rejection, cleanup | no global discovery |
| Transactions | declared writes and exact preimage rollback | no unrelated byte changes |
| Docs | source/generator/output/validator edges | synchronized and idempotent |
| Closure | accepted fresh leaf receipts | zero blockers, findings, or untested capabilities |
