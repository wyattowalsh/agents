# Affected Surfaces

## Source Of Truth (Owned By This Change)

- `openspec/changes/add-hook-discovery-parity/` — this change-control set (proposal, design, validation-matrix, tasks, affected-surfaces).
- `openspec/specs/skills-lifecycle/spec.md` — add hook_scan subprocess scenario requirement.
- `config/hook-surface-registry.json` — new (extracted hook surfaces).
- `config/schemas/hook-surface-registry.schema.json` — new schema.
- `skills/discover-skills/data/schemas/hook-scan.schema.json` — new contract.
- `skills/discover-skills/scripts/hook_scan.py` — new scan (subprocess delegation, no wagents).
- `skills/discover-skills/scripts/_hook_collect.py` — new (or updated) stdlib-only collection helper.
- `skills/discover-skills/scripts/schemas.py` — GapReport extension, validate_hook_scan wiring, SCOUT_ROLES add "hook-scout".
- `skills/discover-skills/scripts/gap_engine.py` — --hooks arg, merge, GapReport construction.
- `skills/discover-skills/scripts/validate_session.py` — hook-scan presence + validation routing.
- `skills/discover-skills/scripts/coordinator.py` — (minor) confirm hook-scout; timeout already present.
- `skills/discover-skills/references/coordinator-contract.md` — W0 command list update (add hook_scan.py + gap --hooks).
- `skills/discover-skills/references/scout-templates.md` — hook-scout report-only template.
- `skills/discover-skills/SKILL.md` — orchestration notes, completion criteria.
- `skills/discover-skills/evals/evals.json` — new eval cases for hook dimension.
- `skills/harness-master/scripts/discover_surfaces.py` — extraction of hook surfaces (read + optional load from registry).
- `scripts/check_discovery_parity.py` — hook count / surface parity assertions.
- `skills/discover-skills/scripts/parity_check.py` — (if wrapper change needed).
- `tests/test_discovery_hook_scan.py` (new), updates to `tests/test_discovery_gap_engine.py`, `tests/test_discovery_coordinator.py`, `tests/test_discovery_schemas.py`, `tests/test_skills_no_wagents.py`, `tests/test_discovery_parity_check.py`.
- `skills/discover-skills/scripts/render_gap_reference.py` — (if it needs to handle new section).
- `skills/discover-skills/data/schemas/gap-report.schema.json` — add hooks property.
- `skills/discover-skills/scripts/_paths.py` — (possible minor update for new schema path).

## Delegated / Complementary (Read-Only or Continued Reporting)

- `skills/harness-master/scripts/discover_surfaces.py` (hook `kind` rows remain for file presence; Grok Build etc. continue to discover them via invoke_surfaces).
- `config/hook-registry.json` — observed (source of semantic truth), not owned by discover.
- `wagents/cli.py` ( _collect_hooks, hooks_list/validate ) — authority for CLI; discover observes via scan.
- `wagents/parsing.py` (extract_hooks) — reference only (reimplemented stdlib in _hook_collect).
- `platforms/*/ *.py` (render_hooks etc.) — unchanged.

## Generated Outputs

- `skills/discover-skills/references/gap-analysis.md` (regenerated after gap schema + engine changes).
- `artifacts/<sid>/wave0/hook-scan.json`, `gap-report.json` (session artifacts, not checked in).
- `dist/discover-skills-*.skill.zip` (via packaging in check).

## Downstream Agent Artifacts

- GapReport consumers (coordinator, orchestrator, journal, subagents, renderers).
- Wave 2 HK-00 hook-scout artifacts (report-only).
- Any KB / planning manifests that enumerate discovery dimensions (mcp/plugins/harness → +hooks).

## Tests

- New and updated tests under `tests/test_discovery_*.py` (see Source Of Truth).
- `tests/test_skills_no_wagents.py` (boundary enforcement for hook_scan + _hook_collect).
- Parity test updates.

## Validation Commands

- `uv run python skills/discover-skills/scripts/check.py`
- `uv run python scripts/check_discovery_parity.py`
- `uv run pytest tests/test_discovery_gap_engine.py tests/test_discovery_coordinator.py tests/test_discovery_schemas.py tests/test_discovery_hook_scan.py tests/test_skills_no_wagents.py tests/test_discovery_parity_check.py -q`
- Full W0 bash sequence (see validation-matrix.md) + `coordinator.py plan --wave 2` + verify with HK-00 stub.
- `python skills/harness-master/scripts/discover_surfaces.py --repo-root . --harness grok-build --level both`
- `uv run wagents openspec validate` (or equivalent openspec cli)
- `uv run wagents hooks validate --format json` (cross-check, non-gate)
