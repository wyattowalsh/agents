# Affected Surfaces

## Source Of Truth

- `skills/chrome-devtools*/SKILL.md` and references - repo-adapted Chrome DevTools skill inventory and provenance.
- `config/plugin-extension-registry.json` - per-harness source ownership for plugin, extension, repo MCP, manual UI, or blind spot status.
- `config/mcp-registry.json` - canonical MCP server definition and hardened launch environment.
- `scripts/sync_agent_stack.py` - harness projection and dedupe behavior for plugin-managed Chrome DevTools sources if required.
- `config/skill-registry-policy.json` or external-skill evaluation metadata - allowlist/provenance for imported Chrome DevTools skills.
- `AGENTS.md` and `instructions/opencode-global.md` - shared Chrome DevTools MCP defaults and OpenCode wrapper override.
- `openspec/changes/integrate-chrome-devtools-skills/` - change-control artifacts for this integration.

## Generated Outputs

- `README.md` from `uv run wagents readme`.
- Docs generated content from `uv run wagents docs generate` or the `docs-steward` workflow.
- Harness config outputs produced by `scripts/sync_agent_stack.py` or related sync commands, only after source-of-truth changes are complete.

## Downstream Agent Artifacts

- Claude Code plugin marketplace entry and plugin install state for `ChromeDevTools/chrome-devtools-mcp`.
- Gemini CLI extension install state from `https://github.com/ChromeDevTools/chrome-devtools-mcp` with auto-update enabled.
- VS Code and GitHub Copilot source plugin path where supported by the harness.
- Codex, OpenCode, Cursor, Claude Desktop, ChatGPT, Antigravity, Perplexity Desktop, and Cherry Studio repo MCP or manual UI import surfaces.
- Existing OpenCode Chrome DevTools wrapper at `/Users/ww/.config/opencode/tools/chrome-devtools-launcher.sh` remains a local override, not a shared repo default.

## Tests

- Skill frontmatter and catalog validation.
- External skill provenance and policy validation.
- MCP registry validation.
- Sync stack tests covering one active `chrome-devtools` source per harness.
- Package portability dry run for the promoted skills.

## Validation Commands

- `uv run wagents openspec validate`
- `uv run wagents validate`
- `uv run wagents eval validate`
- `uv run python skills/skill-creator/scripts/audit.py skills/chrome-devtools`
- `uv run python skills/skill-creator/scripts/package.py --all --dry-run --format table`
- `uv run python scripts/check_agent_stack.py`
- `uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level both --harness claude-code claude-desktop chatgpt codex github-copilot-web github-copilot-cli opencode gemini-cli antigravity perplexity-desktop cherry-studio cursor`
- `npx -y chrome-devtools-mcp@latest --help`
- `git diff --check`
