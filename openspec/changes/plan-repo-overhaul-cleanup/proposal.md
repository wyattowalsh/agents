# Proposal

## Problem

The repository is not short of features. It is carrying three kinds of weight at once, and one of them breaks current Cursor work.

Measured on `main` at commit `afd5f8ff` (2026-11-17):

- **50 active OpenSpec changes** and 54 archived ones. 17 active changes have every `tasks.md` box checked and are still open. 11 active changes have a proposal and no `tasks.md`. A June 2026 cleanup (RV-RC-006) deferred archival until an owner confirmed each change, so finished work never leaves the active set.
- **Tracked bulk.** 8,654 tracked files. `docs/` is 71.7 MB and `planning/` is 56.0 MB. The single largest file is `docs/src/generated-skill-indexes.mjs` (22.2 MB, 398,585 lines). The catalog browser does not import it. `CatalogBrowser.astro` reads `skills-catalog-browser-index.json`, and `tests/test_docs.py` asserts catalog pages do not mention `generated-skill-indexes.mjs`.
- **Split contracts.** `openspec/specs/cursor-harness/spec.md` and `wagents/platforms/cursor.py` (`CURSOR_DEFAULT_MODEL`) say `cursor-grok-4.6-xhigh`. `wagents/hooks/policies/cursor_task_model_pin.py`, `.cursor/rules/cursor-models.mdc`, and `.cursor/agents/*.md` still force `cursor-grok-4.5-high`. This environment rejects `cursor-grok-4.5-high`. The Task hook rewrites every launch to that dead slug, so subagents cannot start. There is no separate "500k" model slug. The live extra-high Grok 4.7 slug is `grok-4.7-xhigh`. `cursor-grok-4.6-xhigh` is also still accepted.
- **A false source of truth for skills.** `AGENTS.md` says harness-only skill keys live in `config/skill-adapters.json`. That file does not exist. Almost every `skills/*/SKILL.md` still carries `argument-hint`, `model`, or `user-invocable`.
- **Generator path drift.** `wagents/docs.py` `write_site_data()` writes `docs/lib/generated-*.mjs`. `docs/lib` does not exist. Astro imports `docs/src/generated-site-data.mjs`. The next generate will not update the files the site loads.

June's cleanup ledger (`planning/manifests/repo-cleanup-review-findings.md`) is historical. Its fixed rows stay fixed. It is not the backlog.

## Intent

Publish one sequenced plan that says what to archive, what to delete, what to tighten, and what to leave alone. Later waves implement it. This change does not perform the overhaul.

Recommended order:

1. **P0 — Make Task launches work.** One model constant, set to `grok-4.7-xhigh`, written through the existing `cursor-grok-high-pin` change. Update the spec, the hook, `cursor.py`, the rule, and `.cursor/agents/` together. Do not open a second pin change.
2. **P0 — Repair the docs writer path** so generate updates `docs/src/`, which Astro already imports. Do this before any attempt to delete generated files.
3. **P1 — Archive finished OpenSpec changes** after a short spot-check. Finish one-box leftovers, then archive those too. Give each proposal-only change a `tasks.md` or archive it as not started.
4. **P1 — Stop shipping the unused 22.2 MB skill-index module** after an import search and a docs check confirm the catalog still builds from the JSON indexes.
5. **P2 — Tell the truth in contracts** (`AGENTS.md` vs missing `skill-adapters.json`; instruction projections vs `instructions/global.md`). Do not strip skill frontmatter in this program.
6. **P2 — Finish the already-scoped product changes** that are mid-flight (Things++, hook promotion, harness retirement, token efficacy, RV skill/docs contracts). Do not fold them into this plan.
7. **P3 — Collapse thin `skill-*` report skills** only after catalog URLs have a redirect story. Keep `skill-creator` and `skill-router`.

## Scope

- This OpenSpec change: the plan documents only.
- Later implementation is sequenced in `tasks.md` and is not part of landing this change.
- The plan covers OpenSpec lifecycle, generated-artifact weight, the Cursor model pin, docs writer paths, skill/agent contract honesty, and explicit non-goals.

## Out Of Scope

- Implementing waves 0–4 here.
- Rewriting git history. Deletes are forward commits. No file in this audit is a secret that would justify a rewrite.
- Deleting `planning/manifests/candidate-corpus-jul2026/`. `tests/test_candidate_corpus.py` and `tests/test_candidate_receipts.py` read those manifests, including `promotion-overrides.json` and `runtime-activation-receipts.json`. Archiving the finished intake change does not delete the corpus.
- Deleting `docs/public/generated-registries/skills-catalog-index.json` (14.6 MB). `config/docs-artifact-registry.json` requires `uv run wagents catalog index --check` for that path.
- Stripping `argument-hint` / `model` / `user-invocable` from skill frontmatter before an adapter file exists.
- Merging the four `fleet-hooks-*` changes into one change.
- A second token-trim program. `token-efficacy-program` (2/31 tasks) already owns standing-context cuts.
- Reverting the ChatGPT exporter or Things++ work landed in `afd5f8ff` and the commits under it.
- Live `wagents skills sync --apply`, plugin installs, or home-directory writes (`~/.cursor/cli-config.json`, `state.vscdb`).
- Weakening fail-closed security hooks.
- New Starlight plugins. `config/docs-artifact-registry.json` already records why each extra plugin is blocked.
- Treating "500k" as a Task model slug. It is not in the catalog.

## Affected Users And Tools

- Maintainers running Cursor Task/subagents (broken pin).
- Anyone reading `openspec/changes/` as the live backlog.
- Docs site and catalog checks (`wagents docs`, `wagents catalog index`).
- Contributors who follow `AGENTS.md` skill frontmatter rules and cannot find `skill-adapters.json`.

## Generated Surfaces To Refresh

None in this change. Later waves that edit registries or skill/agent sources must refresh the surfaces named in `config/docs-artifact-registry.json` (`wagents readme`, `wagents docs generate --no-installed --check`, `wagents catalog index --check`). Do not hand-edit those outputs.

## Risks

| Risk | Mitigation |
| --- | --- |
| Archiving a change whose boxes are checked but whose behavior is absent | Spot-check one observable claim from `proposal.md` before `openspec archive`. Reopen instead of archiving on failure. `replace-package-version-check-mcp` is 12/12 while `config/mcp-registry.json` still has that server id. |
| Deleting the 22.2 MB module while a generator or test still expects the path | Wave 2 deletes only after the writer path is fixed and `rg` plus `wagents docs generate --check` show no runtime import. `tests/test_docs.py` currently asserts the catalog page does **not** name the module. |
| Pin move to `grok-4.7-xhigh` surprises people still on the 4.6 spec | One constant, one spec scenario, tests that grep for the old slug. Alternative, if the maintainer rejects 4.7: set that same constant to `cursor-grok-4.6-xhigh` so it matches today's spec and `cursor.py`. Either choice is valid. Leaving `cursor-grok-4.5-high` in the hook is not. |
| Corpus tests break if evidence JSON is "cleaned up" | Corpus files are out of scope for deletion. |
| Instruction dedup fights `sync_agent_stack.py` | Diff first. Delete a projection only when the sync writer regenerates it. |
