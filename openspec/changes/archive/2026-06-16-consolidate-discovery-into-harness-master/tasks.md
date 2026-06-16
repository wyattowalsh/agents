# Tasks

## OpenSpec (CD-001..008)

- [ ] CD-001: Create `openspec/changes/consolidate-discovery-into-harness-master/` directory.
- [ ] CD-002: Write `proposal.md` (merge discover-skills into harness-master, delete discover-skills, inferred modes, journal unification).
- [ ] CD-003: Write `design.md` (authoritative layout under scripts/discovery + data/discovery, journal ~/.agents/harness-master/discovery/, mode inference, no-wagents boundary, research split).
- [ ] CD-004: Write `validation-matrix.md` (W0 under new paths, harness-master check + portable, parity, grok-build surfaces, openspec validate, coordinator + inferred dispatch).
- [ ] CD-005: Write `tasks.md` (this file) + `affected-surfaces.md`.
- [ ] CD-006: Write `specs/skills-lifecycle/spec.md` delta (replace discover-skills requirement text + hook scenario with harness-master/scripts/discovery naming and paths).
- [ ] CD-007: Update `openspec/specs/skills-lifecycle/spec.md` canonical text to the new harness-master discovery requirement (absorbing prior hook parity scenario).
- [ ] CD-008: Run `uv run wagents openspec validate` (or equivalent) and confirm this change + all specs pass (47/47 or current count).

## Migration Audit & Planning (CD-009..020)

- [ ] CD-009: Full blast-radius grep for `discover-skills` (code, docs, tests, configs, AGENTS.md, KB, external refs) + produce inventory.
- [ ] CD-010: Audit `discover-skills` vs `harness-master` path usage in scripts (config/ vs data/discovery/, _paths.py, subprocess strings).
- [ ] CD-011: Map journal paths in `journal-store.py`, SKILL.md, references, tests; plan v1/v2 compatibility + new default.
- [ ] CD-012: Inventory tests: `tests/test_discovery_*.py`, `test_skills_no_wagents.py`, distribution/packaging tests, parity tests.
- [ ] CD-013: Inventory evals: merge relevant cases from `skills/discover-skills/evals/evals.json` into harness-master.
- [ ] CD-014: Review prior hook-parity artifacts (still satisfy updated spec after path change).
- [ ] CD-015: Confirm standalone `skills/research/` untouched; document boundary.
- [ ] CD-016: Produce migration runbook / task graph (parallel lanes: scripts+data, dispatch+SKILL, tests+parity, docs+delete).
- [ ] CD-017: Update any plan artifacts or goals referencing the consolidation.
- [ ] CD-018: Ensure `config/` registries are not modified by the merge (read-only observation).
- [ ] CD-019: Decide on thin shim or immediate hard delete (prefer immediate after green validation).
- [ ] CD-020: Snapshot current `wagents validate` + openspec + pytest discovery suite + parity ok.

## Scripts / Data / References Move (CD-021..045)

