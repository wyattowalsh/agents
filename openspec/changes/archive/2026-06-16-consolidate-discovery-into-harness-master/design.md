# Design

## Approach

Consolidate by **full merge + delete** (no long-lived bridge):

- Authoritative discovery implementation moves under `skills/harness-master/`:
  - Scripts: `skills/harness-master/scripts/discovery/` (inventory_scan.py, mcp_scan.py, plugin_scan.py, invoke_surfaces.py, hook_scan.py, _hook_collect.py, gap_engine.py, coordinator.py, validate_session.py, merge_artifacts.py, journal-store.py, schemas.py, _paths.py, parity_check.py, check.py, render_gap_reference.py, npx_skills.py, etc.).
  - Data: `skills/harness-master/data/discovery/` (discovery-taxonomy.json, agent-targets.json, schemas/*.schema.json, fixtures/).
  - References (discovery-specific): `skills/harness-master/references/discovery/` (coordinator-contract.md, scout-templates.md, gap-analysis.md, research-integration.md, output-formats.md, team-templates.md, etc.).
  - Evals (harness-bounded discovery cases): co-located under harness-master/evals/ (or data/discovery/evals/ if preferred for packaging); keep general evals separate.
- `skills/harness-master/scripts/discover_surfaces.py`, `usage_probe.py`, `candidate_score.py`, `source_probe.py`, `install_skills.py` etc. remain at `scripts/` (or are harmonized); discovery pipeline now shares the same package.
- Delete `skills/discover-skills/` (including its SKILL.md, evals/evals.json remnants, empty data/refs/scripts after migration).
- **Inferred modes** in harness-master dispatch:
  - Extend the existing dispatch table (intake/audit/apply/research/candidate/compare/usage/sources/install) to recognize and route discovery intents.
  - Mode inference (no explicit `mode:` required): natural language + keywords (`discover`, `audit`, `research <focus>`, `ideate`, `resume`, `list`, `install <owner/repo@skill>`) plus auto-heuristics from prior discover-skills SKILL.md.
  - Empty args or "discover" still triggers full pipeline (W0 scans → gap → plan waves → scouts → ideate/report).
  - Preserve safety: discovery/audit/gap paths are read-only; only `apply approved` mutates.
- Journal path: `~/.agents/harness-master/discovery/` (session dirs with `journal.json`, `wave0/`, `waveN/`, artifacts). `journal-store.py` updated to default + resolve under harness-master namespace. v1 journals under legacy `discover-skills` paths remain loadable via compatibility layer (documented fallback + one-time copy note).
- Subprocess delegation pattern preserved where needed for "portable skill tree" checks (`check.py` + `parity_check.py` wrappers delegate to repo `scripts/check_discovery_parity.py` when the in-tree relative path would break). After merge, in-harness calls can be direct imports within harness-master (still no `wagents` imports inside the discovery scripts themselves).
- `invoke_surfaces.py` (now under discovery/) can call `discover_surfaces.py` via relative import or thin subprocess for portable parity; the old cross-skill subprocess is no longer required.
- `test_skills_no_wagents.py` is updated (or its globs) to assert under `skills/harness-master/scripts/discovery/` and `scripts/` (where applicable). The boundary rule is unchanged: discovery code uses stdlib + subprocess delegation for external collectors (e.g. skill-router, wagents where intentionally observed).
- GapReport, schemas, SCOUT_ROLES, hook-scout etc. (from prior hook parity) continue to work; paths in contracts/docs updated.
- Repo-root `config/` registries (`hook-registry.json`, `hook-surface-registry.json`, `harness-surface-registry.json`, etc.) remain SSOT; discovery reads them (as before).
- Standalone `skills/research/` is untouched and continues to own general (non-harness-gap) research flows.

No wagents imports are permitted in the discovery script tree under harness-master (enforced by test + portable check).

## Data And Control Flow

W0 (deterministic, from repo root, now invoked via harness-master discovery):

```bash
python skills/harness-master/scripts/discovery/inventory_scan.py --repo-root . -o artifacts/<sid>/wave0/inventory.json
python skills/harness-master/scripts/discovery/mcp_scan.py --repo-root . -o artifacts/<sid>/wave0/mcp.json
python skills/harness-master/scripts/discovery/plugin_scan.py --repo-root . -o artifacts/<sid>/wave0/plugins.json
python skills/harness-master/scripts/discovery/invoke_surfaces.py --repo-root . -o artifacts/<sid>/wave0/surfaces.json
python skills/harness-master/scripts/discovery/hook_scan.py --repo-root . -o artifacts/<sid>/wave0/hook-scan.json
python skills/harness-master/scripts/discovery/gap_engine.py \
  --taxonomy skills/harness-master/data/discovery/discovery-taxonomy.json \
  --inventory ... --mcp ... --plugins ... --harness ... --hooks ... \
  -o artifacts/<sid>/wave0/gap-report.json
python skills/harness-master/scripts/discovery/validate_session.py artifacts/<sid>/wave0/gap-report.json
python skills/harness-master/scripts/discovery/parity_check.py
```

`coordinator.py` (under discovery/) consumes the gap and emits wave manifests (W2+ scouts including harness-scout + hook-scout etc.). `merge_artifacts.py` folds resolved scouts back.

Journal init (v2):

```python
# under harness-master/scripts/discovery/journal-store.py
init_journal(sid, artifact_root=Path.home()/".agents/harness-master/discovery"/sid )
```

Inferred mode dispatch example (high level in harness-master/SKILL.md and implementation entry):

- `harness-master discover` or natural "find missing skills / audit my skills / research ecosystem for X" → run full W0 + coordinator + scout orchestration (read-only).
- `harness-master audit <scope>` → W0 + gap only.
- `harness-master research <harness|all> <mcp|skill|...>` → source plan + scouts (inside discover flow) or unified research lane.
- `harness-master ideate` → from prior gap context.
- `harness-master resume <N>` , `list`, `install <candidate>` → journal + apply paths.

GapReport and scout artifacts unchanged in shape (hooks section etc. from prior work).

## Integration Points

- `skills/harness-master/SKILL.md`: new dispatch rows + inference logic + vocabulary merge (gap, coordinator, journal now under harness-master); update NOT FOR and cross-refs.
- `skills/harness-master/scripts/discovery/*` (the moved + adapted modules): path constants via `_paths.py`, relative imports for in-skill surfaces, subprocess only for portable boundaries.
- `skills/harness-master/scripts/discover_surfaces.py`, `usage_probe.py` etc.: now peer; may be invoked directly from discovery scripts.
- `scripts/check_discovery_parity.py` + `scripts/check_hook_discovery_parity.py`: primary repo parity; update any hardcoded discover-skills paths.
- `skills/harness-master/scripts/discovery/parity_check.py`: thin wrapper delegating to repo script (portable check support).
- `skills/harness-master/scripts/check.py` (top-level + discovery/): portable entry that exercises validate + evals + parity + packaging dry-run.
- `tests/test_discovery_*.py` + `tests/test_skills_no_wagents.py` + distribution tests: retarget imports/paths; add delete-guard or post-delete assertions if needed.
- `skills/harness-master/references/discovery/coordinator-contract.md`, `scout-templates.md`, `gap-analysis.md` (regenerated), `research-*.md`: update paths + W0 examples + journal layout.
- `skills/harness-master/evals/evals.json`: absorb relevant cases from prior discover-skills evals; keep harness-bounded.
- `openspec/specs/skills-lifecycle/spec.md` + this change's delta: new requirement text for harness-master discovery submodule.
- `wagents` docs generation, packaging, `dist/`, `AGENTS.md`, KB indexes: refresh after moves.
- Journal consumers (orchestrator, resume logic, `wagents` if any): use new `~/.agents/harness-master/discovery/` default.
- Prior hook parity surfaces (hook_scan etc.): continue to satisfy updated spec under new paths.

## Alternatives Rejected

- Keep `discover-skills` as thin delegating skill / long-term bridge — rejected: user intent is full merge into harness-master control plane; bridge increases complexity.
- Only move scripts, leave separate SKILL.md + evals — rejected: defeats "inferred modes" and single-skill story.
- Change journal to `~/.agents/discovery/` (top level) — rejected: namespace under the owning skill (harness-master) is consistent with harness-specific state.
- Require all scans to stay pure subprocess even inside harness-master — rejected for maintainability; direct calls allowed within the skill tree as long as no wagents imports and portable check wrappers are preserved for copied-skill scenarios.
- Supersede/archive hook-parity change in same step — out of scope; keep historical OpenSpec records intact.

## Migration Or Compatibility Notes

- Invocation: `/discover-skills ...` → recommend `/harness-master discover ...` (or natural language); any thin redirect shim is temporary and not committed long-term.
- Journals: v2 journal-store will attempt legacy discovery paths as fallback for resume/list; new sessions always use harness-master path. Document one-time copy in references.
- Artifacts / sessions: `<sid>` layout (wave0/gap-report.json etc.) unchanged; only parent dir moves.
- Gap / scout artifacts produced by prior discover runs remain valid (schemas stable).
- `wagents validate` and openspec must pass with the updated spec (old discover-skills references live only in archived change history).
- Packaging: harness-master skill zip grows to include the discovery surface; discover-skills zip is removed.
- Tests: discovery suite runs against harness-master paths; no-wagents boundary test updated.
