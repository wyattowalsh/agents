# Proposal: Remediate RV Skill, Runtime, And Docs Contracts

## Problem

The current review found four implementation gaps that span portable skill
behavior, ordinary CLI/plugin process lifecycle, generated docs mutation, and
public harness taxonomy:

- RV-003: ordinary timeout paths can leave process-group descendants alive.
- RV-009: the portable skill-package manifest enricher does not parse real YAML
  folded scalars and hardcodes target harnesses.
- RV-010: docs graph validation can mutate generated state using implicit wall
  clock time, so check-mode proof is not pure or reproducible.
- RV-012: managed harnesses, Skills CLI-native targets, and MCP-only/hybrid
  surfaces are conflated, allowing homepage/README rows and counts to drift.

The fixes affect reusable behavior, tests, generated public surfaces, and final
validation order, so OpenSpec is required instead of isolated direct edits.

## Intent

- Make ordinary CLI/plugin timeout cleanup a POSIX lifecycle contract:
  process-group TERM, bounded wait, KILL when needed, then reap and drain.
- Make the portable manifest enricher parse real YAML folded scalars and derive
  harness targets from portable catalog/sync metadata with explicit source or
  unavailable state.
- Make docs graph validation pure and deterministic; mutation must receive an
  explicit UTC snapshot input.
- Freeze the authoritative taxonomy at exactly six managed harnesses and five
  Skills CLI-native targets while representing MCP-only/hybrid surfaces
  separately.
- Add proof-only regression gates for RV-007, RV-010, RV-011, and RV-013, then
  run RV-008 APM lock convergence as the final gate after generation.

## Scope

- Ordinary candidate CLI/plugin subprocess runners and their timeout tests.
- `skill-package-manifest-enricher` source, portable checks, fixtures, and docs.
- Docs graph/report validation, deterministic snapshot input, homepage data,
  README grouping, and focused tests.
- Harness taxonomy source and generated rows/counts.
- The exact proof-only commands and bounded assertions specified in the review.

## Out Of Scope

- Treating process cleanup as a sandbox or security-isolation primitive.
- Importing repository `wagents` from an installed portable skill package.
- Hardcoding a replacement target list in the manifest enricher.
- Live skill installation, production actions, branch/worktree changes, commits,
  or generated OpenSpec downstream artifacts.
- Regenerating candidate behavioral receipts before the process-lifecycle gate
  passes.

## Affected Users And Tools

Maintainers running candidate canaries, users of packaged portable skills,
docs/README readers, Skills CLI users, managed harness operators, MCP-only or
hybrid client users, and APM consumers rely on these contracts.

## Generated Surfaces To Refresh

- Skill package enrichment examples or generated manifest fixtures.
- Docs graph snapshots, link/insight reports, homepage data, support tables, and
  grouped catalog surfaces owned by the normal docs generator.
- Root README harness grouping and counts through the README generator.
- APM materialized projections and `apm.lock.yaml`, only after all other
  generation has completed.

## Risks

- Killing only the parent can leave descendants alive; killing too broadly can
  target unrelated processes unless a dedicated process group is established.
- YAML scalar shortcuts can corrupt descriptions or compatibility metadata.
- Implicit timestamps can make check-mode appear stale even with identical
  inputs.
- Mixing managed, Skills CLI-native, and MCP-only/hybrid taxonomies can produce
  internally consistent but semantically false public counts.
- Running APM lock proof before the final generator creates a false-green lock
  snapshot.
