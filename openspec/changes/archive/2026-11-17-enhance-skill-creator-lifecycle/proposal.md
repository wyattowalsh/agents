# Summary

Upgrade the repo-owned `skill-creator` skill from structural scaffold and audit
guidance into a lifecycle-oriented skill authoring system covering
source-grounded creation, behavioral eval planning, benchmark comparison,
description trigger optimization, security governance, runtime compatibility,
and verified parallel orchestration.

# Problem

The existing skill-creator workflow is strong at scaffolding, static validation,
audit scoring, package dry-runs, progress tracking, and structural pattern
coverage. It does not yet make behavioral proof a first-class release signal.
That leaves several gaps:

- New skills can be structurally correct while still lacking realistic source
  evidence, trigger/non-trigger tests, or measurable output-quality deltas.
- Existing skill improvements can claim quality gains from static audit scores
  without old-vs-new behavioral comparisons.
- Third-party exemplars and skill imports cross a supply-chain trust boundary
  but need explicit security-governance review before scripts, hooks, templates,
  references, or body substitutions are copied.
- Runtime-specific fields and install paths are easy to blur with portable
  Agent Skills fields.
- Large skill programs need bounded, auditable parallelism instead of broad
  fan-out without owned paths, artifacts, locks, or judge gates.

# Proposed Change

- Add skill-creator modes for security audit, eval planning, benchmark
  planning, old/new comparison, and description trigger optimization.
- Add reference contracts for evidence and benchmarking, security governance,
  runtime compatibility, and orchestration graphs.
- Extend the eval manifest with static cases that validate the new mode routing,
  safety posture, dirty-worktree preservation, OpenSpec routing, and `uv run
  python` command contract.
- Extend package and audit portability checks so executable frontmatter command
  strings cannot rely on repo-root `skills/<name>/...` paths, workspace tokens,
  or machine-local absolute paths.
- Require lifecycle packets for meaningful creation or improvement work:
  source evidence, trigger surface, eval plan, security posture, runtime matrix,
  and baseline.
- Treat security-governance blockers as release blockers even when static audit
  score is high.
- Keep live behavioral eval runners, installs, browser launches, and generated
  docs as opt-in/non-default actions outside Plan, Audit, and Security Audit
  modes.

# Non-Goals

- Do not add a live `wagents eval run` implementation in this change.
- Do not run live installs, `wagents skills sync --apply`, package publishing,
  browser launches, or credentialed behavioral evaluations.
- Do not hand-edit generated docs pages, generated registries, or install
  indexes.
- Do not widen `skill-creator` into agent, MCP, or arbitrary skill execution
  workflows; keep those as redirects.
