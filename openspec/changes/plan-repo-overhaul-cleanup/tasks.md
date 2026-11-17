# Tasks

Implementation of the overhaul is intentionally not done in this change. Boxes below are the later work, in dependency order. `[P]` marks work that can run beside the other `[P]` items in the same wave and must not share a file with them.

## Wave 0 — Unblock

- [x] 0.1 Make `wagents` import. Remove the `wagents.commands.plugin` import and the `plugin` Typer until that module exists. Stop importing `WEB_DIR`. Import `AUTHORING_SKILLS_DIR` from `wagents.skill_index` or define it on the package. Register the docs Typer group as `docs`, which `.github/workflows/ci.yml` already calls.
- [x] 0.2 Point the hook, `config/cursor-agents.json`, its schema `const`, `.cursor/rules/cursor-models.mdc`, and `.cursor/agents/*.md` at one slug. First landed as `cursor-grok-4.6-xhigh`. Maintainer override is task 0.7.
- [x] 0.7 Maintainer override: pin is `grok-4.7-xhigh` in the spec, hook, `CURSOR_DEFAULT_MODEL`, rule, overlays, and tests. 500k is the context window, not a second slug.
- [x] 0.3 Close `cursor-grok-high-pin` as superseded. Do not check off its remaining 4.5 tasks. Do not write `~/.cursor/cli-config.json` or `state.vscdb`.
- [x] 0.4 Point `wagents/docs.py` site-data writes and staleness checks at `docs/src/`, matching Astro imports and `tests/test_docs.py`. Replace `web/lib` and `wagents web generate` strings in those checks. Do not regenerate the skill-index module in this task.
- [x] 0.5 `[P]` Delete the tracked 49-byte file named `warning: could not open directory 'platforms/copilot/': No such file or directory` and the accidental root directory `warning: could not open directory 'platforms`.
- [x] 0.6 Run the wave 0 rows in `validation-matrix.md`, including a one-line `wagents --help` after the import fix. Pin and selector tests passed. Full pytest and `docs generate --check` stay for later waves.

## Wave 1 — Close the books

- [x] 1.1 Spot-check each fully checked change in `design.md`. Archive it only when one proposal claim is true on `main`. `package-version-check-mcp` is the registry server the change intended, so it was archived.
- [x] 1.2 Archive used `wagents openspec archive --skip-specs`. A normal archive of `prefer-grok-tier-t-trivial-offload` aborted because its MODIFIED block would drop scenarios already in the main spec. The same risk applies to the other landed deltas, so main specs were left untouched and 24 finished changes moved to `openspec/changes/archive/2026-11-17-*`. Not archived: ideas backlog, Things++, the still-open programs, `cursor-grok-high-pin`, and `fleet-hooks-promotion`. Corpus manifests stayed in git.
- [ ] 1.3 Finish the one-box changes listed in `design.md`, then archive them. Includes `fleet-hooks-parity`. Do not archive `replace-supathings-with-things-plus-plus` until its capability manifest lives outside the change directory and the schema `const` matches. Remove stale `supathings` client routes in that same change. Do not revert Things++ or the ChatGPT exporter.
- [x] 1.4 Close `fleet-hooks-promotion` without running its task list. Committed `hook_perf.tier` is already `bundle`. The spec fallback stays `legacy` only when the policy key is missing, which matches `resolve_hook_perf_tier`. Do not merge it with the other hook changes.
- [x] 1.5 Kill `remediate-rv-mcp` as a live change (header on `RV-CLOSURE.md`). Leave `public-release-prod-readiness` open. `opencode-claude-auth@latest` stays until a change updates `tests/test_distribution_metadata.py` and the OpenCode instruction together; do not delete the quarantine row.
- [ ] 1.6 Leave these open as their own programs: `token-efficacy-program`, `remediate-rv-skill-docs-contracts`, `remove-gemini-antigravity-copilot`, `activate-candidate-corpus-runtime-jul2026`, `fleet-skill-projection-assurance`, `integrate-apm-package-manager`, `integrate-mcphub-control-plane`, `compose-harness-catalog-pages`, `integrate-ideas-backlog`, `replace-supathings-with-things-plus-plus`.

## Wave 2 — Generated weight

- [ ] 2.1 Re-run the import search for `generated-skill-indexes.mjs` after the writer path fix. Expected: catalog UI uses `skills-catalog-browser-index.json`, not the module.
- [ ] 2.2 Stop writing the module. `git rm docs/src/generated-skill-indexes.mjs`. Forward commit only.
- [ ] 2.3 `[P]` Add `.gitattributes` `linguist-generated` for generated docs that remain. No Git LFS. No history rewrite.
- [x] 2.4 `[P]` Copy the seven-session deferral sentences into `repo-cleanup-review-findings.md`, then `git rm -r planning/tmp planning/workspaces` and gitignore both. Do not delete `planning/manifests/candidate-corpus-jul2026/` or `harness-reconciliation.json`.
- [ ] 2.5 Run wave 2 validation rows, including `catalog index --check` and `docs generate --no-installed --check`.

## Wave 3 — Contract honesty

- [ ] 3.1 Edit `AGENTS.md` so it stops claiming `config/skill-adapters.json` is the source of truth. Leave harness keys in `SKILL.md`.
- [ ] 3.2 Replace full `**/*` Cursor and Claude rule bodies with pointers at `instructions/global.md` and the harness overlays. Restore the Trust Boundary bullets missing from `.cursor/rules/global.mdc`. Do not delete the rule files. Sync does not recreate them.
- [ ] 3.3 File standing-context trim candidates into `token-efficacy-program` instead of editing `instructions/global.md` here.

## Wave 4 — Thin meta skills and scaffold agents

- [ ] 4.1 Do not start until catalog URLs for any removed skill id have a redirect or an explicit major-note. Keep `skill-creator` and `skill-router`.
- [ ] 4.2 Fold the thin `skill-*` report skills listed in `design.md` into `wagents` commands plus one maintainer skill, or close this task as "leave in place" if redirects are rejected.
- [ ] 4.3 Keep all 20 agent names, including the four scaffolds and `mcp-template-maintainer`. A later visibility change must edit the orchestrator allowlist, OpenCode overlay, Cursor registry, and eval manifests in the same commit.
- [ ] 4.4 Do not merge research / host-panel / wargame, and do not merge shell-scripter / shell-conventions / justfile. Move `shell-scripter`'s Justfile mode to `justfile` and fix the two redirects that disagree.

## Documentation

- [ ] D.1 This plan's five artifacts are the documentation for the program. Later waves refresh `README.md` and generated docs only when their own inputs change.
- [ ] D.2 When waves 0–2 have landed or been dropped, archive `plan-repo-overhaul-cleanup`. Waves 3–4 may already have their own changes by then.

## Verification

- [ ] V.1 `uv run wagents openspec validate` for this change before any wave starts.
- [ ] V.2 Each implementation wave runs only its rows in `validation-matrix.md`.
- [ ] V.3 No wave runs `wagents skills sync --apply` or a live plugin install.
