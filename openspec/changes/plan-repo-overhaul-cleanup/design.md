# Design

## Approach

One planning change, then four implementation waves. Each wave has a stop rule: if the spot-check fails, fix or reopen, and do not continue to deletes that depend on it.

The June 2026 ledger stays as history. RV-RC-006's "archive only when an owner confirms" rule is replaced by a mechanical rule: a change is archive-ready when every task box is checked and one observable claim in its proposal is true on `main`. Operator-owned leftovers (IDE picker, home `cli-config.json`) are spec SHOULD notes, not open tasks that pin a change forever.

### Wave 0 — Unblock (P0)

**CLI import.** Before any `wagents` command in later waves:

- `wagents/cli.py` line 19 imports `plugin_app` from `wagents.commands.plugin`. That module is absent. `wagents/commands/` contains `__init__.py` and `validate.py` only. Drop the import and the `plugin` Typer until a real module exists, and drop `just` recipes that call it.
- `wagents/docs.py` imports `WEB_DIR` and `AUTHORING_SKILLS_DIR` from `wagents`. `__init__.py` defines `ROOT`, `DOCS_DIR`, and `CONTENT_DIR` only. `AUTHORING_SKILLS_DIR` already lives in `wagents/skill_index.py`. Stop importing `WEB_DIR`. There is no `web/package.json`. The site is `docs/`.
- CI (`.github/workflows/ci.yml` and `maintenance-freshness.yml`) calls `uv run wagents docs`. The Typer group is registered as `web` only. Register it as `docs`.

**Model pin.** Do not finish `cursor-grok-high-pin`. Its open boxes still target `cursor-grok-4.5-high`. The maintainer set the live pin to `grok-4.7-xhigh` (Grok 4.7 extra high). There is no separate 500k slug; 500k is that model's context window. The spec, hook, `CURSOR_DEFAULT_MODEL`, Cursor rule, overlays, and `.cursor/agents/` use that one string.

**Docs writer path.** `write_site_data()` in `wagents/docs.py` sets `lib_dir = DOCS_DIR / "lib"` with `DOCS_DIR = ROOT / "docs"`. Tracked files and Astro imports live under `docs/src/`. Point the writer and the staleness checks at `docs/src/` (the directory tests already use). Do not regenerate the 22.2 MB module until wave 2 decides its fate. Stale-check strings that say `web/lib` and `wagents web generate` get the same correction.

**Junk paths.** Delete the tracked 49-byte file whose name is the git error `warning: could not open directory 'platforms/copilot/': No such file or directory`, and the untracked directory `warning: could not open directory 'platforms`. `platforms/copilot/` is already gone; this is the leftover message, not a harness.

### Wave 1 — Close the books (P1)

Archive-ready now (every box checked). Spot-check, then archive. Do not re-implement them.

| Change | Boxes |
| --- | --- |
| `add-chatgpt-exporter-userscript` | 12/12 |
| `add-cursor-plannotator-hooks` | 16/16 |
| `add-llms-txt-explorer-mcp` | 10/10 |
| `elevate-cursor-agent-cli-harness` | 27/27 |
| `fleet-hooks-guard-expansion` | 21/21 |
| `fleet-hooks-performance` | 139/139 |
| `grill-me-harness-routing` | 12/12 |
| `integrate-candidate-corpus-jul2026` | 63/63 |
| `integrate-starlight-plugin-stack` | 9/9 |
| `prefer-grok-tier-t-trivial-offload` | 6/6 |
| `reconcile-harness-plugins-skills` | 15/15 |
| `remediate-agent-fleet-governance` | 14/14 |
| `replace-chrome-devtools-custom-with-external` | 22/22 |
| `replace-ddgs-mcp-adapter` | 10/10 |
| `replace-package-version-check-mcp` | 12/12 |
| `skill-portability-decouple` | 9/9 |
| `add-new-project-skill` | numbered 14/14 |
| `consolidate-review-skill` | numbered 15/15 |
| `upgrade-design-skill` | numbered 20/20 |
| `enhance-skill-creator-lifecycle` | numbered 12/12 |
| `enforce-unique-eval-prompts` | numbered 8/8 |
| `repair-ci-agent-stack-check` | numbered 3/3 |
| `grok-delegate-auth-self-contained` | numbered 8/9; last box is operator `grok login` |
| `integrate-custom-media-pentest-skills` | no `tasks.md`; `skills/ffmpeg`, `yt-dlp`, and `pentest` exist |

