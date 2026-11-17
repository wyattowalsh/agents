# Tasks

Implementation of the overhaul is intentionally not done in this change. Boxes below are the later work, in dependency order. `[P]` marks work that can run beside the other `[P]` items in the same wave and must not share a file with them.

## Wave 0 — Unblock

- [ ] 0.1 Choose the pin slug. Default: `grok-4.7-xhigh`. Fallback if the maintainer rejects a model move: `cursor-grok-4.6-xhigh`. Record the choice in `cursor-grok-high-pin` and in `openspec/specs/cursor-harness/spec.md`. Do not leave `cursor-grok-4.5-high` anywhere the hook can write.
- [ ] 0.2 Update these together: `wagents/hooks/policies/cursor_task_model_pin.py`, `wagents/platforms/cursor.py` `CURSOR_DEFAULT_MODEL`, `.cursor/rules/cursor-models.mdc`, `.cursor/agents/*.md`, and the cursor-harness spec. One constant in code, the same string in the spec.
- [ ] 0.3 Move `cursor-grok-high-pin` tasks `W2-L1`, `W2-L2`, and the operator verify box into the spec as SHOULD notes. They must not stay open tasks. Do not write `~/.cursor/cli-config.json` or `state.vscdb`.
- [ ] 0.4 Point `wagents/docs.py` site-data writes and staleness checks at `docs/src/`, matching Astro imports and `tests/test_docs.py`. Do not regenerate the skill-index module in this task.
- [ ] 0.5 `[P]` Delete the tracked 49-byte file named `warning: could not open directory 'platforms/copilot/': No such file or directory` and the accidental root directory `warning: could not open directory 'platforms`.
- [ ] 0.6 Run the wave 0 rows in `validation-matrix.md`.

## Wave 1 — Close the books

- [ ] 1.1 Spot-check each fully checked change in `design.md`. Archive it only when one proposal claim is true on `main`. Hold `replace-package-version-check-mcp` until the `package-version-check-mcp` registry entry is explained.
- [ ] 1.2 `[P]` Archive passes the spot-check: exporter, plannotator hooks, llms-txt explorer, cursor-cli harness, both finished hook changes, grill-me routing, candidate-corpus intake, ideas backlog, starlight stack, grok tier-t, harness plugin reconcile, agent-fleet governance, chrome-devtools replacement, ddgs replacement, skill-portability. Use `uv run wagents openspec archive`. Do not delete corpus manifests when the intake change archives.
- [ ] 1.3 Finish the one-box and last-mile changes listed in `design.md`, then archive them. Includes Things++ (`replace-supathings-with-things-plus-plus`) and `fleet-hooks-parity`. Do not revert Things++ or the ChatGPT exporter.
- [ ] 1.4 After 1.3, `fleet-hooks-promotion` may start. Do not merge it with the other hook changes.
- [ ] 1.5 `[P]` For each proposal-only change named in `design.md`, either add a real `tasks.md` or archive it as not started. Give `public-release-prod-readiness` tasks that cite this validation matrix. Do not implement those proposals in the triage sitting.
- [ ] 1.6 Leave these open as their own programs: `token-efficacy-program`, `remediate-rv-skill-docs-contracts`, `remove-gemini-antigravity-copilot`, `activate-candidate-corpus-runtime-jul2026`, `fleet-skill-projection-assurance`, `integrate-apm-package-manager`, `integrate-mcphub-control-plane`, `compose-harness-catalog-pages`.

## Wave 2 — Generated weight

- [ ] 2.1 Re-run the import search for `generated-skill-indexes.mjs` after the writer path fix. Expected: catalog UI uses `skills-catalog-browser-index.json`, not the module.
- [ ] 2.2 Stop writing the module. `git rm docs/src/generated-skill-indexes.mjs`. Forward commit only.
- [ ] 2.3 `[P]` Add `.gitattributes` `linguist-generated` for generated docs that remain. No Git LFS. No history rewrite.
- [ ] 2.4 `[P]` `rg` readers of `planning/workspaces/justfile-workspace/harness-sync-dry-run.json` and `planning/manifests/harness-reconciliation.json`. Delete a file only when nothing reads it. Do not delete `planning/manifests/candidate-corpus-jul2026/`.
- [ ] 2.5 Run wave 2 validation rows, including `catalog index --check` and `docs generate --no-installed --check`.

## Wave 3 — Contract honesty

- [ ] 3.1 Edit `AGENTS.md` so it stops claiming `config/skill-adapters.json` is the source of truth. Leave harness keys in `SKILL.md`.
- [ ] 3.2 Diff `instructions/global.md` against `.cursor/rules/global.mdc`, `instructions/codex-global.md`, and `instructions/opencode-global.md`. Fix the sync writer if projections drifted. Do not hand-delete a projection the writer will recreate.
- [ ] 3.3 File standing-context trim candidates into `token-efficacy-program` instead of editing `instructions/global.md` here.

## Wave 4 — Thin meta skills and scaffold agents

- [ ] 4.1 Do not start until catalog URLs for any removed skill id have a redirect or an explicit major-note. Keep `skill-creator` and `skill-router`.
- [ ] 4.2 Fold the thin `skill-*` report skills listed in `design.md` into `wagents` commands plus one maintainer skill, or close this task as "leave in place" if redirects are rejected.
- [ ] 4.3 For each scaffold agent named in `design.md`, implement it or stop publishing a public page. Keep the name if `config/opencode-agents.json` or `.cursor/agents/` still projects it. Re-read `mcp-template-maintainer` before hiding it.
- [ ] 4.4 Do not merge research / host-panel / wargame, and do not merge shell-scripter / shell-conventions / justfile.

## Documentation

- [ ] D.1 This plan's five artifacts are the documentation for the program. Later waves refresh `README.md` and generated docs only when their own inputs change.
- [ ] D.2 When waves 0–2 have landed or been dropped, archive `plan-repo-overhaul-cleanup`. Waves 3–4 may already have their own changes by then.

## Verification

- [ ] V.1 `uv run wagents openspec validate` for this change before any wave starts.
- [ ] V.2 Each implementation wave runs only its rows in `validation-matrix.md`.
- [ ] V.3 No wave runs `wagents skills sync --apply` or a live plugin install.
