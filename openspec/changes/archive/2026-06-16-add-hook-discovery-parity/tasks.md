# Tasks

## OpenSpec (HK-001..005)

- [ ] HK-001: Create `openspec/changes/add-hook-discovery-parity/` directory.
- [ ] HK-002: Write `proposal.md` (problem, intent, full-parity scope, out-of-scope, risks).
- [ ] HK-003: Write `design.md` (hook-surface-registry extraction, hook_scan subprocess pattern, GapReport hooks, hook-scout report-only, no-wagents rule).
- [ ] HK-004: Write `validation-matrix.md` (W0 incl. hook_scan.py + grok-build discover_surfaces + parity).
- [ ] HK-005: Write `tasks.md` (this file) + `affected-surfaces.md`; map all to HK-001..086 lanes.

## Foundation & Schemas (HK-006..015)

- [ ] HK-006: Add `skills/discover-skills/data/schemas/hook-scan.schema.json` (minimal version+registry contract).
- [ ] HK-007: Implement `validate_hook_scan` usage + wire into `_validate_with_schema("hook-scan")` (schemas.py).
- [ ] HK-008: Extend SCOUT_ROLES to include "hook-scout".
- [ ] HK-009: Extend GapReport dataclass with `hooks: dict = field(default_factory=dict)`.
- [ ] HK-010: Update GapReport.public_dict() to emit "hooks".
- [ ] HK-011: Update gap-report.schema.json to declare "hooks" property (object).
- [ ] HK-012: Add `validate_gap_report` tolerance / explicit hooks checks.
- [ ] HK-013: Create/update supporting tests for new schema and GapReport shape.
- [ ] HK-014: Ensure test_skills_no_wagents.py covers the new hook_scan module path.
- [ ] HK-015: Update evals/evals.json with hook discovery cases (implicit-trigger etc.).

## hook-surface-registry.json Extraction (HK-016..025)

- [ ] HK-016: Design + write `config/hook-surface-registry.json` (project/global hook paths per harness, labels, roles).
- [ ] HK-017: Create `config/schemas/hook-surface-registry.schema.json`.
- [ ] HK-018: Add references/docs for the new registry (sync-manifest, harness-fixture-support, etc. if needed).
- [ ] HK-019: Extract hook entries from `skills/harness-master/scripts/discover_surfaces.py` PROJECT_SURFACES/GLOBAL_SURFACES (keep inline or load for transition).
- [ ] HK-020: Update discover_surfaces.py to optionally load hook surfaces from the registry (or document dual maintenance during transition).
- [ ] HK-021: Update harness-surface-registry.json projection notes if hook surfaces move in classification.
- [ ] HK-022: Add tests for hook-surface-registry loading / validation.
- [ ] HK-023: Update any planning manifests or kb sources referencing the old hardcoded surfaces.
- [ ] HK-024: Ensure `wagents/docs.py` or distribution tests still see hook surfaces via harness registry path.
- [ ] HK-025: Run full surface discovery dry-run for all harnesses (incl. grok-build, codex, cursor, copilot) post-extraction.

## hook_scan.py + _hook_collect (HK-026..043)

- [ ] HK-026: Create `skills/discover-skills/scripts/hook_scan.py` (argparse --repo-root -o, main entry).
- [ ] HK-027: Implement `collect_hooks(...)` that loads `config/hook-registry.json` (stdlib json).
- [ ] HK-028: Add subprocess delegation pattern inside hook_scan (e.g. to a local collector script or skill-router hooks helper) matching inventory_scan.py exactly in style.
- [ ] HK-029: Create `skills/discover-skills/scripts/_hook_collect.py` (pure stdlib, shared collection for registry + frontmatter scan + embedded; no wagents.* imports).
- [ ] HK-030: Support scanning ./hooks/ directory for script presence + mapping to registry ids.
- [ ] HK-031: Aggregate harness coverage from hook-registry.json "harnesses" arrays.
- [ ] HK-032: Detect blind spots (Grok plannotator, external skill frontmatter hooks, UI-only hooks).
- [ ] HK-033: Produce output shape: { "version":1, "registry": {...}, "present": [...], "gaps": [...], "blind_spots": [...], "file_surfaces": [...] } or per design.
- [ ] HK-034: Wire `write_json` + call `schemas.validate_hook_scan` inside hook_scan before write; fail hard on error.
- [ ] HK-035: Add --format json etc. parity with sibling scans.
- [ ] HK-036: Update `skills/discover-skills/scripts/_paths.py` if new data or script helpers needed.
- [ ] HK-037: Add unit tests `tests/test_discovery_hook_scan.py`.
- [ ] HK-038: Ensure hook_scan never imports wagents (enforce in test + import guard).
- [ ] HK-039: Support repo_root resolution identical to inventory/mcp/plugin scans.
- [ ] HK-040: Handle missing registry gracefully (emit versioned empty report + note).
- [ ] HK-041: Add coverage for Codex research hooks, session-start, stop-verifier etc. from existing registry.
- [ ] HK-042: Dry-run hook_scan and diff output vs `wagents hooks list --format json` (semantic parity check, non-blocking for gate).
- [ ] HK-043: Integrate hook_scan into portable `check.py` for the discover-skill.

## Gap Engine & Hook Section (HK-044..053)

