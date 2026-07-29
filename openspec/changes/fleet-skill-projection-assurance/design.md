# Design: Fleet Skill Projection Assurance

## Approach

Sibling-extend `reconcile-harness-plugins-skills`: keep its terminal dispositions,
redaction, and stop rules. Add an explicit **store vs projection** presence model,
Cursor authoritative-link ensure (skills-sync apply post-step, not stack
`sync_home`), sync planner buckets, and reconciliation keys that cannot false-pass
on store-only Cursor coverage.

Wave 0 freezes contracts only. Waves 1a/1b own production modules per the file
ownership matrix in the fleet plan.

## Scout Findings (Wave 0 RO)

### Ownership / harness surfaces (W0-R1)

| Surface | Tier today | Implication |
| --- | --- | --- |
| `~/.agents/skills` | Skills CLI canonical store; Cursor lists as secondary in harness-surfaces | Store presence ≠ Cursor durable sync |
| `~/.cursor/skills` | Authoritative when present (global) | Required for Cursor `projection_present` |
| `.cursor/skills/**` / `.cursor/skills/repo` | Project authoritative | Never satisfies global sync |
| Codex plugin / OpenCode `skills.paths` | Preferred non-CLI owners | Stay `already_present`; do not force harness-dir fills |
| Ownership MDX | One exposure owner; dry-run before apply | Align; document secondary/store ≠ durable synced in later docs wave |

### Inventory false-pass / hash hotspots (W0-R2)

- `_merge_local_skill_roots_into_query` documents that disk-visible coverage is
  not proof the harness runtime loaded the skill; Cursor still lands in
  `installed_agents` from store/secondary roots → sync planner `already_present`.
- Cleanup path hashes every exposure via `_file_hash` + `_tree_hash` in
  `_iter_skill_exposures` / `collect_skill_cleanup_exposures` — OOM risk on large
  fleets (exit 137 observed). Contract: lazy hash only names with ≥2 exposures;
  SKILL.md first; full tree only on mismatch.

### Sync planner seams (W0-R3)

- `_build_sync_report` in `wagents/cli.py`: `agent_id in sync_row_installed_agents`
  OR `_repo_skill_covered_by_non_cli_owner` → `already_present`; else `missing`.
- No `projection_ensure` / `projection_blocked` / `store_missing` buckets yet.
- Apply path runs Skills CLI batches only; Grok mirror exists as post-step pattern
  to copy for Cursor ensure **after** CLI batches.
- Preserve pin gate, unresolved, skipped, plugin/direct-path skips.

### Reconcile sibling (W0-R4)

- Decision: **sibling extend**, not rewrite. Add
  `store_missing_by_agent` + `projection_missing_by_agent` beside existing
  `default_sync_missing_by_agent`. Baseline reset expected; do not claim July
  packet still green after keys land.
- Ensure stays out of stack `sync_home`; stays skills-sync apply post-step.

## Frozen Contracts

### 1. Presence model

```text
coverage_class:
  store_present          — body under ~/.agents/skills/<name> with readable SKILL.md
  projection_present     — harness authoritative root has dir or same-realpath link
  preferred_non_cli      — plugin / direct-repo-path / bundle owner covers agent
  secondary_only         — store or compat root only (legacy: store-without-projection)
  missing                — neither store nor preferred owner

sync buckets (per agent, per desired skill):
  already_present        — preferred_non_cli OR (store_present AND projection_present*)
  projection_ensure      — store_present AND NOT projection_present AND safe to link
  projection_blocked     — conflict (divergent-body, real dir, wrong target, loop)
  store_missing          — no store body → Skills CLI install command
  internal_projection    — metadata.internal: link-from-store only, never CLI
  skipped                — pin/quarantine/supersession/owner suppress
```

\* Cursor: projection root = `~/.cursor/skills` (global). Project
`.cursor/skills/**` never counts for global sync.

\* Universal peers (Codex/OpenCode): default projection requirement OFF unless
harness-surfaces + ownership say otherwise; still report `secondary_only` counts.

### 2. `ensure_cursor_authoritative_links` API

Location: `wagents/platforms/cursor.py` (Wave 1a exclusive). Leave
`_sync_skill_symlinks` (repo project projection) untouched.

```python
def ensure_cursor_authoritative_links(
    *,
    names: Sequence[str],
    home: Path | None = None,
    store_root: Path | None = None,       # default: home / ".agents" / "skills"
    projection_root: Path | None = None,  # default: home / ".cursor" / "skills"
    dry_run: bool = True,
) -> CursorAuthoritativeLinksReport:
    """Additive same-realpath projection ensure for global Cursor skills.

    Never replaces real directories or divergent bodies. Never rm -r trees.
    Broken / wrong-target symlinks may be replaced when store body is valid.
    """
```

