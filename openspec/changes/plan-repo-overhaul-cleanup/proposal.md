# Proposal

> Wave 0 is done, and the maintainer then moved the pin. `wagents` imports, docs writes target `docs/src`, and the accidental warning path is gone. The enforced Cursor Task slug is `grok-4.7-xhigh` (Grok 4.7 extra high; 500k is that model's context window, not a separate slug). Waves 1–4 below are still open. The problem statement records the state this plan started from.

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

Publish one sequenced plan that says what to archive, what to delete, what to tighten, and what to leave alone. Later waves implement it. This change does not perform the overhaul.

Recommended order:

1. **P0 — Make `wagents` import.** Remove or add the missing `plugin` Typer, export the symbols `docs.py` imports, and register the docs command under the name CI already calls (`docs`). Do this before any generate or validate step.
2. **P0 — Make Task launches work.** The maintainer set the pin to `grok-4.7-xhigh`. That slug is in the spec, the hook, `cursor.py`, the Cursor rule, and `.cursor/agents/`. `cursor-grok-high-pin` stays superseded. There is no 500k slug.
3. **P0 — Repair the docs writer path** so generate updates `docs/src/`, which Astro already imports. Do this before any attempt to delete generated files.
4. **P1 — Archive finished OpenSpec changes** after a short spot-check, counting both `- [x]` and `1. [x]` lists. Do not archive `integrate-ideas-backlog` while its 20 `[~]` rows and 1 open box remain. Do not archive `replace-supathings-with-things-plus-plus` until `capability-manifest.json` is moved out of that change directory: `config/schemas/mcp-registry.schema.json` pins that path.
5. **P1 — Stop shipping the unused 22.2 MB skill-index module** after an import search and a docs check confirm the catalog still builds from the JSON indexes. `planning/tmp/` and `planning/workspaces/` can go in the same wave after the seven-session deferral sentences are copied into the findings ledger. Leave the July corpus, including `runtime-activation-assurance.json`, which `wagents/docs.py` reads.
6. **P1 — Reconcile hook tier text.** `hook_perf.tier` is already `bundle`. Update the hooks spec to say that, and close `fleet-hooks-promotion` without re-running its task list. Do not start that change.
7. **P2 — Tell the truth in contracts** (`AGENTS.md` vs missing `skill-adapters.json`; instruction projections vs `instructions/global.md`). Cursor and Claude rule copies are hand pastes. `sync_agent_stack.py` does not regenerate them. Replace the full `**/*` bodies with pointers. Do not strip skill frontmatter in this program.
8. **P2 — Finish in-flight product work that is still true.** Things++ stays open until the manifest moves and retired `supathings` client routes are gone. Harness retirement, token efficacy, and RV skill/docs contracts stay their own changes. Remove the repo-default `opencode-claude-auth@latest` plugin, or record an exception: quarantine row EXT-017 forbids that default.
9. **P3 — Collapse thin `skill-*` report skills** only after catalog URLs have a redirect story and `sync_skill_portability.py` no longer expects a toolkit copy in each deleted skill. Keep `skill-creator` and `skill-router`. Keep all 20 agent names; orchestrator allowlists and tests bind them. `mcp-template-maintainer` is not a scaffold.

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
