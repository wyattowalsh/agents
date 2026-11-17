# Validation Matrix

Landing **this plan** only requires the first row. Later rows are the gates for the wave that implements them. Do not run those commands while the change is still plan-only.

| Surface | Command | Expected Result | Notes |
| --- | --- | --- | --- |
| This plan | `uv run wagents openspec validate` | Exit 0 | Plan docs only. |
| This plan | `git diff --check` | Exit 0 | No whitespace errors. |
| Wave 0 pin | `rg -n "cursor-grok-4.5-high" --glob '!openspec/changes/archive/**' --glob '!planning/**'` | No matches in source, hooks, rules, or active spec | Archive and planning history may still mention 4.5. |
| Wave 0 CLI | `uv run wagents --help` | Exit 0 and a `docs` command is listed | Fails today on `wagents.commands.plugin` and on `WEB_DIR` / `AUTHORING_SKILLS_DIR`. |
| Wave 0 pin | Focused pytest for cursor pin / hook policy | Pass | Expected slug is `grok-4.7-xhigh`. |
| Wave 0 docs path | `rg -n 'DOCS_DIR / "lib"' wagents/docs.py` | No writer or staleness check still targets `docs/lib` for generated site modules | Astro imports `docs/src/generated-site-data.mjs`. |
| Wave 0 junk | `git ls-files` | No path whose name starts with `warning:` | |
| Wave 1 archive | `uv run wagents openspec validate` | Exit 0 after each archive batch | Spot-check one proposal claim before each archive. |
| Wave 1 registry spot-check | Read `config/mcp-registry.json` entry `package-version-check-mcp` against `replace-package-version-check-mcp` tasks | Archive only if the remaining entry is the intended end state | Do not delete the registry row just to make the change look done. |
| Wave 2 module | `rg -n "generated-skill-indexes.mjs" docs wagents tests --glob '!docs/src/generated-skill-indexes.mjs'` | Only generator code that was just removed, or zero matches | `tests/test_docs.py` already asserts catalog MDX does not name the file. |
| Wave 2 module | `uv run wagents docs generate --no-installed --check` | Exit 0 and the 22.2 MB file is not recreated | Run only after the writer path fix. |
| Wave 2 catalog | `uv run wagents catalog index --check` | Exit 0 | Proves the JSON indexes, not the unused module, are the catalog contract. |
| Wave 3 contract | `test ! -f config/skill-adapters.json && rg -n "skill-adapters.json" AGENTS.md` | `AGENTS.md` no longer claims the missing file is the source of truth | Keys stay in `SKILL.md` until a later adapter change. |
| Wave 3 corpus safety | `uv run pytest tests/test_candidate_corpus.py tests/test_candidate_receipts.py -q` | Pass without deleting manifests | Run if any planning file is removed. |
| Later release gate | Commands already listed in `public-release-prod-readiness` once that change has tasks | Two consecutive clean runs | Not part of waves 0–2. |

## Blockers

- Wave 2 delete is blocked on wave 0 writer-path fix. Deleting `docs/src/generated-skill-indexes.mjs` first either breaks a stale checker or gets recreated in the wrong directory.
- `fleet-hooks-promotion` is blocked on archiving `fleet-hooks-performance` and finishing `fleet-hooks-parity`.
- Wave 4 skill-id removal is blocked on catalog redirects. Until then the skills stay.
- Corpus deletion is blocked indefinitely by current tests. It is not a task in this plan.

## Deferred Checks

- Full `uv run pytest` is a wave-implementation gate, not a gate for merging this plan.
- `uv run wagents readme --check` and a docs build run when a later wave changes skill descriptions, agent pages, or generated MDX.
- Home Cursor sync and the IDE model picker stay operator-owned. Do not automate writes to `~/.cursor/cli-config.json` or `state.vscdb`.
- Live LLM evals stay out of CI. Structural `evals/evals.json` files already exist for all 67 skills; this plan does not add a live eval job.
