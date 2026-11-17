# Affected Surfaces

This change adds plan documents only. The rows below are the surfaces later waves touch. Nothing in those rows is edited by landing the plan.

## Source Of Truth

| Path | Wave | Why it is in the plan |
| --- | --- | --- |
| `openspec/changes/plan-repo-overhaul-cleanup/` | now | This plan. |
| `openspec/changes/*` (50 active) | 1 | Archive, finish, or give tasks. Do not edit `openspec/changes/archive/**` history. |
| `openspec/specs/cursor-harness/spec.md` | 0 | Still requires `cursor-grok-4.6-xhigh` while the hook forces a dead slug. |
| `wagents/cli.py`, `wagents/docs.py`, `wagents/__init__.py` | 0 | Missing `plugin` module and missing `WEB_DIR` / `AUTHORING_SKILLS_DIR` exports. CI calls `wagents docs`. |
| `wagents/hooks/policies/cursor_task_model_pin.py` | 0 | `CURSOR_PINNED_MODEL = "cursor-grok-4.5-high"`. |
| `config/tooling-policy.json` | 1 | `hook_perf.tier` is already `bundle`. Spec text still says `legacy`. |
| `config/mcp-registry.json`, `config/schemas/mcp-registry.schema.json` | 1 | Things++ manifest path is inside the open change. `supathings` id remains. |
| `opencode.json` | 1 | `opencode-claude-auth@latest` contradicts quarantine EXT-017. |
| `wagents/platforms/cursor.py` | 0 | `CURSOR_DEFAULT_MODEL = "cursor-grok-4.6-xhigh"`. |
| `.cursor/rules/cursor-models.mdc` | 0 | Always-apply rule still names 4.5-high. |
| `.cursor/agents/*.md` | 0 | Frontmatter `model: cursor-grok-4.5-high` on every projected agent. |
| `wagents/docs.py` (`write_site_data`) | 0 | Writes `docs/lib/...`; site imports `docs/src/...`. |
| `AGENTS.md` | 3 | Points at missing `config/skill-adapters.json`. |
| `instructions/global.md` | 3 | Canonical shared instructions (11.8 KB). Trim stays owned by `token-efficacy-program`. |
| `skills/skill-*` except `skill-creator` and `skill-router` | 4 | Thin report skills (about 37–50 body lines). Not deleted in waves 0–3. |
| `agents/agent-permission-simulator.md`, `agent-registry-publisher.md`, `agent-transpiler.md`, `prompt-optimizer.md` | 4 | Bodies describe themselves as planned scaffolds. |
| Repo root file `warning: could not open directory 'platforms/copilot/': No such file or directory` | 0 | 49-byte tracked accident. |
| Repo root directory `warning: could not open directory 'platforms` | 0 | Accidental directory whose only child is `'copilot'`. |

## Generated Outputs

Do not hand-edit.

| Path | Size | Plan |
| --- | --- | --- |
| `docs/src/generated-skill-indexes.mjs` | 22.2 MB | Stop emitting after proof it has no site import. Header says `wagents docs generate` wrote it. |
| `docs/src/generated-site-data.mjs` | 0.75 MB | Keep. Astro imports it (`docs/astro.config.mjs`, Starlight components). |
| `docs/public/generated-registries/skills-catalog-index.json` | 14.6 MB | Keep. Registry validation owns it. Slim only with a catalog-index design, not a delete. |
| `docs/public/generated-registries/skills-catalog-browser-index.json` | 0.50 MB | Keep. This is what `CatalogBrowser.astro` loads. |
| `docs/public/generated-skill-indexes/install-scripts.json` | 0.56 MB | Keep. Install page references it. |
| `planning/manifests/candidate-corpus-jul2026/**` | majority of 56 MB `planning/` | Keep in git. Tests bind these files. A later fixture extraction is a separate change. |
| `mcp/mcphub/downstream/provenance/*.json` | 3.6 MB + 0.62 MB | Do not delete until a test/rg shows no reader. Not a wave 0 delete. |
| `README.md` | generated | Refresh only when a later wave changes skill or agent descriptions. |

## Downstream Agent Artifacts

- `.cursor/rules/global.mdc` (11.4 KB), `.cursor/rules/codex.mdc` (12.3 KB), `.cursor/rules/opencode.mdc` (13.3 KB) overlap `instructions/global.md`, `instructions/codex-global.md`, and `instructions/opencode-global.md`. Treat them as projections until a diff proves a hand-maintained fork.
- `config/opencode-agents.json` must stay in filename lockstep with `agents/*.md` if scaffold agents are hidden rather than deleted.
- Home `~/.cursor/` is out of scope. Sync must not write `cli-config.json` or `state.vscdb` (existing spec).

## Tests

Later waves must update, not skip:

- Pin: tests that assert `cursor-grok-4.5-high` or `cursor-grok-4.6-xhigh` (`tests/` grep during wave 0).
- Docs path: `tests/test_docs.py`, `tests/test_golden_docs.py` expect `docs/src/generated-site-data.mjs`.
- Corpus: `tests/test_candidate_corpus.py`, `tests/test_candidate_receipts.py`, `tests/test_retire_harness_targets.py`.
- OpenSpec: `uv run wagents openspec validate` after archives.

## Validation Commands

For this plan change:

- `uv run wagents openspec validate`
- `git diff --check`

For later waves, use the matrix in `validation-matrix.md`. Do not run live installs.