- [ ] CD-021: Ensure `skills/harness-master/scripts/discovery/` contains (or receives) the full set: inventory_scan.py, mcp_scan.py, plugin_scan.py, hook_scan.py, _hook_collect.py, invoke_surfaces.py, gap_engine.py, coordinator.py, validate_session.py, merge_artifacts.py, journal-store.py, schemas.py, _paths.py, parity_check.py, check.py, render_gap_reference.py, npx_skills.py + __init__ if needed.
- [ ] CD-022: Move/adapt `skills/discover-skills/data/` → `skills/harness-master/data/discovery/` (taxonomy, agent-targets, schemas/, fixtures/).
- [ ] CD-023: Move/adapt discovery references → `skills/harness-master/references/discovery/` (coordinator-contract.md, scout-templates.md, gap-analysis.md, research-*.md, output-formats.md, team-templates.md, research-queries.md etc.).
- [ ] CD-024: Move relevant evals cases into harness-master/evals/ (or data/discovery/evals); update evals.json.
- [ ] CD-025: Update all internal path strings, imports, and `_paths.py` constants for new locations (data/discovery, discovery/ subpackage).
- [ ] CD-026: Update `invoke_surfaces.py` to prefer in-package call to `../discover_surfaces.py` (or relative) while keeping subprocess wrapper option for portable parity_check.
- [ ] CD-027: Update `gap_engine.py`, `coordinator.py`, `validate_session.py` for new taxonomy/schema paths and harness-master package.
- [ ] CD-028: Update `journal-store.py` defaults + init to `~/.agents/harness-master/discovery/<sid>`, keep v1 legacy fallback for resume.
- [ ] CD-029: Update `schemas.py` (if any hard-coded skill names), SCOUT_ROLES, GapReport helpers (no functional change).
- [ ] CD-030: Update `parity_check.py` (under discovery/) to be thin delegation wrapper (call repo `scripts/check_discovery_parity.py` + hook variant when present).
- [ ] CD-031: Update `check.py` (discovery/ and top-level harness scripts/check.py) for new internal paths; keep portable contract (validate + evals + audit + package dry-run).
- [ ] CD-032: Update `render_gap_reference.py` output paths / headings if needed.
- [ ] CD-033: Adapt `npx_skills.py` and other collectors if they embed old skill names.
- [ ] CD-034: Ensure no direct `import wagents` in any file now under `skills/harness-master/scripts/discovery/`.
- [ ] CD-035: Add/update `__pycache__` cleanup or .gitignore as needed (post-move).
- [ ] CD-036: Run the moved `inventory_scan.py` etc. standalone smoke (exit 0, produce valid JSON).
- [ ] CD-037: Run moved `gap_engine.py` + `validate_session.py` end-to-end on sample artifacts.
- [ ] CD-038: Run moved `coordinator.py plan --wave 0/2` and verify accounting.
- [ ] CD-039: Execute full W0 sequence under new paths into a temp artifacts dir; validate outputs.
- [ ] CD-040: Update any shebangs or direct-exec assumptions.
- [ ] CD-041: Harmonize top-level `skills/harness-master/scripts/check.py` vs `scripts/discovery/check.py`.
- [ ] CD-042: Move or symlink any remaining top-level discovery helpers if present in old discover-skills/scripts/.
- [ ] CD-043: Update `skills/harness-master/scripts/discovery/_paths.py` (or equivalent) for journal + data resolution under harness-master.
- [ ] CD-044: Ensure `discover_surfaces.py` (at harness scripts/) and discovery/invoke remain consistent on hook surfaces etc.
- [ ] CD-045: Dry-run `python -m pyright` / ruff / ty on the migrated discovery tree (or project equivalent).

## Harness-Master Dispatch + Inferred Modes (CD-046..060)

- [ ] CD-046: Extend dispatch table in `skills/harness-master/SKILL.md` with discovery rows (discover, audit, research, ideate, resume, list, install) + inference rules from prior discover-skills.
- [ ] CD-047: Implement / update mode normalization + heuristic in harness-master entry logic (or dedicated dispatcher) to route to discovery pipeline.
- [ ] CD-048: Merge vocabulary table (gap, coverage, coordinator, journal, auditor, registry-scout, web-researcher, ideator) into harness-master docs.
- [ ] CD-049: Add "inferred modes" section explaining natural language triggers and auto-detection (domain → research, question → full discover, etc.).
- [ ] CD-050: Document safety: discovery paths read-only; apply only via explicit `apply approved`.
- [ ] CD-051: Update argument-hint and supported tokens.
- [ ] CD-052: Add redirect notes for legacy `/discover-skills` phrasing (in SKILL.md + AGENTS.md).
- [ ] CD-053: Update NOT FOR / redirect table (skill-creator, find-skills, general research → research skill).
- [ ] CD-054: Wire research category handling (`research <harness|all> <config|mcp|skill|...>`) to reuse the unified W0–W4 discover pipeline where appropriate.
- [ ] CD-055: Preserve existing harness-master modes (usage, candidate, compare, sources, apply, intake) unchanged.
- [ ] CD-056: Add examples in SKILL.md for `/harness-master discover`, `/harness-master audit claude-code both`, `/harness-master research all skill "cache"`.
- [ ] CD-057: Update any harness-specific notes (Grok Build, Codex, etc.) if they referenced discovery separately.
- [ ] CD-058: Test dispatch manually (empty, keywords, natural language) via skill invocation or unit harness.
- [ ] CD-059: Ensure `harness-master` evals cover inferred discovery triggers.
- [ ] CD-060: Regenerate or refresh any derived dispatch docs.

