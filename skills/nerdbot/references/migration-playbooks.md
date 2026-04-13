# Migration Playbooks

## Default stance
Treat `migration` as the last resort. If an `imperfect repo` can be repaired by adding `raw`, `indexes`, `activity log`, `provenance`, and shared vault conventions around existing material, stop there.

Even explicit `/nerdbot migrate` requests start with a quick additive-repair triage. If a small in-place repair can satisfy the goal, stop there; otherwise continue into the migration interview without forcing a full repair workflow first.

## Decision gate: additive repair or migration?
| Situation | Safe default |
|-----------|--------------|
| Missing `indexes` or `activity log` | Add them in place |
| Mixed notes and source captures | Add a `raw/` intake area and map the current state |
| Existing markdown repo should become an Obsidian vault | Normalize metadata, link style, and shared `.obsidian/` surfaces before broad enrichment |
| New page structure is needed but old links still matter | Create companion pages and mapping pages before any move |
| Path stability no longer works and consumers must switch | Plan a staged `migration` with rollback |

## Risky migration interview
Answer or determine all of these before mutating paths:

1. What files are `canonical material` and must keep authority?
2. What paths are consumed by people, agents, or automation today?
3. What note names, aliases, `[[wikilinks]]`, embeds, and Dataview fields are already in use?
4. What can be regenerated, and what is irreplaceable?
5. What is allowed to move, rename, merge, or disappear?
6. What is the rollback plan if the new structure fails?

### Interview worksheet
| Path | Canonical material? | Current consumers | Allowed change | Rollback note |
|------|---------------------|-------------------|----------------|---------------|
| `wiki/topics/vendor-landscape.md` | yes | handbook links, agent prompts | annotate only | keep old path until new links are proven |

### Path mapping worksheet
| Old path or note name | New path or note name | Alias or mapping note? | Backlink status | Dataview/frontmatter impact |
|-----------------------|-----------------------|------------------------|-----------------|----------------------------|
| `wiki/topics/vendor-landscape.md` | `wiki/platform/vendor-landscape.md` | `aliases` + mapping page | pending | update `kind`, `updated`, and any path-sensitive fields |

If any answer is missing and clarification is unavailable, stop after the plan.

## Playbook 1 — Additive repair for an imperfect repo
Use this before any real `migration`.

### Steps
1. Add `indexes/source-map.md`, `indexes/coverage.md`, and `activity/log.md`.
2. Create a safe `raw/` intake area for future evidence.
3. Add or normalize shared `.obsidian/` surfaces that belong to the project, not the user session.
4. Map existing notes into `wiki` through links, companion pages, or summaries.
5. Normalize note metadata, aliases, and `[[wikilinks]]` before broad synthesis.
6. Backfill `provenance` on the highest-value pages.
7. Re-audit, using `scripts/kb_lint.py --root <path> --include-unlayered` when important markdown still sits outside the default layers.
8. Only escalate if the goal is still blocked.

### Review checkpoints
- [ ] No existing path was deleted or renamed.
- [ ] `canonical material` stayed authoritative.
- [ ] The repo is more legible without breaking consumers.
- [ ] The repo is closer to an Obsidian-native baseline before any deeper expansion or refinement.

## Playbook 2 — Re-root a KB without breaking paths
Use when the layered shape must move to a new root.

### Safe sequence
1. Create the new root beside the old one.
2. Mirror `.obsidian`, `raw`, `wiki`, `schema`, `config`, `indexes`, and `activity` in the new root.
3. Copy or summarize into the new root; do not remove the old root yet.
4. Add mapping pages, aliases, or notes so old paths still point to live content.
5. Update `indexes`, frontmatter aliases, and any path-sensitive vault config in both places while the cutover is in review.
6. Verify `provenance`, path consumers, backlinks, embeds, and rollback.
7. Cut over only after explicit approval.

### Rollback
- Keep the old root intact until the new root is proven.
- Keep a log entry that lists both old and new paths.
- Revert consumers first, then new content, if the cutover fails.
- Restore aliases or mapping pages before deleting any old note name.

## Playbook 3 — Split or merge wiki pages
Use when the `wiki` shape is too large or too mixed.

### Safe sequence
1. Create new companion pages.
2. Move only summaries or copied excerpts first; keep the old page as a stable landing point.
3. Add `Provenance` to the new pages before deprecating anything.
4. Update `indexes/source-map.md` and `indexes/coverage.md` for both old and new paths.
5. Add a clear note on the old page that points to the new pages.
6. Add `aliases` and update any affected embeds or block references.
7. Wait for review before any archival step.

### Example mapping row
| Old path | New path | Status | Notes |
|----------|----------|--------|-------|
| `wiki/topics/platform.md` | `wiki/topics/platform-overview.md` | parallel | old page remains canonical until approval |

## Playbook 4 — Obsidian vault migration
Use when a markdown repo should become an Obsidian-native vault before broader work.

### Safe sequence
1. Run inventory and classify the repo as `legacy_markdown_repo`, `mixed_vault`, or `obsidian_native_vault`.
2. Add project-safe `.obsidian/` shared surfaces and `config/obsidian-vault.md`.
3. Normalize frontmatter on high-value notes first.
4. Normalize note names, `aliases`, and `[[wikilinks]]` in small batches.
5. Move or re-root notes only after aliases, mapping pages, and path-map rows exist.
6. Re-run vault-aware lint after each batch.
7. Expand or refine only after the vault baseline is stable.

### Stop conditions
- Broken `[[wikilinks]]` remain unresolved.
- Alias collisions are unresolved.
- Dataview or frontmatter drift would make the repo less navigable than before.
- Shared `.obsidian/` surfaces are mixed with volatile workspace files.

## Playbook 5 — Derived output cutover
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
- Unresolved `[[wikilinks]]`, embeds, or aliases would break navigation during the move.
- Frontmatter drift would invalidate Dataview or vault-level expectations.
- `schema` or `config` changes are bundled into the same risky batch.
- Rollback is vague or untested.

## Migration exit checklist
- [ ] Additive repair was considered first.
- [ ] The interview is complete.
- [ ] Rollback is concrete and reviewable.
- [ ] `indexes` and `activity log` changes are staged with the move.
- [ ] Path mapping, aliases, and backlink preservation were reviewed for vault moves.
- [ ] No destructive cutover happens without explicit approval.