The first inventory only matched lines that start with `- [x]`. Numbered `1. [x]` lists are done too. `integrate-ideas-backlog` is not in this table: it has 127 `[x]` rows, 1 open box, and 20 `[~]` deferrals. Archiving it would hide that.

`skill-portability-decouple` is about portable ZIP paths and CI, not about removing frontmatter keys. Archiving it does not authorize a frontmatter strip. Deleting a `skill-*` directory later must update that sync list, because each skill still vendors `scripts/asset_toolkit/`.

`integrate-candidate-corpus-jul2026` being done means the intake change can archive. It does not mean the JSON corpus can leave git.

`replace-package-version-check-mcp` stays in the spot-check list because `config/mcp-registry.json` still has a `package-version-check-mcp` entry. Archive only if that remaining entry matches the change's definition of done.

Finish-then-archive (one to six boxes left, or a last-mile product change). Do not merge these into this plan.

- MCP adds at 10/11 or 11/12: `add-jupyter-mcp-server`, `add-scrapling-mcp`, `add-open-websearch-mcp-skill`, `add-reddit-mcp-buddy`.
- `add-lm-studio-harness` 29/30.
- `fleet-hooks-parity` 84/90. Archive `fleet-hooks-performance` and `fleet-hooks-guard-expansion` after the spot-check. Do not collapse the four hook changes into one.
- `fleet-hooks-promotion` is not unstarted work. `config/tooling-policy.json` already sets `hook_perf.tier` to `bundle`, and `fleet-pre-tool-enforce` is already in the hook registry. The unchecked task list would redo that flip. Close the change after the hooks spec stops saying the default tier is `legacy`. Do not run its task list.
- `harden-docs-site-findings-jul2026` 28/29, `integrate-rtk-harness-fleet` 40/41, `mcphub-qsv-data-group` 13/14, `optimize-harness-image-inputs` 35/36.
- `kill-agent-attribution` 5/7.
- `replace-supathings-with-things-plus-plus` stays open. Recent commits sealed the local Things++ runtime and the exporter. Do not revert them. Do not archive this change until `capability-manifest.json` moves to a durable path: `config/mcp-registry.json` and `config/schemas/mcp-registry.schema.json` both `const` that file inside the change directory. `supathings` is still a server id in the registry beside `things`. Remove those retired client routes in the same change. A checked task names `config/skill-adapters.json` as its output; that file is not in the tree now, so do not treat the checkbox as proof the adapter file exists.

Keep open as their own programs, even though they are young:

- `token-efficacy-program` (2/31) — standing-context trim.
- `remediate-rv-skill-docs-contracts` (0/33) — RV-003, RV-009, RV-010, RV-012.
- `remove-gemini-antigravity-copilot` (0/15) — real harness retirement, not a drive-by delete during the archive wave.
- `activate-candidate-corpus-runtime-jul2026` (7/37) — runtime receipts. Do not "simplify" by deleting evidence it measures.
- `fleet-skill-projection-assurance` (6/15), `integrate-apm-package-manager` (27/35), `integrate-mcphub-control-plane` (11/16), `compose-harness-catalog-pages` (2/7).

Still needs a real task list or an explicit kill, not an archive-as-done:

- `harden-nerdbot-source-health-skill-tooling` has no `tasks.md`.
- `remediate-rv-mcp` is a closure note whose DDGS pin (`ddgs-mcp-server==0.5.1`) is not what shipped (`ddgs[mcp]==9.14.4` in `scripts/mcphub/ddgs-stdio.sh`). Kill it. Do not archive it as current truth.
- `public-release-prod-readiness` already has tasks 1–10, all open. Leave it. It is the release gate after the CLI imports and the RV contracts move. Do not invent a second task list.

