# Tasks

## Wave 1 — Planning And OpenSpec Tooling

- [x] Update `planning/manifests/external-skills/chrome-devtools-mcp.json` promotion
      block to `curated-external-catalog`, empty `repo_skill_names`, six external
      catalog rows in `executable_surface`, and `access_date: 2026-06-29`.
- [x] Create `openspec/changes/replace-chrome-devtools-custom-with-external/` with
      proposal, design, tasks, and delta specs for downstream-tooling and
      registry-core.
- [x] Supersede `upgrade-design-skill` chrome-retention language across design.md,
      agent-assets, registry-core, downstream-tooling, docs-instructions deltas,
      validation-matrix, and affected-surfaces.
- [x] Remove prefixed `chrome-devtools-*` entries from `wagents/eval_adequacy.py`
      `r3_names` and `high_names`; keep `chrome-devtools` as an R3 keyword only.
- [x] Update `tests/test_eval_adequacy.py` R3 fixture to use `mcp-creator`.
- [x] Update `skills/design/evals/evals.json` boundary assertions for upstream
      external handoff IDs.
- [x] Update `docs/src/skill-research/design.md` chrome boundary table rows.
- [x] Patch comparable-alternatives wording in accessibility, performance, seo,
      best-practices, web-quality-audit, and core-web-vitals research pages.

## Wave 2 — Catalog And Skill Removal (implementation)

- [x] Remove `skills/chrome-devtools*` directories if any remain.
- [x] Delete custom `docs/src/authoring/skills/chrome-devtools*.mdx` rows.
- [x] Delete custom `docs/src/skill-research/chrome-devtools*.md` pages unless
      retained as historical evidence only.
- [x] Add curated-external authoring MDX rows for all six upstream skills with
      install commands from `chrome-devtools-mcp.json` list evidence.
- [x] Mark Chrome rows `sync_kind: skills-cli`, preserve pinned audited install
      commands during `wagents skills sync`, and keep non-Skills-CLI tools such
      as `apm-cli` out of skills-sync apply rows.
- [x] Update cross-skill handoffs and README/catalog references from prefixed
      repo names to upstream IDs per slash migration table.
- [x] Run `uv run wagents catalog sync-authoring` and
      `uv run wagents docs generate --no-installed`.
- [x] Prove generated catalog has six curated-external Chrome rows and zero
      custom `chrome-devtools*` rows.

## Wave 3 — Validation

- [x] Run `uv run wagents openspec validate --strict --format json`.
- [x] Run `uv run wagents validate --format json`.
- [x] Run `uv run wagents eval validate --format json`.
- [x] Run `uv run pytest -q tests/test_eval_adequacy.py`.
- [x] Run `uv run python skills/design/scripts/check.py`.
- [x] Run `git diff --check`.