## Retarget References, Tests, Parity, Checks (CD-061..085)

- [ ] CD-061: Update `skills/harness-master/references/discovery/coordinator-contract.md` W0 block with new script paths (harness-master/scripts/discovery/...).
- [ ] CD-062: Update `scout-templates.md`, `gap-analysis.md`, `research-integration.md`, `output-formats.md`, `team-templates.md`.
- [ ] CD-063: Retarget `scripts/check_discovery_parity.py` (and hook variant) — confirm or fix any discover-skills strings.
- [ ] CD-064: Update `skills/harness-master/scripts/discovery/parity_check.py` delegation + tests.
- [ ] CD-065: Create/update `tests/test_discovery_*.py` (or move/adapt) so all import from harness-master discovery modules; zero path breakage.
- [ ] CD-066: Update `tests/test_skills_no_wagents.py` globs/paths/asserts for `harness-master/scripts/discovery` (and scripts/ peers); keep strict no-wagents.
- [ ] CD-067: Update `tests/test_discovery_parity_check.py` (wrapper delegation test) for new layout.
- [ ] CD-068: Run full discovery pytest suite: `uv run pytest tests/test_discovery_*.py tests/test_skills_no_wagents.py -q --tb=line`.
- [ ] CD-069: Run repo parity: `uv run python scripts/check_discovery_parity.py` (expect ok).
- [ ] CD-070: Run hook parity if separate: `uv run python scripts/check_hook_discovery_parity.py`.
- [ ] CD-071: Run portable in-skill check: `uv run python skills/harness-master/scripts/discovery/check.py` (and top-level scripts/check.py).
- [ ] CD-072: Update any `tests/test_distribution_metadata.py` or packaging tests that enumerate discover-skills.
- [ ] CD-073: Add consolidation coverage: test that legacy discover-skills paths are absent (or redirect).
- [ ] CD-074: Update `skills/harness-master/scripts/discovery/check.py` audit score target if evals moved.
- [ ] CD-075: Fix any import errors surfaced by running moved modules as packages.
- [ ] CD-076: Validate GapReport + hook section + scout artifacts still produced and validated under new paths.
- [ ] CD-077: Update `validate_session.py` routing if it had skill-name assumptions.
- [ ] CD-078: Ensure `merge_artifacts.py` and coordinator verify still function.
- [ ] CD-079: Run `python skills/harness-master/scripts/discover_surfaces.py --repo-root . --harness grok-build --level both` (smoke, no regression on hooks/surfaces).
- [ ] CD-080: Run `uv run python skills/harness-master/scripts/discovery/invoke_surfaces.py ...` (post-merge).
- [ ] CD-081: Cross-check `wagents hooks validate` and discovery hook parity.
- [ ] CD-082: Update any CI / Makefile / pre-commit references to discovery paths.
- [ ] CD-083: Retarget KB indexes / repo-map / source-map if they hardcode discover-skills.
- [ ] CD-084: Update `skills/harness-master/references/harness-checklists.md` or surfaces docs if they cross-link.
- [ ] CD-085: Re-run `uv run pytest ... -q` + parity + portable check after all retargets; zero regressions.

## Journals, Artifacts, Packaging, Generated (CD-086..100)

