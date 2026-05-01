# Tasks

## OpenSpec And Intake

- [x] Create the OpenSpec scaffold for `integrate-chrome-devtools-skills`, including `.openspec.yaml`, once non-Markdown edits are allowed.
- [x] Record upstream provenance for `ChromeDevTools/chrome-devtools-mcp` commit `a90378adf3226e8b27a05cdcfdd801c199acaa93`, package version `0.23.0`, author `Google LLC`, and license `Apache-2.0`.
- [x] Capture external-source evidence from `npx skills add github:ChromeDevTools/chrome-devtools-mcp --list` in the external skill evaluation or policy metadata.
- [x] Inspect upstream skill content for scripts, references, absolute paths, install side effects, telemetry behavior, and output artifacts before promotion.

## Skill Promotion

- [x] Add `skills/chrome-devtools/SKILL.md` from the upstream `chrome-devtools` skill with repo-safe provenance and safety notes.
- [x] Add `skills/chrome-devtools-cli/SKILL.md` from the upstream `chrome-devtools-cli` skill with explicit install/run guardrails.
- [x] Add `skills/chrome-devtools-a11y-debugging/SKILL.md` from upstream `a11y-debugging`.
- [x] Add `skills/chrome-devtools-debug-optimize-lcp/SKILL.md` from upstream `debug-optimize-lcp`.
- [x] Add `skills/chrome-devtools-memory-leak-debugging/SKILL.md` from upstream `memory-leak-debugging`.
- [x] Add `skills/chrome-devtools-troubleshooting/SKILL.md` from upstream `troubleshooting`.
- [x] Add references or provenance files for each promoted skill when useful, keeping runtime artifacts out of version control.
- [x] Run skill audits and resolve blocking findings without weakening repo skill standards.

## Plugin And MCP Integration

- [x] Add Chrome DevTools plugin/extension ownership metadata to `config/plugin-extension-registry.json` for Claude Code, Gemini CLI, and VS Code/GitHub Copilot where supported.
- [x] Record `repo-mcp`, `manual-ui`, or `blind-spot` ownership for Codex, OpenCode, Cursor, Antigravity, Claude Desktop, ChatGPT, Perplexity Desktop, and Cherry Studio.
- [x] Harden `config/mcp-registry.json` with supported no-usage-statistics and no-update-check settings while preserving the current headed persistent-profile launch.
- [x] Decide and implement the repo policy for `--no-performance-crux` based on current package support and desired privacy behavior.
- [x] Preserve the OpenCode local wrapper override in `instructions/opencode-global.md` and any sync logic that writes live OpenCode config.
- [x] Add or update sync logic so plugin-managed or extension-managed harnesses do not also receive an active standalone `chrome-devtools` repo MCP entry.

## Documentation And Catalogs

- [x] Update `AGENTS.md` with the Chrome DevTools plugin/extension/source ownership invariant and MCP hardening notes.
- [x] Update OpenCode-specific instructions only as needed to preserve the wrapper and avoid duplicate Chrome DevTools MCP ownership.
- [x] Update external skill intake documentation or registry policy with the upstream Chrome DevTools source and install commands.
- [x] Regenerate README and docs catalogs after skill promotion.
- [x] Invoke `docs-steward` after skill definitions or docs catalogs change.

## Verification

- [x] Run `uv run wagents openspec validate`.
- [x] Run `uv run wagents validate`.
- [x] Run `uv run wagents eval validate`.
- [x] Run `uv run python skills/skill-creator/scripts/audit.py skills/chrome-devtools` and equivalent audits for the other promoted Chrome DevTools skills if needed.
- [x] Run `uv run python skills/skill-creator/scripts/package.py --all --dry-run --format table`.
- [x] Run `uv run python scripts/check_agent_stack.py`.
- [x] Run the harness surface discovery command from `validation-matrix.md`.
- [x] Run `npx -y chrome-devtools-mcp@latest --help`.
- [x] Run `git diff --check`.