`remove-gemini-antigravity-copilot` stays a real change. `config/tooling-policy.json` still has `copilot` and `gemini` model-default keys, and `token-efficacy-program` still names those harnesses in its RTK apply list. Do not apply token-efficacy's platform list until the retirement change decides they are gone. `agents/README.md` still claims a Copilot agent directory that is not in the tree.

### Wave 2 — Generated weight (P1)

After wave 0's writer path fix:

1. Confirm no Astro, MDX, or TS file imports `generated-skill-indexes.mjs` (already true for `docs/src/components/CatalogBrowser.astro` and catalog pages; re-check after the path fix).
2. Stop rendering that module in `render_skill_indexes_module` / `write_site_data`.
3. `git rm` the 22.2 MB file. Forward delete only.
4. Add `linguist-generated` in a new `.gitattributes` for the generated files that stay (`docs/src/generated-site-data.mjs`, catalog JSON). No LFS. No history rewrite.
5. Leave the 14.6 MB catalog index. A size budget belongs to a catalog change, not a delete.

`planning/tmp/` and `planning/workspaces/` have no readers under `tests/`, `wagents/`, `scripts/validate/`, or `docs/`. Delete them after copying the seven-session sentences from `planning/workspaces/seven-session-resume/ledger.md` into `planning/manifests/repo-cleanup-review-findings.md` (the "145" quarantine residual and "S6 cleanup closed light"). Then gitignore both directories. Keep `planning/manifests/harness-reconciliation.json`; tests use it. Keep `runtime-activation-assurance.json`; `wagents/docs.py` errors if it is missing.

`platforms/chatgpt/dev-harness/` is an abandoned gateway: it starts scripts that are not in the tree. Remove it only after confirming LaunchAgent `com.wyatt.agents.chatgpt-dev-harness` is not loaded. Do not touch the Things++ bundle beside it.

### Wave 3 — Contract honesty (P2)

- Rewrite the `AGENTS.md` skill-key paragraph so it describes the tree: those keys are still in `SKILL.md`, and `config/skill-adapters.json` is not a file. Do not invent the adapter file in this wave.
- `.cursor/rules/global.mdc` is a hand paste and is missing Trust Boundary bullets that are in `instructions/global.md`. `.cursor/rules/codex.mdc` and `.claude/rules/codex.md` are missing those bullets and the MCPHub preflight section. `sync_agent_stack.py` does not regenerate these files. Replace the full `globs: "**/*"` bodies with one-line pointers at the hand files, the same shape as `claude-code.mdc`. Do not delete the rule files. Highest duplicate is the second full copy of global inside the Codex rules, then the 13 KB OpenCode rule (OpenCode already loads `instructions/opencode-global.md`).
- Do not start a parallel trim of `instructions/global.md`. File the trim list as input to `token-efficacy-program`.

### Wave 4 — Refine products that are actually thin (P3)

Skill meta family, measured body lines: `skill-token-budget-linter` 37, `skill-quality-dashboard` 38, `skill-bundle-curator` 39, `skill-compat-matrix` 47, `skill-install-dry-run-planner` 47, `skill-lifecycle-manager` 48, `skill-trace-debugger` 48, `skill-eval-scaffolder` 49, `skill-tag-taxonomist` 50. `skill-creator` is 259 lines and `skill-router` is 140. All 67 skills have an `evals/` directory, so "no evals" is not a deletion reason.

Target shape, only after catalog URL redirects exist and the portability sync list drops those directories: keep `skill-creator` and `skill-router`; fold the nine report skills into `wagents eval` / `audit` commands. `skill-package-manifest-enricher` becomes `wagents package enrich`, then the skill can go. Until the redirect exists, leave the skills in place. Niche product skills stay. Research, host-panel, and wargame stay distinct. Shell-conventions, shell-scripter, and justfile stay distinct, except one routing fix: `shell-scripter` still has a Justfile mode while `justfile/references/when-not-just.md` says that work belongs to `/justfile`. Move that mode. Do not merge the skills.

