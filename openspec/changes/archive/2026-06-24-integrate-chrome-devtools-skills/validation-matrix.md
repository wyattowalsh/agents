# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec | `uv run wagents openspec validate` | Pass | Requires scaffold plus Markdown artifacts to be valid. |
| Asset validation | `uv run wagents validate` | Pass | Validates promoted skill and agent frontmatter. |
| Evaluation metadata | `uv run wagents eval validate` | Pass | Validates repo evaluation metadata after external intake updates. |
| Primary Chrome skill audit | `uv run python skills/skill-creator/scripts/audit.py skills/chrome-devtools` | Pass or actionable findings only | Run additional audits for each promoted `skills/chrome-devtools*` directory if the script accepts one path at a time. |
| Skill portability | `uv run python skills/skill-creator/scripts/package.py --all --dry-run --format table` | Pass | Ensures promoted skills can be packaged. |
| Agent stack | `uv run python scripts/check_agent_stack.py` | Pass | Detects sync/config regressions. |
| Harness surfaces | Run `uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level both --harness <harness>` once for each target harness | No unexpected missing source-of-truth surfaces | `<harness>` is one of `claude-code`, `claude-desktop`, `chatgpt`, `codex`, `github-copilot-web`, `github-copilot-cli`, `opencode`, `gemini-cli`, `antigravity`, `perplexity-desktop`, `cherry-studio`, or `cursor`. Blind spots should remain documented, not silently treated as configured. |
| MCP package | `npx -y chrome-devtools-mcp@latest --help` | Help output exits successfully | Confirms package can be resolved and CLI remains available. |
| README | `uv run wagents readme --check` | Pass after regeneration | Expected to fail before generated docs are refreshed if skill catalog changes. |
| Docs | `uv run wagents docs generate` then docs health checks if available | Generated docs include promoted skills | Run through `docs-steward` after skill definitions change. |
| Whitespace | `git diff --check` | Pass | Catches trailing whitespace and patch issues. |

## Blockers

- Plan mode currently prevents creating non-Markdown OpenSpec scaffold files and implementation/config edits.

## Deferred Checks

- Do not commit runtime traces, screenshots, Lighthouse reports, heap snapshots, or browser profile data generated while testing Chrome DevTools workflows.
- Do not claim plugin ownership for Cursor, Codex, OpenCode, Antigravity, Claude Desktop, ChatGPT, Perplexity Desktop, or Cherry Studio unless verified by a concrete harness surface.
- Do not change the OpenCode wrapper unless a test shows it is incompatible with the upstream package.
