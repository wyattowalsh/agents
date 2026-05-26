# Affected Surfaces

## Source Of Truth

- `instructions/global.md` — canonical cross-platform instruction source.
- `instructions/opencode-global.md` — OpenCode-specific overlay and secret-guard guidance.
- `AGENTS.md` — repo documentation for instruction architecture and supported agent surfaces.
- `scripts/sync_agent_stack.py` — generator for Codex and Copilot instruction mirrors; no source edit expected unless regeneration reveals a generator gap.
- `openspec/changes/improve-instruction-corpus/` — change-control artifacts for this work.

## Generated Outputs

- `instructions/codex-global.md` — generated mirror of `instructions/global.md` plus Codex suffix.
- `.github/copilot-instructions.md` — generated Copilot instruction output.
- Any repo-local instruction entrypoints refreshed by `uv run python scripts/sync_agent_stack.py --targets repo --apply`.

## Validation Commands

- `uv run python scripts/sync_agent_stack.py --targets repo --apply`
- `uv run python scripts/sync_agent_stack.py --targets repo --check`
- `uv run wagents validate`
- `uv run wagents openspec validate`
- `uv run wagents readme --check`
- `rg '@RTK\.md' instructions .github/copilot-instructions.md AGENTS.md`
- `rg 'OPENCODE_ALLOW_SECRET_FILES=1.*zshrc|zshrc.*OPENCODE_ALLOW_SECRET_FILES=1' instructions AGENTS.md .github/copilot-instructions.md`
