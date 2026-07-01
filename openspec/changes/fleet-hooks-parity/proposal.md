# Proposal

## Why

Hook generation logic is duplicated and drifting across `wagents/apm.py`,
`scripts/sync_agent_stack.py`, and `wagents/platforms/*.py`. There is no schema
for `config/hook-registry.json`, so registry edits are unguarded, and there is
no curated registry for externally-owned hooks (such as Plannotator plan
review). Before the fleet can scale hook coverage across harnesses, the shared
rendering and merge primitives must be consolidated into a single source and the
registry surfaces must be schema-validated.

This change implements the **G0 Foundation** gate of the Fleet Hooks program and
is now **complete**. **G1–G6** fleet implementation is likewise landed in the
working tree (see [`tasks.md`](tasks.md) for honest deferrals). Guard expansion
and review-finding closure (RV-001–RV-010, C-010/C-020) are tracked in
[`fleet-hooks-guard-expansion/`](../fleet-hooks-guard-expansion/).

## What Changes

- Add `config/schemas/hook-registry.schema.json` describing the current
  `config/hook-registry.json` shape and reserving the forward-looking
  `logical_policy`, `projection`, and `harness_overrides` fields for the later
  registry refactor.
- Add a `$schema` pointer to `config/hook-registry.json` with no semantic change
  to its hook entries.
- Extract the shared hook renderer into `wagents/hooks/render.py` and import it
  from both `wagents/apm.py` and `scripts/sync_agent_stack.py` so there is one
  rendering source.
- Consolidate `strip_generated_hook_entries` and `merge_hook_groups` into
  `wagents/hooks/merge.py` as the single implementation, imported by
  `wagents/platforms/base.py` and `scripts/sync_agent_stack.py`.
- Add `config/schemas/external-hooks-registry.schema.json` and
  `config/external-hooks-registry.json` with a curated Plannotator row.
- Wire the two new config/schema pairs into the existing schema-conformance test.

## Impact

- Hook rendering and merge behavior get a single, testable source of truth,
  eliminating the apm/sync duplication called out in the program critique.
- Registry edits in later waves are guarded by a JSON schema.
- Externally-owned hooks gain an auditable registry surface separate from
  repo-owned `config/hook-registry.json`.
- No change to generated hook output for any harness in this gate.

## Scope

- New hook-registry schema, registry `$schema` pointer, shared renderer module,
  consolidated merge module, external-hooks registry + schema, and focused test
  wiring.
- OpenSpec artifacts for the foundation gate (this change).

## Out Of Scope

- Cursor flat-hook rendering and global Plannotator unification (G1).
- Registry Tier A hook rows and matcher pack (G2).
- Per-harness adapter expansion (G3a/G3b).
- Policy module split under `wagents/hooks/policies/` (G4).
- `wagents hooks validate --harness` and docs hub (G5/G6).
- Any live `sync --apply --targets home` against the user home directory.

## Risks

- APM hook output could drift during extraction. Mitigate by preserving each
  harness's existing event map and shape inside the shared renderer and by
  keeping `tests/test_apm_materialize.py` and `tests/test_sync_agent_stack.py`
  green.
- Schema could be too strict and reject the current registry. Mitigate by
  modeling the schema on the observed registry shape and adding a conformance
  test rather than rewriting hook entries.