- [ ] CD-086: Implement + test journal v2 path under `~/.agents/harness-master/discovery/`.
- [ ] CD-087: Add compatibility loader for v1 journals in legacy locations (document + test resume from old path).
- [ ] CD-088: Update journal layout docs in references and SKILL.md.
- [ ] CD-089: Produce sample journal + artifacts using new default path; validate resume/list.
- [ ] CD-090: Update packaging (skill zip manifest) to include data/discovery/, scripts/discovery/, references/discovery/.
- [ ] CD-091: Remove discover-skills from any `dist/*.zip` generation or external catalog after delete.
- [ ] CD-092: Run `wagents docs generate` (or docs-steward) and verify harness-master docs surface the discovery flows.
- [ ] CD-093: Refresh `docs/skills/harness-master.mdx` (and remove discover-skills page if generated).
- [ ] CD-094: Update `AGENTS.md` sections that mention `/discover-skills` (audit-before-record etc.).
- [ ] CD-095: Update `config/external-skills.md` or curated lists if discover-skills was listed (remove).
- [ ] CD-096: Regenerate gap-analysis.md via render_gap_reference after a W0 run.
- [ ] CD-097: Update any mdx or generated skill pages for dispatch examples.
- [ ] CD-098: Validate `uv run wagents validate` still green.
- [ ] CD-099: Check `uv run wagents skills list` (or equivalent) no longer advertises discover-skills.
- [ ] CD-100: Snapshot before/after journal dir layout and artifact metadata.

## Delete, Cleanup, Deprecation (CD-101..115)

- [ ] CD-101: After green validation matrix, delete `skills/discover-skills/` tree (rm -rf or equivalent).
- [ ] CD-102: Remove any remaining symlinks, pycache, or empty dirs left from old location.
- [ ] CD-103: Delete or archive discover-skills references in goals/ or openspec/changes/archive/ as appropriate (do not delete historical hook-parity change).
- [ ] CD-104: Clean .gitignored artifacts or temp session dirs that may have old names.
- [ ] CD-105: Update any lockfiles, uv cache, or installed skill metadata if discover-skills was installed.
- [ ] CD-106: Confirm `wagents skills sync --dry-run` no longer sees discover-skills.
- [ ] CD-107: Remove discover-skills from `opencode.json`, `mcp.json`, or other skill manifests if listed.
- [ ] CD-108: If a thin redirect shim was added temporarily, remove it.
- [ ] CD-109: Run full `git status` + `git diff --stat` to list all changes (moves + deletes + edits).
- [ ] CD-110: Ensure no stray imports or strings referencing `skills/discover-skills` remain in source (except historical docs in archived changes).
- [ ] CD-111: Rebuild dist if needed and confirm harness-master zip size increased appropriately.
- [ ] CD-112: Update any release notes or changelog entries for the merge.
- [ ] CD-113: Mark tasks complete in this file up to deletion gate.
- [ ] CD-114: Prepare archive notes for this change (after user sign-off).
- [ ] CD-115: Do not auto-archive; wait for explicit validation + review.

## Documentation

- [ ] Refresh SKILL.md (harness-master), all references/discovery/*.md, AGENTS.md, START-HERE.md, KB indexes.
- [ ] Run docs generation / steward for skill pages.
- [ ] Update external references (if any) and curated catalog notes.
- [ ] Add migration note to harness-master SKILL.md and coordinator-contract.md.

## Verification

- [ ] All CD-001..115 executed or explicitly deferred with note in tasks.md.
- [ ] `uv run python skills/harness-master/scripts/discovery/check.py`
- [ ] `uv run python scripts/check_discovery_parity.py` (and hook variant)
- [ ] Full W0 + coordinator plan/verify pipeline under harness-master paths + journal in ~/.agents/harness-master/discovery/
- [ ] `uv run pytest tests/test_discovery_*.py tests/test_skills_no_wagents.py -q`
- [ ] `uv run wagents validate`
- [ ] `uv run wagents openspec validate` (this change present + skills-lifecycle updated)
- [ ] Manual dispatch smoke: harness-master with inferred discover/audit/research keywords
- [ ] `python skills/harness-master/scripts/discover_surfaces.py ...` (grok-build + others) still green
- [ ] Journal resume/list works from new path (v2) + legacy fallback tested
- [ ] Zero references to live `skills/discover-skills/` in non-archived source/docs
- [ ] Dist / packaging + docs refresh succeed
