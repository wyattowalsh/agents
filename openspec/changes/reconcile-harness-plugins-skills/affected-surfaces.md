# Affected Surfaces

## New tracked source files

- `scripts/generate_harness_reconciliation.py` — read-only generator for the
  reconciliation matrix.
- `tests/test_harness_reconciliation.py` — static checks for coverage,
  terminal actions, and redaction.

## New tracked evidence files

- `planning/manifests/harness-reconciliation.json` — redacted local snapshot of
  skill/plugin/extension reconciliation state.

## New OpenSpec files

- `openspec/changes/reconcile-harness-plugins-skills/proposal.md`
- `openspec/changes/reconcile-harness-plugins-skills/design.md`
- `openspec/changes/reconcile-harness-plugins-skills/tasks.md`
- `openspec/changes/reconcile-harness-plugins-skills/affected-surfaces.md`
- `openspec/changes/reconcile-harness-plugins-skills/validation-matrix.md`
- `openspec/changes/reconcile-harness-plugins-skills/specs/skill-registry-intake/spec.md`
- `openspec/changes/reconcile-harness-plugins-skills/specs/downstream-tooling/spec.md`

## Local-only surfaces inspected, not modified

- `~/.codex/config.toml`
- `~/.codex/plugins/cache/agents/agents/local`
- `~/.config/opencode/opencode.json`
- `~/.config/opencode/tui.json`
- `~/.gemini/settings.json`
- `~/.gemini/extensions`
- `~/.grok/config.toml`

## Out of scope

- Home config writes, plugin installs, Skills CLI apply, and cache deletion.
