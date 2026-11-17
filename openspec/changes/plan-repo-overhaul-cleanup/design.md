# Design

## Approach

One planning change, then four implementation waves. Each wave has a stop rule: if the spot-check fails, fix or reopen, and do not continue to deletes that depend on it.

The June 2026 ledger stays as history. RV-RC-006's "archive only when an owner confirms" rule is replaced by a mechanical rule: a change is archive-ready when every task box is checked and one observable claim in its proposal is true on `main`. Operator-owned leftovers (IDE picker, home `cli-config.json`) are spec SHOULD notes, not open tasks that pin a change forever.

### Wave 0 — Unblock (P0)

**Model pin.** Finish inside `openspec/changes/cursor-grok-high-pin/`, do not start a sibling change. That change is 29/32. The three open boxes are operator-owned (`W2-L1`, `W2-L2`, and the local verify that repeats them). Repo code has already drifted past the change text: the task list still says the writer default became `cursor-grok-4.5-high`, but `wagents/platforms/cursor.py` now says `cursor-grok-4.6-xhigh`, and the spec agrees with `cursor.py`. The hook and the Cursor rule do not.

Pick one slug and write it everywhere the pin is read:

| Copy | Current value | Allowed here? |
| --- | --- | --- |
| Hook `CURSOR_PINNED_MODEL` | `cursor-grok-4.5-high` | No. Task rewrite fails. |
| `.cursor/rules/cursor-models.mdc` and `.cursor/agents/*.md` | `cursor-grok-4.5-high` | No. |
| Spec and `CURSOR_DEFAULT_MODEL` | `cursor-grok-4.6-xhigh` | Yes. |
| Maintainer request for this session | `grok-4.7-xhigh` | Yes. Extra high. No 500k slug exists. |

**Recommendation:** set the single constant to `grok-4.7-xhigh`, and change the spec scenario to that slug in the same commit. The hook's job is to force a slug the catalog accepts. A pin the catalog rejects is worse than a pin one generation behind.

**Rejected alternative:** keep the spec on `cursor-grok-4.6-xhigh` and only repair the hook to match it. Choose this if the maintainer wants no model move. Do not choose "leave the hook on 4.5".

Close the operator boxes by moving them into the spec as SHOULD, then archive `cursor-grok-high-pin` in wave 1.

**Docs writer path.** `write_site_data()` in `wagents/docs.py` sets `lib_dir = DOCS_DIR / "lib"` with `DOCS_DIR = ROOT / "docs"`. Tracked files and Astro imports live under `docs/src/`. Point the writer and the staleness checks at `docs/src/` (the directory tests already use). Do not regenerate the 22.2 MB module until wave 2 decides its fate.

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
| `integrate-ideas-backlog` | 126/126 |
| `integrate-starlight-plugin-stack` | 9/9 |
| `prefer-grok-tier-t-trivial-offload` | 6/6 |
| `reconcile-harness-plugins-skills` | 15/15 |
| `remediate-agent-fleet-governance` | 14/14 |
| `replace-chrome-devtools-custom-with-external` | 22/22 |
| `replace-ddgs-mcp-adapter` | 10/10 |
| `replace-package-version-check-mcp` | 12/12 |
| `skill-portability-decouple` | 9/9 |

`skill-portability-decouple` is about portable ZIP paths and CI, not about removing frontmatter keys. Archiving it does not authorize a frontmatter strip.

`integrate-candidate-corpus-jul2026` being done means the intake change can archive. It does not mean the JSON corpus can leave git.

`replace-package-version-check-mcp` stays in the spot-check list because `config/mcp-registry.json` still has a `package-version-check-mcp` entry. Archive only if that remaining entry matches the change's definition of done.

Finish-then-archive (one to six boxes left, or a last-mile product change). Do not merge these into this plan.

- MCP adds at 10/11 or 11/12: `add-jupyter-mcp-server`, `add-scrapling-mcp`, `add-open-websearch-mcp-skill`, `add-reddit-mcp-buddy`.
- `add-lm-studio-harness` 29/30.
- `fleet-hooks-parity` 84/90. Archive `fleet-hooks-performance` and `fleet-hooks-guard-expansion` first. Start `fleet-hooks-promotion` (0/24) only after parity is archived. Do not collapse the four hook changes into one.
- `harden-docs-site-findings-jul2026` 28/29, `integrate-rtk-harness-fleet` 40/41, `mcphub-qsv-data-group` 13/14, `optimize-harness-image-inputs` 35/36.
- `kill-agent-attribution` 5/7.
- `replace-supathings-with-things-plus-plus` 23/31. Finish it. Recent commits already sealed Things++ and the exporter. Do not revert those commits.

Keep open as their own programs, even though they are young:

- `token-efficacy-program` (2/31) — standing-context trim.
- `remediate-rv-skill-docs-contracts` (0/33) — RV-003, RV-009, RV-010, RV-012.
- `remove-gemini-antigravity-copilot` (0/15) — real harness retirement, not a drive-by delete during the archive wave.
- `activate-candidate-corpus-runtime-jul2026` (7/37) — runtime receipts. Do not "simplify" by deleting evidence it measures.
- `fleet-skill-projection-assurance` (6/15), `integrate-apm-package-manager` (27/35), `integrate-mcphub-control-plane` (11/16), `compose-harness-catalog-pages` (2/7).

