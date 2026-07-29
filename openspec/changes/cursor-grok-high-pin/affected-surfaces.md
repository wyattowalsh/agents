# Affected surfaces

## Spec / change

- `openspec/specs/cursor-harness/spec.md` (live flip)
- `openspec/changes/cursor-grok-high-pin/**` (this change)

## Pin / overlay

- `config/cursor-agents.json`
- `config/schemas/cursor-agents.schema.json`
- `.cursor/agents/*.md` (generated)
- `.cursor/rules/cursor-models.mdc`

## Adapter / sync

- `wagents/platforms/cursor.py`
- `scripts/sync_agent_stack.py` (`CURSOR_HOME_RULES_ALLOWLIST`, home agents)
- `config/sync-manifest.json`

## Hooks

- `config/hook-registry.json` (`cursor-task-model-pin-rewrite`, `cursor-subagent-model-allowlist`)
- `wagents/hooks/policies/cursor_task_model_pin.py`
- `.cursor/hooks.json` (generated)

## Docs / KB

- `kb/wiki/topics/cursor-harness-policy.md`
- `kb/wiki/topics/agent-frontmatter-dialects.md`
- `AGENTS.md` / harness-surface notes (as needed)

## Tests

- Focused pin/sync/hook tests under `tests/`

## Local (machine, not committed)

- `~/.cursor/cli-config.json` (`exploreSubagentModel`)
- `~/.cursor/rules/cursor-models.mdc`
- `~/.cursor/agents/` (managed-marker)
- IDE picker Grok 4.5 High; RO verify `state.vscdb` only
