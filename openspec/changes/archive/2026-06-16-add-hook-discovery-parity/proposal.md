# Proposal

## Problem

Plugins (`plugin_scan.py`), MCP (`mcp_scan.py`), and skills (`inventory_scan.py`) are first-class citizens inside `discover-skills`: each has a dedicated W0 scan script, contributes a top-level section to `GapReport`, participates in Wave 2 scout planning via `coordinator.py`, and is covered by `gap-report.schema.json` + `validate_*` helpers.

Hooks are not. The only visibility today is incidental `kind: "hooks"` file-presence rows (`.codex/hooks.json`, `.cursor/hooks.json`, `.github/hooks/*`, etc.) emitted by `skills/harness-master/scripts/discover_surfaces.py` (invoked via `invoke_surfaces.py`). There is no semantic hook inventory scan against `config/hook-registry.json`, no aggregation of hook declarations from skill/agent frontmatter, no Grok plannotator hook surface, and no `hooks` key in `GapReport`. Consequently `hook-scout` (already timed-out in coordinator) cannot be validated by `validate_wave_manifest` (SCOUT_ROLES) and produces no useful gap signal.

## Intent

Achieve full discovery parity for hooks matching the MCP/plugin model:

- Dedicated `hook_scan.py` (stdlib-only, subprocess delegation pattern, zero `wagents` imports).
- `config/hook-surface-registry.json` extraction so hook file surfaces are not hardcoded only inside discover_surfaces (reducing merge conflicts and enabling hook-scout to reason over surfaces separately from general harness surfaces).
- `hooks` section in `GapReport` (and supporting schema/validate/gap_engine changes).
- `hook-scout` (W2-HK-00) that is report-only (produces `candidates: []` today; no `merge_artifacts` install path for hooks).
- All supporting updates to coordinator contract, SKILL.md, tests, evals, parity, and the skills-lifecycle spec.

## Scope

- Create `openspec/changes/add-hook-discovery-parity/` (this change) with proposal, design, validation-matrix, tasks (HK-001..086 mapping), affected-surfaces.
- Add requirement scenario to `openspec/specs/skills-lifecycle/spec.md` for `hook_scan.py`.
- (Per plan) Introduce:
  - `config/hook-surface-registry.json` + schema (extraction of hook surfaces from discover_surfaces.py).
  - `skills/discover-skills/scripts/hook_scan.py` (and supporting `_hook_collect.py` stdlib helper if needed for pure collection).
  - `skills/discover-skills/data/schemas/hook-scan.schema.json`.
  - Extend `GapReport` dataclass + public_dict + merge + gap_engine + schemas.validate + gap-report.schema.json.
  - Add "hook-scout" to SCOUT_ROLES.
  - Update W0 commands in `skills/discover-skills/references/coordinator-contract.md` to run hook_scan.py.
  - Update `invoke_surfaces.py`? or keep surfaces reporting hooks for file presence while hook_scan owns semantic.
  - Update `skills/discover-skills/scripts/validate_session.py`, `parity_check.py` (or root `scripts/check_discovery_parity.py`), SKILL.md, evals, tests.
  - Hook-scout template / evaluator stub per plan lanes.
  - `scripts/check_discovery_parity.py` extension or new hook parity.
- Keep harness surface discovery's `kind: "hooks"` rows (they remain useful for raw file presence).
- Hook authority (registry, wagents hooks CLI/validate, frontmatter) stays outside discover-skills; discover only observes/ gaps.

## Out Of Scope

- Implementing actionable hook candidates or install/merge path through merge_artifacts (hook-scout remains report-only for this wave).
- Modifying `wagents/` hook collection, validation, or sync logic (except via future shared stdlib if extracted).
- Removing `kind: "hooks"` entries from `discover_surfaces.py` (complementary, not replacement).
- Updating live `~/.codex/hooks.json` etc. or full sync flows.
- Archiving this OpenSpec change before all validation matrix items (incl. W0 pipeline + parity + grok-build discover_surfaces) pass.
- Changes to non-hook harness surfaces or other Wave 0/2 dimensions.

## Affected Users And Tools

- Discovery users (orchestrator, subagent researchers) gain hook gap visibility in GapReport.
- `discover-skills` maintainers and parity check authors.
- Harness surface consumers (unchanged for file surfaces).

## Generated Surfaces To Refresh

- `skills/discover-skills/references/coordinator-contract.md`
- `skills/discover-skills/references/gap-analysis.md` (via render after gap schema change)
- Possibly generated docs referencing discovery.

## Risks

- Duplication risk if _hook_collect logic not kept minimal; mitigated by "no wagents import" rule + subprocess pattern.
- Coordinator expected_count and cap (24) must accommodate the fixed HK-00 task without blowing the budget.
- Parallel wave execution must keep non-overlapping ownership (HK tasks touch different files than harness-scout etc.).
