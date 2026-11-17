# Proposal

> Cleanup is finished. `wagents` imports, docs write to `docs/src`, the Cursor pin is `grok-4.7-xhigh`, the unused 22 MB index and planning scratch are gone, and 24 finished changes are archived. Do not continue this as a program. The problem statement below is the record of what we started from. What remains is normal product work, listed in `tasks.md`.

## Problem

The repository is not short of features. It is carrying three kinds of weight at once, and one of them breaks current Cursor work.

Measured on `main` at commit `afd5f8ff` (2026-11-17):

- **50 active OpenSpec changes** and 54 archived ones. A first pass only counted tasks that start with `- [x]`, so it missed finished changes whose boxes are numbered (`1. [x]`) and it treated `integrate-ideas-backlog` as done even though that file has 127 `[x]`, 1 open box, and 20 `[~]` deferrals. A June 2026 cleanup (RV-RC-006) deferred archival until an owner confirmed each change, so finished work never leaves the active set.
- **Tracked bulk.** 8,654 tracked files. `docs/` is 71.7 MB and `planning/` is 56.0 MB. The single largest file is `docs/src/generated-skill-indexes.mjs` (22.2 MB, 398,585 lines). The catalog browser does not import it. `CatalogBrowser.astro` reads `skills-catalog-browser-index.json`, and `tests/test_docs.py` asserts catalog pages do not mention `generated-skill-indexes.mjs`.
- **Split contracts.** `openspec/specs/cursor-harness/spec.md` and `wagents/platforms/cursor.py` (`CURSOR_DEFAULT_MODEL`) say `cursor-grok-4.6-xhigh`. `wagents/hooks/policies/cursor_task_model_pin.py`, `.cursor/rules/cursor-models.mdc`, and `.cursor/agents/*.md` still force `cursor-grok-4.5-high`. This environment rejects `cursor-grok-4.5-high`. The Task hook rewrites every launch to that dead slug, so subagents cannot start. There is no separate "500k" model slug. The live extra-high Grok 4.7 slug is `grok-4.7-xhigh`. `cursor-grok-4.6-xhigh` is also still accepted.
- **A false source of truth for skills.** `AGENTS.md` says harness-only skill keys live in `config/skill-adapters.json`. That file does not exist. Almost every `skills/*/SKILL.md` still carries `argument-hint`, `model`, or `user-invocable`.
- **The CLI does not import.** `wagents/cli.py` imports `wagents.commands.plugin`, and that module is not in the tree (`wagents/commands/` only has `validate.py`). `wagents/docs.py` imports `WEB_DIR` and `AUTHORING_SKILLS_DIR` from `wagents`, and `wagents/__init__.py` does not define them. CI still runs `uv run wagents docs ...` (`.github/workflows/ci.yml`), while the Typer group is registered only as `web`.
- **Generator path drift.** `wagents/docs.py` `write_site_data()` writes `docs/lib/generated-*.mjs`. `docs/lib` does not exist. Astro imports `docs/src/generated-site-data.mjs`. The next generate will not update the files the site loads.
- **Hook promotion is already applied and still filed as unstarted.** `config/tooling-policy.json` has `hook_perf.tier` set to `bundle`. `openspec/changes/fleet-hooks-promotion/tasks.md` is unchecked, and `openspec/specs/hooks-runtime-performance/spec.md` still says the default tier is `legacy`.

June's cleanup ledger (`planning/manifests/repo-cleanup-review-findings.md`) is historical. Its fixed rows stay fixed. It is not the backlog.

## Intent

The useful cleanup is already on `main`. Stop there.

Do not collapse skills, rewrite instruction files, or run another docs regeneration as part of this change. The only follow-up that is still real is moving the Things++ manifest out of its OpenSpec directory the next time that feature is edited. Everything else still under `openspec/changes/` is ordinary product work.

## Scope

- This OpenSpec change: the plan documents only.
- Later implementation is sequenced in `tasks.md` and is not part of landing this change.
- The plan covers OpenSpec lifecycle, generated-artifact weight, the Cursor model pin, docs writer paths, skill/agent contract honesty, and explicit non-goals.

## Out Of Scope

- Implementing waves 0–4 here.
- Rewriting git history. Deletes are forward commits. No file in this audit is a secret that would justify a rewrite.
- Deleting `planning/manifests/candidate-corpus-jul2026/`. Tests import `promotion-overrides.json` at collection time, `tests/test_candidate_receipts.py` schema-checks the receipt ledger, and `wagents/docs.py` raises if `runtime-activation-assurance.json` is missing. Archiving the finished intake change does not delete the corpus. `planning/tmp/` and `planning/workspaces/` are the scratch that can go.
- Deleting `docs/public/generated-registries/skills-catalog-index.json` (14.6 MB). `config/docs-artifact-registry.json` requires `uv run wagents catalog index --check` for that path.
- Stripping `argument-hint` / `model` / `user-invocable` from skill frontmatter before an adapter file exists.
- Merging the four `fleet-hooks-*` changes into one change.
- Starting `fleet-hooks-promotion`. The live tier is already `bundle`.
- Archiving `replace-supathings-with-things-plus-plus` while the registry schema `const` points at that change directory.
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
| Finishing `cursor-grok-high-pin` writes `cursor-grok-4.5-high` back over the spec | That change stays superseded. The live pin is `grok-4.7-xhigh`. |
| Archiving Things++ deletes the manifest the schema requires | Move `capability-manifest.json` to a durable path and update the schema `const` before archive. Also remove stale `supathings` client routes. |
| Corpus tests break if evidence JSON is "cleaned up" | Delete only `planning/tmp/` and `planning/workspaces/` after copying the seven-session deferral sentences into `repo-cleanup-review-findings.md`. |
| Instruction dedup deletes files sync will not recreate | `sync_agent_stack.py` does not write `.cursor/rules/` except the home copy of `cursor-models.mdc`. Replace duplicated bodies with pointers. Do not delete the rule files. |
