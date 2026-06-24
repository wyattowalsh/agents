# Affected Surfaces

## Source Of Truth

- `opencode.json` - repo-managed OpenCode runtime plugin and provider config.
- `openspec/changes/add-opencode-plugins-golang-skills/` - change-control artifacts.

## User-Owned Global Surfaces

- `~/.config/opencode/opencode.json` - live global OpenCode runtime plugin and provider config.
- `~/.config/opencode/tui.json` - live TUI plugin registration for `opencodeBar`.
- `~/.config/opencode/opencode-bar.json` - live TUI plugin tuning.
- `~/.local/share/opencode/plugins/opencode-bar/` - stable local source checkout for `opencodeBar`.

## External Sources

- `https://github.com/samber/cc-skills-golang`
- `https://github.com/nghyane/opencode-plugin-notebooklm`
- `https://github.com/ghoulr/opencode-websearch-cited`
- `https://github.com/rapidrabbit76/OpenCodeInsights`
- `https://github.com/Icicno/opencodeBar`
- `https://github.com/anis-dr/opencode-mermaid-renderer`

## Validation Commands

- `npx skills add https://github.com/samber/cc-skills-golang --list`
- `npx skills add https://github.com/samber/cc-skills-golang --all -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode`
- `npx skills add https://github.com/nghyane/opencode-plugin-notebooklm --skill nlm-index -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode`
- `opencode --version`
- `bun --version`
- `uv run wagents openspec validate`
