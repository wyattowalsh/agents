# Proposal: Fleet Skill Projection Assurance

## Why

Skills CLI treats `~/.agents/skills` as the canonical store and marks Cursor as a
universal agent. Fleet sync currently treats store-only (or secondary-root)
presence as “already present,” so Cursor can report fully reconciled while
`~/.cursor/skills` remains sparse. Project `.cursor/skills/repo` never satisfies
global Cursor coverage. Naive “ensure symlink” without a conflict matrix risks
clobbering divergent real directories. Dry-run cleanup hashing has OOMed (exit 137)
on this fleet, blocking gates before any apply.

Sibling change `reconcile-harness-plugins-skills` accounts for plugin/extension
dispositions and default desired missing counts, but does not split
`store_present` vs `projection_present`, does not define Cursor projection
ensure, and can false-pass when authoritative projection is empty.

## What Changes

- Freeze a presence model: `store_present`, `projection_present`,
  `preferred_non_cli`, sync buckets, and Cursor global projection root rules.
- Freeze `ensure_cursor_authoritative_links` API signature and additive-only
  conflict rules (never `rm -r` real trees; never overwrite divergent bodies).
- Extend reconciliation evidence with `store_missing_by_agent` and
  `projection_missing_by_agent` (sibling extend, not July-packet green claim).
- Plan inventory tiers + lazy cleanup hashing and sync planner buckets for later
  waves; this change’s evidence path stays dry-run only.

## Intent

OpenSpec-freeze contracts so Wave 1a/1b implementers share one SSOT before any
production Python edits. Gate G0: validate green; no live apply.

## Scope

- OpenSpec change artifacts under
  `openspec/changes/fleet-skill-projection-assurance/` only (this wave).
- Contract freeze for presence, ensure API, recon keys, and hard stop rules.
- Documentation-of-record inside this change (design / specs / matrices).

## Out Of Scope (this change / Wave 0)

- Editing production Python under `wagents/` or `scripts/` (Wave 1+).
- Running `wagents skills sync --apply`, live `npx skills add`, mass home
  symlink writes, or cleanup `--apply`.
- Promoting inspect-then / avoid catalog rows into the desired set.
- Touching `~/.cursor/skills-cursor/` product builtins.
- Forcing `~/.codex/skills` fills when Codex plugin / OpenCode `skills.paths`
  already owns repo skills.
- Bulk `--copy` installs.

## Affected Users And Tools

- Maintainers running `wagents skills sync --dry-run` / reconciliation.
- Cursor (global `~/.cursor/skills` projection assurance primary).
- Dual-root harness reporting (Codex/OpenCode/Crush tiers; projection require
  default OFF for universal peers unless ownership docs say otherwise).

## Generated Surfaces To Refresh (later waves)

- Hand docs: plugin-skill-ownership, harness-surfaces, CLI help notes.
- Recon packet `planning/manifests/harness-reconciliation.json` after code lands.
- Focused pytest modules listed in the validation matrix.

## Risks

- Ensure without conflict rules could destroy user skill trees — mitigated by
  frozen conflict matrix and additive-only API.
- Treating secondary-only as synced false-passes Cursor — mitigated by split
  presence + recon keys.
- Dry-run OOM blocks evidence — mitigated by lazy hashing + compact JSON in
  Wave 1a (contract noted here; implementation deferred).

## Relationship To Sibling

Extend `reconcile-harness-plugins-skills` design: keep its terminal dispositions
and stop rules; add store/projection split and Cursor ensure. Do not pretend the
July reconciliation packet remains green after the new keys land — baseline
reset is expected.