Proposal-only (no `tasks.md`). One sitting each: write tasks or archive as not started. Do not implement them during that sitting.

`add-new-project-skill`, `consolidate-review-skill`, `enforce-unique-eval-prompts`, `enhance-skill-creator-lifecycle`, `grok-delegate-auth-self-contained`, `harden-nerdbot-source-health-skill-tooling`, `integrate-custom-media-pentest-skills`, `public-release-prod-readiness`, `remediate-rv-mcp`, `repair-ci-agent-stack-check`, `upgrade-design-skill`.

`public-release-prod-readiness` is the right home for a later release gate. Give it tasks that point at the validation matrix. Do not delete it as noise.

### Wave 2 — Generated weight (P1)

After wave 0's writer path fix:

1. Confirm no Astro, MDX, or TS file imports `generated-skill-indexes.mjs` (already true for `docs/src/components/CatalogBrowser.astro` and catalog pages; re-check after the path fix).
2. Stop rendering that module in `render_skill_indexes_module` / `write_site_data`.
3. `git rm` the 22.2 MB file. Forward delete only.
4. Add `linguist-generated` in a new `.gitattributes` for the generated files that stay (`docs/src/generated-site-data.mjs`, catalog JSON). No LFS. No history rewrite.
5. Leave the 14.6 MB catalog index. A size budget belongs to a catalog change, not a delete.

`planning/workspaces/justfile-workspace/harness-sync-dry-run.json` (0.94 MB) is a dry-run dump. Delete it only when `rg` shows no test reads it. Same rule for `planning/manifests/harness-reconciliation.json` (2.67 MB).

### Wave 3 — Contract honesty (P2)

- Rewrite the `AGENTS.md` skill-key paragraph so it describes the tree: those keys are still in `SKILL.md`, and `config/skill-adapters.json` is not a file. Do not invent the adapter file in this wave.
- Diff `instructions/global.md` against `.cursor/rules/global.mdc` and the Codex/OpenCode copies. If sync regenerates a byte-identical projection, mark the projection generated. If the copies have drifted, fix the writer, do not hand-merge three 12 KB files in a cleanup commit.
- Do not start a parallel trim of `instructions/global.md`. File the trim list as input to `token-efficacy-program`.

### Wave 4 — Refine products that are actually thin (P3)

Skill meta family, measured body lines: `skill-token-budget-linter` 37, `skill-quality-dashboard` 38, `skill-bundle-curator` 39, `skill-compat-matrix` 47, `skill-install-dry-run-planner` 47, `skill-lifecycle-manager` 48, `skill-trace-debugger` 48, `skill-eval-scaffolder` 49, `skill-tag-taxonomist` 50. `skill-creator` is 259 lines and `skill-router` is 140. All 67 skills have an `evals/` directory, so "no evals" is not a deletion reason.

Target shape, only after catalog URL redirects exist: keep `skill-creator` and `skill-router`; fold the report-shaped skills into `wagents` subcommands plus one maintainer skill. Until that redirect exists, leave the skills in place. Niche product skills (draw-thing, things-manager, nerdbot, pentest, and the rest) stay. Overlap among research / host-panel / wargame and among shell-scripter / shell-conventions / justfile is real and is **keep-distinct**. Their descriptions already draw NOT-for boundaries.

Scaffold agents stay in `agents/` until a wave-4 decision per name: implement, or mark non-public and stop emitting a public docs page. Do not delete a name that `config/opencode-agents.json` or `.cursor/agents/` still projects. Candidates whose bodies say planned or scaffold: `agent-permission-simulator`, `agent-registry-publisher`, `agent-transpiler`, `prompt-optimizer`. `mcp-template-maintainer` matched the word scaffold; re-read it before hiding it.

### Leave alone

- The 67 skills as a set, including every niche skill.
- Fail-closed shell, secret, and protected-path hooks. The model-pin hook stays fail-open, but its slug must be valid.
- MCPHub as an opt-in maintainer surface.
- Things++ (`mcp/things-core`, `things-native`, `things-shortcuts`, `packages/things-common`) and `tools/userscripts/chatgpt-exporter`.
- Candidate-corpus manifests required by tests.
- `README.md` generation and `START-HERE.md`.
- Security quarantine register and `skills/pentest` policy boundaries. No exploit-procedure cleanup in this plan.
- `skills/nerdbot/uv.lock` (0.92 MB) until the nerdbot change says whether the skill vendors its own environment on purpose.

## Data And Control Flow

```text
wave 0 pin + docs path
        |
        v
wave 1 archive checked changes, finish one-box changes, triage proposal-only
        |
        +----> fleet-hooks-promotion waits on parity archive
        |
        v
wave 2 drop unused skill-index module, linguist-generated marks
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