- [ ] HK-044: Update `gap_engine.py` `merge_asset_sections` to accept `hooks=...`.
- [ ] HK-045: Extend `build_gap_report(..., hooks=...)`.
- [ ] HK-046: Pass `--hooks` from main() and load_json for it.
- [ ] HK-047: Default hooks section to {"present": [], "gaps": [], "blind_spots": []} when absent.
- [ ] HK-048: Include hooks in GapReport.public_dict().
- [ ] HK-049: Update `render_gap_reference.py` to render new hooks section in generated gap-analysis.md.
- [ ] HK-050: Add gap-engine tests that assert hooks section appears and is mergeable.
- [ ] HK-051: Validate full gap-report after adding hook-scan input in test fixtures.
- [ ] HK-052: Update any hardcoded gap report expectations in evals or tests.
- [ ] HK-053: Run `validate_gap_report` explicitly on payloads containing hooks.

## Coordinator, Scout, Contract Updates (HK-054..065)

- [ ] HK-054: Confirm / add "hook-scout" to SCOUT_ROLES in schemas.py (already in coordinator timeout).
- [ ] HK-055: Update coordinator.py plan_wave (if needed) to keep the existing W2-HK-00 emission.
- [ ] HK-056: Update `skills/discover-skills/references/coordinator-contract.md` W0 block with hook_scan.py line + gap_engine --hooks.
- [ ] HK-057: Add hook-scan.json to journal/artifact layout docs and examples.
- [ ] HK-058: Implement or stub `skills/discover-skills/references/scout-templates.md` entry for hook-scout (report-only guidance).
- [ ] HK-059: Create evaluator stub / eval case for hook-scout (report-only, no candidates).
- [ ] HK-060: Update `validate_session.py` to validate presence + schema of hook-scan.json when in wave0 dir.
- [ ] HK-061: Extend `coordinator.py verify` handling if special casing needed for HK-00 (should be generic).
- [ ] HK-062: Update MAX_WAVE2_TASKS accounting / comments if the fixed HK slot pushes near cap.
- [ ] HK-063: Add coordinator tests for hook-scout task emission and verify with HK artifact.
- [ ] HK-064: Update SKILL.md orchestration / completion criteria mentioning hook dimension.
- [ ] HK-065: Ensure merge_artifacts.py ignores or handles hook artifacts (no change to merge logic).

## Parity, Check, and Validation Scripts (HK-066..075)

- [ ] HK-066: Extend root `scripts/check_discovery_parity.py` with hook section (e.g. registry hook count vs scan).
- [ ] HK-067: Or add dedicated hook parity assertion (document choice in parity_check).
- [ ] HK-068: Update `skills/discover-skills/scripts/parity_check.py` to delegate to the (extended) root parity script.
- [ ] HK-069: Add hook-scan vs wagents hooks list count parity (optional, audit-only).
- [ ] HK-070: Run full `uv run python scripts/check_discovery_parity.py` and assert ok.
- [ ] HK-071: Add discovery parity test `tests/test_discovery_parity_check.py` coverage for hooks.
- [ ] HK-072: Update discover-skills check.py if it hardcodes the other scans.
- [ ] HK-073: Run `uv run python skills/discover-skills/scripts/check.py` end-to-end.
- [ ] HK-074: `uv run wagents validate` + `uv run wagents hooks validate`.
- [ ] HK-075: Schema validation for new hook-surface-registry and hook-scan.schema.

## Wave 2 Hook-Scout (Report-Only) (HK-076..081)

- [ ] HK-076: Write minimal hook-scout prompt / instructions per scout-templates (report gaps + registry summary, candidates=[]).
- [ ] HK-077: Produce sample W2-HK-00.json artifact (success, candidates: [], errors:[], provenance noting hook-scan input).
- [ ] HK-078: Verify accounting: coordinator verify returns ok with HK-00 present.
- [ ] HK-079: Ensure merge_artifacts does not treat HK artifact as candidate source (no side effects).
- [ ] HK-080: Add harness-scout vs hook-scout distinction note (harness = all surfaces incl file hooks; hook = semantic registry + coverage).
- [ ] HK-081: Update any research-integration or team-templates docs.

## Final Validation, Docs, Archive Prep (HK-082..086)

- [ ] HK-082: Execute full manual W0 + plan + stub HK scout + verify; capture artifacts.
- [ ] HK-083: Run targeted pytest for all new + touched discovery tests; zero regressions.
- [ ] HK-084: Run validation matrix commands (incl. grok-build discover_surfaces, parity, openspec validate).
- [ ] HK-085: Refresh generated references (gap-analysis.md) and confirm docs build if applicable.
- [ ] HK-086: Update this tasks.md to mark all complete; prepare for archive after user sign-off (do not auto-archive).

## Documentation

- [ ] Refresh SKILL.md, coordinator-contract.md, scout-templates.md, gap-analysis.md, and any xref in AGENTS.md / START-HERE.
- [ ] Invoke docs-steward if generated artifacts are produced.

## Verification

- [ ] All items HK-001..086 executed or explicitly deferred with note.
- [ ] `uv run python skills/discover-skills/scripts/check.py`
- [ ] Full W0 + coordinator verify pipeline green.
- [ ] `uv run pytest ...` (discovery suite + no-wagents + parity tests)
- [ ] `uv run python scripts/check_discovery_parity.py`
- [ ] OpenSpec + skills-lifecycle spec validation.
- [ ] Manual diff: before/after hook surfaces in discover_surfaces + new registry.
