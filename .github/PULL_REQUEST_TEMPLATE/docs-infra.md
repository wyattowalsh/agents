<!--
Docs/infra change PR template — for docs generation, CI workflows, hooks,
and other repo-tooling changes that do not fit the skill/agent/mcp templates.
-->

## Summary

<!-- What changed and why, in 1-3 sentences. -->

## Type of change

- [ ] Docs generation / Starlight site (`wagents/docs.py`, `docs/`)
- [ ] CI workflow (`.github/workflows/*.yml`)
- [ ] Hooks fleet (`config/hook-registry.json`, `wagents/hooks/`, `hooks/`)
- [ ] Other repo tooling (scripts, `justfile`, config)

## Validation run locally

- [ ] `uv run wagents validate`
- [ ] `uv run wagents docs generate --no-installed --check` (docs changes)
- [ ] `uv run wagents docs build` (docs changes affecting build output)
- [ ] `actionlint .github/workflows/*.yml` (workflow changes)
- [ ] `uv run wagents hooks validate --harness all` (hooks changes)
- [ ] `uv run pytest` (relevant subset)
- [ ] `uv run wagents openspec validate` (if this change has an OpenSpec change directory)

## Collision / ownership notes

- [ ] I confirmed I am the sole owner of any serialized file I touched (`.github/workflows/ci.yml` is SA-CI-only; `wagents/docs.py` merges are SA-DOC-serialized; `config/mcp-registry.json` batches are SA-MCP0-serialized)
- [ ] No generated files (`docs/src/generated-sidebar.mjs`, catalog pages, `skills-catalog-index.json`) were hand-edited

## Rollout / risk notes

<!-- Any staged rollout flags, backward-compat concerns, or CI cost changes? -->
