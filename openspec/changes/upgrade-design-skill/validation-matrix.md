## Validation Matrix

| Area | Command | Required Result |
| --- | --- | --- |
| Branch | `git status --short --branch` | On `main`; unrelated dirty state preserved. |
| OpenSpec status | `uv run wagents openspec status --change upgrade-design-skill --format json` | Emits machine-readable change state. |
| OpenSpec strict validation | `uv run wagents openspec validate --strict --format json` | Passes. |
| Skill local check | `uv run python skills/design/scripts/check.py` | Passes metadata, eval, package, and audit checks. |
| Scanner tests | `uv run pytest -q tests/test_design_scan.py` | Passes. |
| Repo validation | `uv run wagents validate --format json` | Passes. |
| Eval validation | `uv run wagents eval validate --format json` | Passes. |
| Authoring sync | `uv run wagents catalog sync-authoring` | Custom authoring reflects `design`. |
| Docs generation | `uv run wagents docs generate --no-installed` | Emits generated docs and registries. |
| Catalog index | `uv run wagents catalog index --check --format json` | Passes. |
| Research coverage | `uv run wagents docs research --check-research --source-type custom --no-installed` | Passes. |
| Research artifacts | `uv run wagents docs research --validate-artifacts` | Passes. |
| README | `uv run wagents readme` then `uv run wagents readme --check --format json` | Fresh and check passes. |
| Docs build | `uv run wagents docs build` | Passes. |
| Sync preview | `uv run wagents skills sync --dry-run --format json` | No live install; preview succeeds. |
| Diff whitespace | `git diff --check` | Passes. |
| Folded custom skills | `for s in chrome-devtools chrome-devtools-a11y-debugging chrome-devtools-cli chrome-devtools-debug-optimize-lcp chrome-devtools-memory-leak-debugging chrome-devtools-troubleshooting; do test ! -d "skills/$s"; done` | Folded wrapper directories are removed. |
| Folded badge skills | `test ! -d skills/add-badges`; targeted scans for `add-badges` and `shieldcn-badges` in active catalog/docs routes | Badge and ShieldCN wrappers are folded into `/design` and not active as custom/external rows. |
| Global badge mirrors | `find /Users/ww/.agents/skills -maxdepth 1 \( -name add-badges -o -name shieldcn-badges \) -print` | Empty after explicit user-local cleanup approval, or reported as approval-gated residual. |
| Folded catalog rows | `jq` checks against `docs/public/generated-registries/skills-catalog-index.json` | Exactly one custom `design` row and zero active folded custom/external rows. |
| Chrome proof behavior | `rg -n "Chrome DevTools MCP|Inference First|compound mode|\\[mode\\] <request\\|path\\|url>" skills/design docs/src/skill-research/design.md docs/src/authoring/skills/design.mdx docs/src/content/docs/skills/catalog/custom/design.mdx` | Canonical sources and generated docs mention inference and Chrome proof. |
| MCP config isolation | `git diff --name-only -- config/mcp-registry.json config/codex-config.toml config/sync-manifest.json` | No output from this task. |
| Review consolidation isolation | `git diff --name-only -- skills/review skills/honest-review skills/simplify skills/external-skill-auditor openspec/changes/consolidate-review-skill` | No output from this task. |

## Cleanup Proof

- `test -d skills/design`
- `test ! -d skills/frontend-designer`
- `test -f docs/src/skill-research/design.md`
- `test ! -f docs/src/skill-research/frontend-designer.md`
- Generated catalog JSON contains a custom `design` row and no stale custom
  `frontend-designer` row.
- Generated catalog JSON contains no active custom rows for folded
  `chrome-devtools*` wrapper skills.
- Generated catalog/docs contain no active folded curated external UI/design
  rows after their useful synthesis is captured under `design`.
- Remaining `frontend-designer` text hits are categorized as historical,
  approved redirect, or fixed.
- Remaining folded-skill text hits are categorized as historical evidence,
  research synthesis, or fixed.