Report shape (frozen fields):

| Field | Meaning |
| --- | --- |
| `created` | names where a new symlink would be / was created |
| `repaired` | broken or wrong-target symlink replaced |
| `already_correct` | same-realpath link or same-body real dir |
| `blocked` | list of `{name, reason}` conflict entries |
| `skipped_missing_store` | no readable store `SKILL.md` |

### 3. Conflict / safety rules

| Situation | Action |
| --- | --- |
| Missing `~/.cursor/skills/<name>`, store OK | Create symlink → store realpath |
| Broken symlink at projection root, store OK | Replace symlink only |
| Symlink to wrong target, store OK | Replace symlink only |
| Real directory, same-body as store | `already_present` / preserve |
| Real directory, divergent-body | `projection_blocked` / manual-review — never overwrite |
| Dangling store / missing SKILL.md | Do not link; store gap or blocked |
| Project `.cursor/skills/repo/*` | Out of scope for home ensure |
| `metadata.internal` | Projection ensure from store; never `npx skills add` |
| Upstream CLI destructive repair | Fleet ensure never `rm -r` real trees |

### 4. Reconciliation keys

Under skills summary (alongside existing fields):

| Key | Meaning |
| --- | --- |
| `store_missing_by_agent` | desired skills lacking canonical store body per agent |
| `projection_missing_by_agent` | store present (or N/A) but authoritative projection absent where required |

“Fully reconciled” for Cursor desired set requires `projection_missing` → 0 after
approved ensure, not merely `default_sync_missing` → 0.

### 5. Hard stop (this change’s evidence path)

- SHALL NOT run `wagents skills sync --apply`
- SHALL NOT run live `npx skills add`
- SHALL NOT perform mass home symlink writes
- SHALL NOT run cleanup `--apply`
- Live apply only after Wave 2 + explicit human approval

### 6. Performance contracts (implement Wave 1a; freeze now)

1. Lazy cleanup hashing — hash only names with ≥2 exposures; SKILL.md first;
   full tree only on mismatch.
2. Compact sync JSON default — counts + samples; full name lists behind
   `--verbose` or JSONL.
3. Projection ensure — O(1) lstat/readlink; skip-if-correct; no content hash on
   happy path.
4. Keep Skills CLI source-grouped batches; no one-process-per-skill.

## Data And Control Flow

```text
catalog desired set
        │
        ▼
 Skills CLI (mutator for net-new store)
        │
        ▼
 ~/.agents/skills/<name>     ← store_present
        │
        ├── projection ensure (Cursor first; additive)
        │      → ~/.cursor/skills/<name>
        ├── report tiers (Codex/OpenCode/Crush; require OFF by default)
        └── preferred_non_cli short-circuit (plugin / skills.paths)
```

Apply order when eventually approved: Skills CLI batches →
`ensure_cursor_authoritative_links(dry_run=False)` for `projection_ensure` +
`internal_projection` names → optional future Crush/OpenCode policy (Phase D).

## Integration Points

| Module | Owner wave | Change |
| --- | --- | --- |
| `wagents/skill_coverage.py` (new) | W1-INV | Shared root→tier map + presence helpers |
| `wagents/installed_inventory.py` | W1-INV | Per-root presence; lazy cleanup hash |
| `wagents/platforms/cursor.py` | W1-CUR | `ensure_cursor_authoritative_links` |
| `wagents/cli.py` | W1-SYNC | Planner buckets; ensure after CLI on apply |
| `scripts/generate_harness_reconciliation.py` | W1-RECON | New recon keys |
| Hand docs | W1-DOCS | Ownership + surfaces: store ≠ durable sync |

## Alternatives Rejected

| Alternative | Why rejected |
| --- | --- |
| Treat secondary-alone as the whole bug | Underspecifies store vs projection |
| Put ensure in stack `sync_home` | Wrong lifecycle; Grok-mirror pattern belongs on skills-sync apply |
| Force `~/.codex/skills` for all universal peers | Regresses plugin / `skills.paths` one-owner policy |
| Invent Grok-style alternate install owner for Cursor | Skills CLI remains mutator; fleet owns projection only |
| Destructive upstream-style `rm` real dirs | Violates additive-only fleet policy |

## Migration Or Compatibility Notes

- Existing `already_present` / `missing` report keys remain during transition;
  new buckets are additive. Compact JSON may hide full lists unless verbose.
- Recon baseline reset after new keys: expect Cursor `projection_missing` ≫ 0
  until human apply gate.
- `reconcile-harness-plugins-skills` stop rules remain in force for this change’s
  evidence path.
