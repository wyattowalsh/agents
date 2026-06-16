# Affected Surfaces

## Source Of Truth (Owned By This Change)

- `openspec/changes/consolidate-discovery-into-harness-master/` — this change-control set (proposal, design, validation-matrix, tasks, affected-surfaces, specs/skills-lifecycle/spec.md delta).
- `openspec/specs/skills-lifecycle/spec.md` — replace "Discover-skills uses skill-local discovery scripts" requirement (incl. hook scan scenario) with harness-master equivalent naming `skills/harness-master/scripts/discovery/`.
- `skills/harness-master/scripts/discovery/` (and contents) — primary landing for migrated scan, gap, coordinator, journal, validate, parity, check, merge, schemas, _paths, render, npx helpers (inventory_scan.py, gap_engine.py, coordinator.py, hook_scan.py, invoke_surfaces.py, etc.).
- `skills/harness-master/data/discovery/` — taxonomy, schemas, fixtures, agent-targets (moved/adapted from discover-skills/data).
- `skills/harness-master/references/discovery/` — coordinator-contract.md, scout-templates.md, gap-analysis.md, research-*.md, output-formats.md, team-templates.md and related.
- `skills/harness-master/SKILL.md` — dispatch table extension for inferred discovery modes (discover/audit/research/ideate/resume/list/install), vocabulary merge, migration notes, journal path docs.
- `skills/harness-master/scripts/check.py` (top + discovery/ sub) — portable check entrypoints updated for layout.
- `skills/harness-master/scripts/discovery/parity_check.py` — delegation wrapper updated.
- `scripts/check_discovery_parity.py` + `scripts/check_hook_discovery_parity.py` — retarget any legacy paths; primary repo parity.
- `skills/harness-master/evals/` + `evals/evals.json` — absorb harness-bounded discovery evals (implicit-trigger, scope-refusal, w0/w2 cases, etc.).
- `tests/test_discovery_*.py` (gap_engine, coordinator, schemas, hook_scan, parity_check, etc.), `tests/test_skills_no_wagents.py`, `tests/test_distribution_metadata.py` — path/import retargets + new delete-guard coverage.
- `skills/harness-master/scripts/discovery/journal-store.py` — new journal default `~/.agents/harness-master/discovery/`, v1 fallback.
- `skills/harness-master/scripts/discover_surfaces.py`, `invoke_surfaces.py` (discovery/), `usage_probe.py`, `candidate_score.py`, `source_probe.py`, `install_skills.py` — harmonized call sites and docs.
- `skills/harness-master/references/` (harness-surfaces.md, harness-checklists.md, workflow.md, install-guidance.md, etc.) — cross-ref updates.
- `AGENTS.md` — replace /discover-skills usage notes with harness-master inferred discovery.
- `config/external-skills.md` (if listed), curated catalog, docs indexes — remove discover-skills entries.

## Delegated / Complementary (Read-Only or Continued Observation)

- `config/hook-registry.json`, `config/hook-surface-registry.json`, `config/harness-surface-registry.json`, other repo-root registries — SSOT; discovery reads (no ownership change).
- `wagents/cli.py`, parsing, platforms/* — authority for hooks/inventory/validate/sync; discovery observes via scan or npx subprocess.
- `skills/skill-router/scripts/skill_index.py` — still invoked via subprocess from inventory_scan (portable boundary).
- `skills/research/` — untouched; general research remains separate from harness-bounded discover inside harness-master.
- `skills/harness-master/scripts/` (non-discovery) — peer modules; direct calls now preferred inside the unified skill.
- Prior OpenSpec changes (e.g. `add-hook-discovery-parity/`, archived unify changes) — historical; their deltas are superseded in canonical spec only.

## Generated Outputs

- `skills/harness-master/references/discovery/gap-analysis.md` (regenerated post gap engine + render updates).
- `artifacts/<sid>/...` and `~/.agents/harness-master/discovery/<sid>/` (session journals + wave artifacts; not checked in).
- `dist/harness-master-*.skill.zip` (includes discovery/ + data/discovery/ + references/discovery/ post-merge).
- `docs/skills/harness-master.mdx` + other generated skill docs (via wagents docs generate / docs-steward).
- `docs/indexes/*`, `kb/indexes/*` (refreshed maps after delete and doc regen).
- Packaging / install metadata (no discover-skills zip).

## Downstream Agent Artifacts

- GapReport, wave-manifest, scout-artifact consumers (coordinator, orchestrator, sub-agents, journal resume, renderers, evals).
- Wave 2+ scouts (harness-scout, hook-scout, research scouts) now dispatched under harness-master discover flow.
- Journal v2 artifacts (new path).
- Any KB / planning manifests, AGENTS.md examples, external-skill-auditor notes that referenced discover-skills.
- `wagents validate`, openspec, skill list surfaces.

## Tests

- All `tests/test_discovery_*.py` (retargeted + expanded for migration).
- `tests/test_skills_no_wagents.py` (boundary now asserts under harness-master discovery tree).
- `tests/test_discovery_parity_check.py` (wrapper delegation + new layout).
- Distribution / packaging / metadata tests.
- Harness-master evals covering inferred modes + full discover pipeline.
- Portable check execution under copied skill tree simulation (if tested).

## Validation Commands

- `uv run python skills/harness-master/scripts/discovery/check.py`
- `uv run python scripts/check_discovery_parity.py`
- `uv run python scripts/check_hook_discovery_parity.py` (if present)
- `uv run pytest tests/test_discovery_gap_engine.py tests/test_discovery_coordinator.py tests/test_discovery_schemas.py tests/test_discovery_hook_scan.py tests/test_discovery_parity_check.py tests/test_skills_no_wagents.py tests/test_distribution_metadata.py -q`
- Full W0 bash sequence (see validation-matrix.md) using `skills/harness-master/scripts/discovery/*` + `validate_session.py` + `parity_check.py`
- `python skills/harness-master/scripts/discover_surfaces.py --repo-root . --harness grok-build --level both`
- `uv run python skills/harness-master/scripts/discovery/invoke_surfaces.py --repo-root . -o /tmp/surfaces.json`
- `uv run wagents validate`
- `uv run wagents openspec validate` (or `python skills/openspec-workflow/scripts/openspec_cli.py validate`)
- `uv run wagents docs generate` (or docs-steward invocation) + inspection of harness-master page
- Journal smoke: run discovery that writes journal under `~/.agents/harness-master/discovery/`, then `resume` / `list`
- `git status --porcelain` + manual confirmation of `skills/discover-skills/` absence post-delete
- `uv run python -c 'import skills.harness_master.scripts.discovery.coordinator as c; ...'` (package import smoke)