Keep all 20 agent names. `config/agent-delegation-policy.json`, OpenCode task allowlists, Cursor overlays, and `tests/test_agent_eval_manifests.py` bind them. The four self-described scaffolds (`agent-permission-simulator`, `agent-registry-publisher`, `agent-transpiler`, `prompt-optimizer`) stay until a change updates those allowlists in the same commit. `mcp-template-maintainer` is a real `acceptEdits` agent, not a scaffold. Do not hide it. Eight core agents have no `evals/agents/` manifest; that gap is not a test failure. Do not add live LLM evals.

### Leave alone

- The 67 skills as a set, including every niche skill.
- Fail-closed shell, secret, and protected-path hooks. The model-pin hook stays fail-open, but its slug must be valid.
- MCPHub as an opt-in maintainer surface.
- Things++ (`mcp/things-core`, `things-native`, `things-shortcuts`, `packages/things-common`) and `tools/userscripts/chatgpt-exporter`.
- Candidate-corpus manifests required by tests.
- `README.md` generation and `START-HERE.md`.
- The eight quarantine rows. Do not delete them to go green. `opencode.json` still enables `opencode-claude-auth@latest` while EXT-017 says that plugin must not be a repo default. Remove the default or write the exception. Do not clear the row.
- `skills/pentest` policy boundaries. No exploit-procedure cleanup in this plan.
- `skills/nerdbot/uv.lock` (0.92 MB) until the nerdbot change says whether the skill vendors its own environment on purpose.

## Data And Control Flow

```text
wave 0 CLI import, pin matches 4.6 spec, docs path
        |
        v
wave 1 archive checked changes; do not archive ideas or Things++ yet
        |
        +----> close fleet-hooks-promotion as already applied
        |
        v
wave 2 drop unused skill-index module, planning/tmp, planning/workspaces
        |
        v
wave 3 contract text matches the tree; token trim handed to token-efficacy-program
        |
        v
wave 4 skill-meta collapse and scaffold-agent visibility, only with redirects
```

OpenSpec remains the record. This plan change archives itself only after waves 0–2 have landed or been explicitly dropped. Waves 3–4 can outlive it as their own changes.

## Integration Points

- Archive with the repo's OpenSpec wrapper (`uv run wagents openspec archive`), not by moving directories by hand, so specs and change indexes stay consistent.
- Model pin tests and hook policy must change in one commit. A hook-only edit will be overwritten or will disagree with the spec again.
- Docs deletes go through the generator. Hand-deleting `docs/src/generated-*.mjs` without changing `write_site_data()` brings the file back, or, given the current path bug, writes a second copy under `docs/lib/`.

## Alternatives Rejected

- **One giant cleanup commit.** Mixes a pin fix, 17 archives, and a 22 MB delete. Unreviewable, and the delete depends on the path fix.
- **Deleting `planning/`**. Breaks corpus tests and throws away the only record of accepted deferrals (RV-RC-006 and the wontfix rows).
- **Deleting generated catalog JSON because it is large.** The browser and `catalog index --check` require it.
- **Collapsing product skills that share a domain.** The NOT-for lines are the product boundary.
- **New compatibility shims for the old model slug.** `cursor-grok-4.5-high` is not in the catalog. There is no runtime to shim. The old string should disappear from repo source.
- **History rewrite to shrink clone size.** A forward `git rm` of the 22 MB module is enough. The corpus must stay.

## Migration Or Compatibility Notes

No on-disk migration for users. Cursor home agents that still say `cursor-grok-4.5-high` update on the next home sync the maintainer chooses to run. This plan does not run that sync.

Catalog URLs under `/skills/catalog/custom/` and `/skills/catalog/external/` stay stable through waves 0–3. Wave 4 may remove skill ids only with redirects or a catalog major note.
