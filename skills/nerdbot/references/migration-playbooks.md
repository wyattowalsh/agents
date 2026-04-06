# Migration Playbooks

## Default stance
Treat `migration` as the last resort. If an `imperfect repo` can be repaired by adding `raw`, `indexes`, `activity log`, and `provenance` around existing material, stop there.

## Decision gate: additive repair or migration?
| Situation | Safe default |
|-----------|--------------|
| Missing `indexes` or `activity log` | Add them in place |
| Mixed notes and source captures | Add a `raw/` intake area and map the current state |
| New page structure is needed but old links still matter | Create companion pages and mapping pages before any move |
| Path stability no longer works and consumers must switch | Plan a staged `migration` with rollback |

## Risky migration interview
Answer or determine all of these before mutating paths:

1. What files are `canonical material` and must keep authority?
2. What paths are consumed by people, agents, or automation today?
3. What can be regenerated, and what is irreplaceable?
4. What is allowed to move, rename, merge, or disappear?
5. What is the rollback plan if the new structure fails?

### Interview worksheet
| Path | Canonical material? | Current consumers | Allowed change | Rollback note |
|------|---------------------|-------------------|----------------|---------------|
| `wiki/topics/vendor-landscape.md` | yes | handbook links, agent prompts | annotate only | keep old path until new links are proven |

If any answer is missing and clarification is unavailable, stop after the plan.

## Playbook 1 — Additive repair for an imperfect repo
Use this before any real `migration`.

### Steps
1. Add `indexes/source-map.md`, `indexes/coverage.md`, and `activity/log.md`.
2. Create a safe `raw/` intake area for future evidence.
3. Map existing notes into `wiki` through links, companion pages, or summaries.
4. Backfill `provenance` on the highest-value pages.
5. Re-audit. Only escalate if the goal is still blocked.

### Review checkpoints
- [ ] No existing path was deleted or renamed.
- [ ] `canonical material` stayed authoritative.
- [ ] The repo is more legible without breaking consumers.

## Playbook 2 — Re-root a KB without breaking paths
Use when the layered shape must move to a new root.

### Safe sequence
1. Create the new root beside the old one.
2. Mirror `raw`, `wiki`, `schema`, `config`, `indexes`, and `activity` in the new root.
3. Copy or summarize into the new root; do not remove the old root yet.
4. Add mapping pages, aliases, or notes so old paths still point to live content.
5. Update `indexes` in both places while the cutover is in review.
6. Verify `provenance`, path consumers, and rollback.
7. Cut over only after explicit approval.

### Rollback
- Keep the old root intact until the new root is proven.
- Keep a log entry that lists both old and new paths.
- Revert consumers first, then new content, if the cutover fails.

## Playbook 3 — Split or merge wiki pages
Use when the `wiki` shape is too large or too mixed.

### Safe sequence
1. Create new companion pages.
2. Move only summaries or copied excerpts first; keep the old page as a stable landing point.
3. Add `Provenance` to the new pages before deprecating anything.
4. Update `indexes/source-map.md` and `indexes/coverage.md` for both old and new paths.
5. Add a clear note on the old page that points to the new pages.
6. Wait for review before any archival step.

### Example mapping row
| Old path | New path | Status | Notes |
|----------|----------|--------|-------|
| `wiki/topics/platform.md` | `wiki/topics/platform-overview.md` | parallel | old page remains canonical until approval |

## Playbook 4 — Derived output cutover
Use when `derived output` paths or formats need to change.

### Safe sequence
1. Generate the new `derived output` in a versioned or parallel location.
2. Compare it against the previous output.
3. Update any `config` only after the new output is verified.
4. Log the recipe, inputs, and rollback path in the `activity log`.
5. Retain the previous export until downstream consumers confirm the change.

## Stop conditions
Halt and return a plan only if:
- `canonical material` is not fully identified.
- Current consumers are unknown.
- The proposed move would break `provenance` temporarily.
- `schema` or `config` changes are bundled into the same risky batch.
- Rollback is vague or untested.

## Migration exit checklist
- [ ] Additive repair was considered first.
- [ ] The interview is complete.
- [ ] Rollback is concrete and reviewable.
- [ ] `indexes` and `activity log` changes are staged with the move.
- [ ] No destructive cutover happens without explicit approval.
