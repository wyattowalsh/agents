# Design

## Approach

Treat hooks as a first-class discovery dimension parallel to `mcp` and `plugins`:

- Extract hook-specific surface definitions into a portable `config/hook-surface-registry.json` (with corresponding schema under `config/schemas/`). This decouples the concrete paths (`.codex/hooks.json`, `.cursor/hooks.json`, Copilot `.github/hooks/*`, global variants) from the monolithic `PROJECT_SURFACES`/`GLOBAL_SURFACES` dicts in `skills/harness-master/scripts/discover_surfaces.py`, reducing future merge friction and allowing `hook_scan` / `hook-scout` to operate on a focused registry slice.
- Add `hook_scan.py` that produces a `hook-scan.json` artifact. It follows the inventory_scan delegation pattern: pure stdlib + subprocess call (no `import wagents` anywhere in discover-skills tree). Collection logic for registry + frontmatter-derived + embedded hooks lives in a local `scripts/_hook_collect.py` (stdlib reimplementation or thin wrapper that can later be shared) or delegated subprocess to a harness-master / skill-router hook collector if introduced.
- Extend `GapReport` (schemas.py dataclass + public_dict), `gap_engine.py` (merge_asset_sections, build), `gap-report.schema.json`, and `validate_gap_report` (or new dedicated) to include a `hooks` top-level object (shape: registry presence, coverage per harness, blind spots, semantic vs file-presence delta, etc.).
- `hook-scout` (already allocated as W2-HK-00 in coordinator.py) remains deliberately report-only: its scout artifact contains `candidates: []` (plus any audit notes / gaps surfaced from the W0 hook-scan.json). No path through `merge_artifacts.py` for hooks at this time (hooks are not "installed skills").
- Update SCOUT_ROLES, DEFAULT_TIMEOUTS (already partially present), validate_wave_manifest, and coordinator planning/verification to accept `hook-scout`.
- W0 pipeline (coordinator-contract.md) gains the explicit `hook_scan.py` line before gap_engine.
- Parity guard (scripts/check_discovery_parity.py and/or discover-skills parity_check) extended for hook surfaces / registry counts.
- discover_surfaces.py continues to emit `kind: "hooks"` rows for harness file surfaces (Grok Build etc. still see them); hook_scan owns the semantic registry view.

No wagents imports are permitted under `skills/discover-skills/` (enforced by existing `tests/test_skills_no_wagents.py`).

## Data And Control Flow

W0 (deterministic, from repo root):

```bash
python skills/discover-skills/scripts/inventory_scan.py ...
python skills/discover-skills/scripts/mcp_scan.py ...
python skills/discover-skills/scripts/plugin_scan.py ...
python skills/discover-skills/scripts/invoke_surfaces.py ...   # still reports hook file kinds
python skills/discover-skills/scripts/hook_scan.py --repo-root . -o artifacts/<sid>/wave0/hook-scan.json
python skills/discover-skills/scripts/gap_engine.py \
  ... --harness ... --hooks artifacts/<sid>/wave0/hook-scan.json \
  -o artifacts/<sid>/wave0/gap-report.json
...
```

GapReport shape gains:

```json
{
  ...
  "hooks": {
    "version": 1,
    "registry_hooks": 22,
    "harness_coverage": { "codex": [...], "claude-code": [...], ... },
    "file_surfaces_present": 5,
    "blind_spots": ["frontmatter-only-in-external-skills", "grok-plannotator-hooks"],
    "gaps": ["no semantic hook for PostToolUse on new harness X"]
  },
  ...
}
```

Wave 2 planning (coordinator) already emits the hook-scout task when wave==2. Scout produces standard scout-artifact wrapping the analysis of hook-scan.json + gap input; status success/skipped with empty candidates for report-only posture.

Hook surface registry (planned shape sketch):

```json
{
  "version": 1,
  "project_hooks": {
    "codex": [ { "label": "project hooks", "path": ".codex/hooks.json", "role": "authoritative" } ],
    ...
  },
  "global_hooks": { ... }
}
```

`hook_scan.py` can consume both the semantic `config/hook-registry.json` and (optionally) the surface registry for presence checks, emitting the scan artifact for gap + scout.

## Integration Points

- `skills/discover-skills/scripts/gap_engine.py`: accept `--hooks`, pass through merge, include in GapReport.
- `skills/discover-skills/scripts/schemas.py`: add `validate_hook_scan`, extend GapReport, add "hook-scout" to SCOUT_ROLES, ensure _validate_with_schema("hook-scan").
- `skills/discover-skills/data/schemas/gap-report.schema.json`: add "hooks": {"type":"object"} (additionalProperties true for now).
- `skills/discover-skills/data/schemas/hook-scan.schema.json`: new (will be created by impl).
- `skills/discover-skills/references/coordinator-contract.md`: add hook_scan.py to the W0 bash block.
- `skills/discover-skills/scripts/validate_session.py`: route hook-scan.json validation.
- `skills/harness-master/scripts/discover_surfaces.py`: (planned) load hook surfaces from extracted registry instead of only inline dicts (or at minimum keep in sync during extraction).
- `scripts/check_discovery_parity.py`: add hook parity assertion (registry vs scan counts or surface coverage).
- `skills/discover-skills/scripts/parity_check.py`: delegate wrapper if needed.
- `skills/discover-skills/SKILL.md`, evals, tests/test_*.py under discover, references/*.
- OpenSpec change + skills-lifecycle/spec.md (this work).

## Alternatives Rejected

- Treating hooks only as harness surfaces (status quo) — rejected by user for "full parity" requirement.
- Importing wagents hooks collection directly into hook_scan — violates the "no wagents imports in discover-skills" boundary and portable check contract.
- Full hook candidate generation + install path in Wave 2 — out of scope; hooks live in registry + sync, not the npx skills add model.
- Renaming hook-scout to harness-hook-scout — would duplicate harness-scout; separate semantic slice is cleaner.

## Migration Or Compatibility Notes

- Existing gap-report.json payloads without "hooks" remain loadable (gap_engine merge defaults it).
- v1 journals + artifacts continue to work; new runs will include hook-scan.json and hooks in gap.
- discover_surfaces output shape unchanged for downstream harness consumers.
- Hook registry (`config/hook-registry.json`) and its schema stay the source of truth for managed hooks; discover observes it.
