# Affected Surfaces

## Source Of Truth (contracts this change)

- `openspec/changes/fleet-skill-projection-assurance/proposal.md`
- `openspec/changes/fleet-skill-projection-assurance/design.md`
- `openspec/changes/fleet-skill-projection-assurance/tasks.md`
- `openspec/changes/fleet-skill-projection-assurance/affected-surfaces.md`
- `openspec/changes/fleet-skill-projection-assurance/validation-matrix.md`
- `openspec/changes/fleet-skill-projection-assurance/specs/skills-lifecycle/spec.md`
- `openspec/changes/fleet-skill-projection-assurance/specs/cursor-harness/spec.md`
- `openspec/changes/fleet-skill-projection-assurance/specs/ux-cli/spec.md`
- `openspec/changes/fleet-skill-projection-assurance/specs/skill-registry-intake/spec.md`

## Sibling / live specs referenced (not flipped in Wave 0)

- `openspec/changes/reconcile-harness-plugins-skills/**` — sibling extend target
- `openspec/specs/skills-lifecycle/spec.md`
- `openspec/specs/cursor-harness/spec.md`
- `openspec/specs/ux-cli/spec.md`
- `openspec/specs/skill-registry-intake/spec.md`
- `docs/src/content/docs/harness-config/plugin-skill-ownership.mdx` (docs wave)
- `skills/harness-master/references/harness-surfaces.md` (docs wave)

## Implementation surfaces (Wave 1+ only — not edited in Wave 0)

| Path | Owner | Notes |
| --- | --- | --- |
| `wagents/skill_coverage.py` | W1-INV | New shared presence SSOT |
| `wagents/installed_inventory.py` | W1-INV | Tiers + lazy hash |
| `wagents/platforms/cursor.py` | W1-CUR | Ensure helper; leave `_sync_skill_symlinks` |
| `wagents/cli.py` | W1-SYNC | Planner buckets + apply wiring |
| `scripts/generate_harness_reconciliation.py` | W1-RECON | Recon keys |
| `planning/manifests/harness-reconciliation.json` | W1-RECON | Regenerated packet |
| Hand docs (ownership, surfaces, CLI) | W1-DOCS | Store ≠ durable sync |
| Focused `tests/test_*.py` | W1-TEST | Presence + ensure + planner |

## Generated Outputs

- None in Wave 0.
- Later: recon JSON, optional docs regenerate after hand-doc edits.

## Downstream Agent Artifacts

- None written in Wave 0.
- Post–apply-gate (human): additive `~/.cursor/skills/<name>` → store realpaths.

## Tests (planned, Wave 1b)

- `tests/test_installed_inventory.py`
- `tests/test_sync_desired_skills.py`
- `tests/test_skills_sync_pin_gate.py`
- `tests/test_harness_reconciliation.py`
- `tests/test_cursor_skill_ensure.py` (new)

## Validation Commands

See `validation-matrix.md`. Wave 0 required: `uv run wagents openspec validate`.

## Local-only surfaces inspected, not modified

- `~/.agents/skills` (store)
- `~/.cursor/skills` (sparse projection)
- `.cursor/skills/repo` (project; out of global ensure scope)
- Home Codex/OpenCode/Crush skill roots (reporting only)

## Out Of Scope Writes

- Production Python (`wagents/`, `scripts/`) in Wave 0
- `skills sync --apply`, live `npx skills add`, mass home symlinks, cleanup `--apply`
- Plan file edits
