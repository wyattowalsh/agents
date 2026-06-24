# Design

## Approach

Keep ecosystem research advisory, evidence-gated, and read-only. `harness-master` gains four new dispatch modes:

- `research <harness|all> <config|plugin|extension|mcp|skill|all> [goal]`
- `candidate <source-or-url> <harness|all> [level]`
- `compare <candidate...> for <harness|all>`
- `sources [category]`

The skill loads source registry metadata only for the active research step and uses helper scripts to plan access before live calls. Live execution is optional and limited to low-risk read-only APIs. Credentialed APIs report missing environment variables as degraded evidence rather than hard failures.

## Data And Control Flow

1. Normalize harness, category, depth, and goal.
2. Run local surface discovery and load local repo registries as fit and ownership context.
3. Build a source plan from `data/research-sources.json` with `source_probe.py --dry-run`.
4. Dispatch parallel scouts by source family when runtime supports teams or subagents.
5. Normalize candidates into evidence dossiers.
6. Score candidates with `candidate_score.py`.
7. Report ranked recommendations, blocked evidence, validation requirements, and rollback paths.
8. Stop before any apply or install step unless a later matching dry-run audit is approved.

## Integration Points

- `references/workflow.md` remains the default audit/apply workflow and links to ecosystem research as a separate mode.
- `references/output-format.md` gains an `Ecosystem Research Report` template.
- `references/ecosystem-research.md` carries orchestration wave semantics.
- `references/source-profiles.md` explains source families, source confidence, and degraded behavior.
- `data/research-sources.json` is the machine-readable registry for source planning.
- Evals cover classification, source confidence, GraphQL enrichment, skill-auditor routing, and apply blocking.

## Alternatives Rejected

- Do not make live network calls mandatory. Baseline mode must work as a dry-run source plan and local registry review.
- Do not promote community/social evidence to adoption proof. It can only raise investigation priority.
- Do not hard-code a local orchestrator skill path. The guidance describes Pattern F and Pattern E semantics without assuming a specific runtime path.
- Do not couple research reports to generated docs. Docs generation remains a separate validation-driven step.

## Migration Or Compatibility Notes

This is an additive skill behavior. Existing audit and apply modes remain dry-run first and approval gated. New scripts use only the Python standard library so packaging remains portable.
