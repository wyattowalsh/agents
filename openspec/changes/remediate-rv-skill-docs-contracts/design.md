# Design: RV Skill, Runtime, And Docs Contract Remediation

## Approach

Implement four bounded lanes, then run proof-only regressions and a serialized
generation closeout.

### RV-003: ordinary process lifecycle

Use one existing or minimally shared POSIX subprocess-lifecycle helper for the
ordinary candidate CLI and plugin timeout paths:

1. Start the child in a dedicated process group/session.
2. On timeout, send TERM to that process group.
3. Wait for a fixed bounded grace interval.
4. If any group member remains, send KILL to the same process group.
5. Wait/reap the direct child and drain stdout/stderr after TERM or KILL.
6. Return timeout evidence only after cleanup completes.

The helper owns lifecycle cleanup, not sandboxing. It must never signal the
parent agent's process group or claim network/filesystem isolation. Focused
tests spawn a descendant, force timeout, and prove both direct and descendant
processes are gone and output pipes are drained before a later receipt can run.

### RV-009: portable manifest enrichment

Replace line-oriented frontmatter parsing with a real YAML safe loader so folded
scalars, chomping, quoted values, lists, and mappings have YAML semantics.
Enrichment remains additive and preserves upstream keys.

Resolve harness targets from explicit portable inputs:

1. Prefer portable catalog metadata for the selected skill when supplied.
2. Otherwise use portable sync metadata when supplied and applicable.
3. Record which input and digest produced the target set.
4. If neither source is available, emit an explicit unavailable state and an
   empty derived target set; do not substitute a hardcoded list.

The installed skill package must not import this repository's `wagents`
package. Any YAML runtime dependency is declared by the skill's compatibility
contract, and portable checks exercise the script outside repo-module imports.
Writes still require explicit `--apply`; preview and `--dry-run` do not mutate.

### RV-010: pure docs graph validation

Separate report computation/validation from report mutation:

- Pure graph and validation functions accept source data and an explicit
  snapshot value and return deterministic data without filesystem writes or
  clock reads.
- Check/validation mode performs no writes and does not synthesize a current
  timestamp.
- Mutation internals accept an explicit UTC snapshot date in canonical
  `YYYY-MM-DD` form. The CLI exposes optional
  `--snapshot-date YYYY-MM-DD`; when omitted in mutation mode, the
  CLI/generator boundary captures the current UTC date exactly once and passes
  it explicitly through every related report.
- Equal inputs plus the same explicit snapshot produce byte-identical output.
- An invalid supplied date fails before writing. Internal mutation calls
  without a boundary-resolved date fail, while the established CLI invocation
  without the option remains supported by the one-time boundary capture.

### RV-012: authoritative harness taxonomy

Use the current repository taxonomy as structured source data:

- Managed six: `claude-code`, `codex`, `crush`, `cursor`, `grok`, `opencode`.
- Skills CLI-native five: managed six minus `grok`.
- MCP-only/hybrid surfaces: represented separately with explicit surface kind
  and excluded from both managed and Skills CLI-native counts.

Homepage rows, badges/counts, install commands, support tables, and README
grouping derive from those categories. Tests assert row identity as well as
counts so duplicated or mislabeled rows cannot pass merely by preserving a
total.

## Data And Control Flow

1. RV-003 focused tests pass.
2. Only then may candidate behavioral receipts be regenerated.
3. RV-009 reads `SKILL.md` with a real YAML loader, resolves explicit portable
   metadata, emits preview or writes only under `--apply`.
4. RV-010 resolves one UTC snapshot date at the mutation boundary and computes
   graph/report payloads from source inputs plus that explicit date; check mode
   compares without mutation or a clock read.
5. RV-012 projects the structured taxonomy into site data and README grouping.
6. Run focused implementation tests and RV-007/RV-010/RV-011/RV-013 proof-only
   regressions.
7. Run source-driven docs/README/sync/APM generation in the owning serialized
   lane.
8. Run `uv run wagents apm refresh-lock --check` as the final RV-008 gate.

## Integration Points

- Existing candidate canary runners and ReceiptStore v2 freshness gates.
- The portable `skill-package-manifest-enricher` CLI and its local checks.
- Existing catalog/sync metadata formats; no new repo-package import from the
  installed skill.
- Existing docs graph/report functions, docs generator, site model, and README
  command.
- The concurrent harness-retirement change for RV-007, RV-013, taxonomy, and
  final APM ordering.

## Alternatives Rejected

- Killing only the direct child: descendants survive and contaminate evidence.
- Calling process cleanup a sandbox: lifecycle termination does not isolate
  filesystem, credentials, or network.
- Hand-parsing YAML or stripping `>` characters: folded scalars and chomping
  semantics are lost.
- Hardcoding the six harness targets inside the portable enricher: it hides
  metadata absence and drifts from the catalog/sync source.
- Importing `wagents` from the installed skill: the package is not guaranteed
  to contain the repo application.
- Reading the wall clock inside validation: identical inputs become
  nondeterministic and check mode can mutate.
- Counting every client as a managed harness: MCP-only/hybrid support is a
  different surface.
- Running APM lock proof before docs/sync generation: later writes invalidate
  the proof.

## Migration Or Compatibility Notes

No compatibility alias or dual parser is added. Existing enriched manifests may
gain explicit metadata source/status fields when regenerated. Generated docs
may change rows or counts to match the authoritative taxonomy. Existing
candidate behavioral receipts are not silently upgraded; regeneration remains
blocked until RV-003 lifecycle tests pass, then normal ReceiptStore v2
freshness rules apply.
