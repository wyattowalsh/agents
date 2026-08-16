# Affected surfaces

## Tracked source

- `openspec/specs/cursor-harness/spec.md`
- `openspec/changes/elevate-cursor-agent-cli-harness/**`
- `config/harness-surface-registry.json`
- `config/hook-surface-registry.json`
- `config/sync-manifest.json`
- `config/plugin-extension-registry.json`
- `config/image-input-optimizer.json`
- `config/rtk-integration.json`
- `planning/manifests/harness-fixture-support.json`
- `planning/manifests/repo-sync-inventory.json`
- `planning/manifests/repo-drift-ledger.json`
- `skills/harness-master/SKILL.md`
- `skills/harness-master/scripts/discovery/classify_intent.py`
- `skills/harness-master/scripts/discover_surfaces.py`
- `skills/harness-master/scripts/usage_probe.py`
- `skills/harness-master/references/harness-surfaces.md`
- `skills/harness-master/references/harness-checklists.md`
- `skills/harness-master/references/latest-doc-sources.md`
- `skills/harness-master/references/install-guidance.md`
- `skills/harness-master/references/usage-review.md`
- `skills/harness-master/evals/evals.json`
- `skills/harness-master/evals/cursor-agent-alias.json`
- `skills/harness-master/evals/cursor-cli-both.json` (new)
- `docs/src/authoring/skills/harness-master.mdx`
- `instructions/cursor-cli-global.md` (new)
- `.cursor/rules/cursor-cli.mdc` (new)
- `AGENTS.md`
- `platforms/cursor-cli/README.md` (new)
- `wagents/cursor_cli_doctor.py` (new)
- `wagents/cli.py` (append-only command)
- `justfile`
- `scripts/cursor/agent-wrapper.sh` (optional new)
- `tests/test_discovery_classify_intent.py`
- `tests/test_distribution_metadata.py`
- `tests/test_cursor_cli_doctor.py` (new)

## Generated (do not hand-edit)

- `docs/src/content/docs/harness-support.mdx` via `wagents web generate`
- public catalog / `skills-catalog-index.json` via `wagents web generate`
- `README.md` via `wagents readme` when catalog/AGENTS inputs change

## Explicitly not changed

- `wagents/site_model.py` `SUPPORTED_AGENTS`
- `config/hook-registry.json` render harness lists
- `wagents/platforms/cursor.py` (unless a later approved permission-token hole)
- `~/.cursor/cli-config.json` / `state.vscdb`
