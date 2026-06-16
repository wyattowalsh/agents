# Proposal

## Problem

`discover-skills` owns the full discovery pipeline (W0 deterministic scans via `inventory_scan.py`/`mcp_scan.py`/`plugin_scan.py`/`invoke_surfaces.py`/`hook_scan.py`/`gap_engine.py`, `coordinator.py` for wave planning + scout accounting, `validate_session.py` + parity, `merge_artifacts.py`, journal-store, evals, references like coordinator-contract.md / scout-templates.md / gap-analysis.md, and the SKILL.md dispatch for audit/research/ideate/resume/install modes). At the same time `harness-master` owns harness surface discovery (`discover_surfaces.py`, `usage_probe.py`, `candidate_score.py`, `source_probe.py`), ecosystem research entry points, install flows, and is the designated harness control plane.

This split creates:
- Duplicate orchestration stories (ecosystem-research.md W0-W4 vs discover-skills coordinator).
- Subprocess indirection (`invoke_surfaces.py` calling into harness-master) that can be in-process after merge.
- Journal fragmentation (`~/.*/discover-skills/` per harness) vs unified under harness-master.
- Path drift and maintenance (parity_check.py wrappers, check.py, tests/test_discovery_*, spec naming "discover-skills").
- User confusion: two skills for overlapping harness-gap + research concerns.
- Spec drift: `skills-lifecycle/spec.md` still mandates behavior under `skills/discover-skills/scripts/`.

Prior hook-parity work (add-hook-discovery-parity) was implemented under the discover-skills tree; consolidation is the follow-up to fully own discovery inside harness-master.

## Intent

Fully merge `discover-skills` discovery assets and logic into `harness-master`:
- Move pipeline to `skills/harness-master/scripts/discovery/`, `data/discovery/`, `references/discovery/`, evals (harness-bounded), etc.
- Delete `skills/discover-skills/` directory and skill entirely (no deprecation stub).
- Update `harness-master` SKILL.md dispatch table and normalization to support **inferred modes** (empty / `discover` / `audit` / `research [focus]` / `ideate` / `resume` / `list` / `install <...>` inferred from user goal + args; no separate skill entrypoint).
- Fold harness-bounded ecosystem research and scouts into the unified discover pipeline inside harness-master.
- Retarget journals to `~/.agents/harness-master/discovery/` (with optional v1 migration support).
- Retarget all call sites, tests, parity guards, docs generation, OpenSpec, and the `skills-lifecycle` spec to name `harness-master/scripts/discovery` paths.
- Preserve `skills/research/` as standalone for general/non-harness deep research.
- Keep `wagents` authority and repo-root `config/*-registry.json` as SSOT; discovery observes (via stdlib/subprocess where needed).
- Update `test_skills_no_wagents.py` boundary to cover the new location under harness-master.

## Scope

- Create `openspec/changes/consolidate-discovery-into-harness-master/` (this change) containing proposal.md, design.md, tasks.md, affected-surfaces.md, validation-matrix.md, and `specs/skills-lifecycle/spec.md` delta.
- Replace the "Discover-skills uses skill-local discovery scripts" requirement (and its hook scenario) in both `openspec/specs/skills-lifecycle/spec.md` and the per-change delta with equivalent language naming `harness-master/scripts/discovery/`.
- Physical migration of discovery scripts, data, references, evals, SKILL dispatch updates (inferred modes), journal-store updates for new path + session_version, coordinator + gap + scan updates for new locations (in-package where possible).
- Retarget: `scripts/check_discovery_parity.py` (and hook variant), `skills/harness-master/scripts/discovery/parity_check.py` (wrapper), all `tests/test_discovery_*.py`, `skills/harness-master/scripts/check.py`, references (coordinator-contract.md etc.), evals/evals.json, SKILL.md, AGENTS.md, docs generation surfaces, dist packaging, wagents validate flows.
- Update `discover_surfaces.py` / `invoke_surfaces.py` call patterns post-merge (direct or minimal subprocess for portable check parity).
- Ensure `uv run python skills/harness-master/scripts/discovery/check.py` (portable) and repo `scripts/check_discovery_parity.py` continue to pass.
- Delete `skills/discover-skills/` only after migration validation.
- `wagents openspec validate` + full test matrix pass for this change.

## Out Of Scope

- Merging or altering the standalone `skills/research/` skill (remains for general research outside harness gaps).
- Changes to `wagents/` core CLI, hook runner, sync, or registry authority (discovery continues to observe).
- Full superseding/archive of the prior `add-hook-discovery-parity` change (may be noted as historical; its delta is absorbed into the new skills-lifecycle text).
- Implementing journal v3 or new artifact formats beyond v2 compatibility already present.
- Non-harness surface or general agent capability discovery.
- Auto-migration of end-user journals on disk (document + optional helper only).
- Archiving this OpenSpec change before all validation matrix items pass (incl. openspec validate, discovery parity, harness-master check, pytest suite, and `wagents validate`).

## Affected Users And Tools

- Users invoking `/discover-skills` (or its modes) — will now use `/harness-master` with inferred discover intent (or explicit `discover` / `audit` etc. tokens).
- Orchestrator / subagent researchers relying on discover flow or GapReport + scout artifacts.
- Harness surface + usage consumers (unchanged or improved by unified control plane).
- `harness-master` and former `discover-skills` maintainers; parity and check authors.
- Generated docs consumers (`wagents docs generate`, SKILL index pages).
- Journal users (new location under `~/.agents/harness-master/discovery/`).

## Generated Surfaces To Refresh

- `skills/harness-master/SKILL.md` (dispatch table + inferred mode docs).
- `skills/harness-master/references/discovery/*` (coordinator-contract.md, scout-templates.md, gap-analysis.md via render, etc.).
- `docs/skills/harness-master.mdx` and related (via wagents docs generate).
- `dist/harness-master-*.skill.zip` (post-merge packaging).
- Any KB indexes, AGENTS.md cross-refs, external-skills.md notes.

## Risks

- Invocation breakage for anyone hardcoding `/discover-skills` — mitigated by clear migration notes in SKILL.md, AGENTS.md, and error redirects in any thin shim (if used briefly).
- Journal path change — old journals under prior harness discover-skills dirs must be discoverable or migrated; v2 journal-store will document fallback.
- Parity / portable check drift during transition — use the existing delegation wrapper pattern (`parity_check.py` calls repo `scripts/check_discovery_parity.py` when present) and update tests first.
- Test / evals volume — large discovery test surface; parallel lanes recommended in execution plan.
- OpenSpec validate during the window when spec text is updated but old discover-skills artifacts still referenced in archived changes (addressed by including delta + main update in this change).
- Hook parity (already shipped) must remain compatible; new paths under harness-master/scripts/discovery/hook_scan.py etc. must satisfy the (updated) lifecycle req.
