# Sync Workflow Rules

The repository uses `scripts/sync_agent_stack.py` and the `wagents` CLI to keep cross-platform assets, documentation, and harness configurations in sync. Manual edits to derived files are overwritten on the next sync.

## Pre-commit Validation

Before every commit that touches skills, agents, MCP servers, or harness configuration:

1. Run validation:
   ```bash
   wagents validate
   ```
   Fix any frontmatter or naming errors before proceeding.

2. Regenerate the README if the repo structure or asset inventory changed:
   ```bash
   wagents readme
   ```
   Do not hand-edit `README.md`; it is fully generated from repo contents.

3. Regenerate documentation if skills or agents changed:
   ```bash
   wagents docs generate
   ```
   Do not hand-edit generated MDX content pages under the docs site.

## Documentation Site Commands

| Command | Purpose |
|---------|---------|
| `wagents docs init` | One-time setup (`pnpm install` in `docs/`) |
| `wagents docs generate` | Generate MDX content pages |
| `wagents docs generate --include-installed` | Include installed skills from harness inventory |
| `wagents docs generate --include-drafts` | Include skills with TODO descriptions |
| `wagents docs dev` | Generate + launch dev server |
| `wagents docs build` | Generate + static build |
| `wagents docs preview` | Generate + build + preview server |
| `wagents docs clean` | Remove generated content pages |

## Modifying `sync_agent_stack.py`

This script propagates canonical repo state to multiple agent harnesses (Claude Code, Codex, Cursor, Gemini CLI / Antigravity, OpenCode, GitHub Copilot, etc.). It contains platform-specific logic for config paths, entrypoints, MCP registries, and hook registries.

### Rules when editing the sync script

- **Treat platform paths as immutable contracts.** Changing a path variable (e.g., `GEMINI_ANTIGRAVITY_MCP_PATH`, `CLAUDE_ENTRYPOINT_PATH`) changes where every user’s harness looks for config. Only change after verifying the target platform’s documented config location.
- **Preserve managed-file headers.** The script injects `<!-- Managed by scripts/sync_agent_stack.py. Do not edit directly. -->` into generated files. Do not remove or alter these markers; they signal to users that the file is derived.
- **Respect TOML/JSON ownership boundaries.** For Codex `config.toml`, the script owns specific top-level keys and tables listed in `CODEX_OWNED_TOP_LEVEL_KEYS` and `CODEX_OWNED_TABLES`. Do not expand ownership without testing against a live Codex installation.
- **Test with `--dry-run` first.** The script supports dry-run modes for many operations. Verify diff before applying changes to user home directories.
- **Add platform-specific logic in isolated blocks.** Keep per-platform path constants, config shapes, and write logic grouped together so regressions are scoped.

## CI/CD Automation

The `release-skills.yml` workflow runs `wagents validate` on every PR. It automatically packages and releases skills when a version tag (`v*.*.*`) is pushed. Validation failures block the release.

## Golden Rule

Repo policy and workflow truth lives in `AGENTS.md` and `instructions/global.md`. Generated artifacts (`README.md`, docs pages, harness configs, plugin manifests) are derived output. Regenerate them via the CLI rather than editing directly.
