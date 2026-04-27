---
name: Sync Script Debug
description: Debug sync_agent_stack.py issues — check platform paths, config merges, and idempotency failures.
---

## Task
Debug failures in `sync_agent_stack.py` by systematically checking platform paths, config file merges, and idempotency guarantees.

## Diagnostic Steps

1. **Locate the sync script**
   - Find `sync_agent_stack.py` in the repo root or `scripts/` directory
   - Check its Python version compatibility (3.12+ per repo conventions)
   - Verify it uses `uv run` or a valid shebang

2. **Platform path verification**
   - For each supported agent (Claude Code, Codex, Cursor, Gemini CLI, Antigravity, Copilot, OpenCode):
     - Check the target config directory exists (e.g., `~/.config/opencode/`, `~/.claude/`)
     - Verify write permissions
     - Confirm path resolution is absolute and handles `~` expansion correctly
   - Check for macOS vs Linux path differences (e.g., `~/Library/Application Support/` vs `~/.config/`)

3. **Config merge logic**
   - Identify which files are overwritten vs merged (skills, instructions, rules, plugins)
   - Check JSON/YAML merge behavior — does it deep-merge or replace?
   - Verify backup/rollback behavior before destructive writes
   - Look for hardcoded paths that may have changed in newer agent versions

4. **Idempotency check**
   - Run the script twice in succession with `--dry-run` if available
   - Compare outputs: second run should report "no changes" or zero diff
   - Check for timestamp-based non-determinism
   - Verify checksums or hashes are stable across runs

5. **Common failure modes**
   - Missing `skills` CLI (`npx skills` or `wagents` not in PATH)
   - Git branch dirty-check blocks sync unexpectedly
   - Platform-specific plugin manifests outdated (`.claude-plugin/`, `.codex-plugin/`)
   - Internal skills (`metadata.internal: true`) incorrectly excluded or included

## Output Format
Return a debug summary:
- **Root cause**: One-sentence diagnosis
- **Evidence**: Relevant log snippets, file diffs, or path listings
- **Fix**: Specific code change or command to resolve the issue
- **Prevention**: Recommendation to avoid recurrence (test, lint, or CI check)
