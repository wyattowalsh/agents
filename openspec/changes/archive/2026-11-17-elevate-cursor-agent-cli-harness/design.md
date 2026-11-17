# Design: Elevate Cursor Agent CLI

## Decisions

1. **Harness id:** `cursor-cli`. Binaries: `agent`, `cursor-agent`.
2. **Three-list discipline:**
   - `harness-surface-registry.json` — elevate existing `cursor-cli` row.
   - harness-master `SUPPORTED_HARNESSES` — add `cursor-cli`; remap CLI aliases.
   - `site_model.SUPPORTED_AGENTS` — unchanged (`cursor` only).
3. **Shared SSOT:** rules, hooks.json, MCP, skills, agents stay rendered by
   `wagents/platforms/cursor.py` with hook-registry harness id `cursor`.
4. **Hook-surface vs render:** add a `cursor-cli` hook-surface consumer row
   pointing at the same files. Do not render hooks twice.
5. **CLI-only:** project `.cursor/cli.json` (permissions only, already
   generated); global `cli-config.json` is user-owned (doctor key presence
   only). New instruction overlay + thin rule pointer + doctor.
6. **Plugins:** document `--plugin-dir` and `agent plugin marketplace`.
   Marketplace add is operator-opt-in, never sync.
7. **ACP / worker / worktrees:** document and cite existing `cursor-acp`.
   Do not merge those rows into `cursor-cli`.
8. **Support tier:** keep `validated` only if W3 fixtures cover the expanded
   surfaces; otherwise temporarily `repo-present-validation-required`.
9. **Doctor:** read-only JSON/text; never print email, tokens, or API keys.

## Research lock

Official docs 2026-08-16 (`cursor.com/llms.txt` + CLI pages) and local
`agent` 2026.08.11-e8db854: CLI loads AGENTS.md / CLAUDE.md / `.cursor/rules`,
project+user `hooks.json` and plugin hooks, shared MCP/skills, CLI permissions
in project `cli.json`, remaining CLI settings in `~/.cursor/cli-config.json`.
Sync SHALL NOT write `cli-config.json`.

If later smoke shows project `hooks.json` is ignored in CLI, demote the hook
claim to plugin-hooks only. Do not duplicate hook files.
