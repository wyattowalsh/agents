# OpenCode Plugins — Installation Notes

This directory contains manually-installed and npm-managed plugins for OpenCode.

## NPM-Managed Plugins (auto-installed via `opencode.json`)

These are declared in `../opencode.json` and installed automatically by OpenCode on restart:

| Plugin | Version | Purpose |
|--------|---------|---------|
| `opencode-handoff` | `^0.5.0` | Cross-session context transfer via `/handoff` |
| `open-plan-annotator` | `^1.3.0` | Browser-based plan annotation UI |
| `@mailshieldai/opencode-canvas` | `^0.1.2` | Interactive terminal canvases in tmux panes |
| `@kdcokenny/opencode-notify` | `^0.3.1` | Native OS notifications for OpenCode events |
| `@kdcokenny/opencode-background-agents` | `^0.1.1` | Async background task delegation |
| `@slkiser/opencode-quota` | `^3.3.0` | Real-time token quota tracking |

To update: edit versions in `../opencode.json` and restart OpenCode.

## Manually Installed Plugins

### Context Analysis Plugin

**Source:** `IgorWarzocha/Opencode-Context-Analysis-Plugin` (GitHub)
**Why manual:** Not published to npm; must be copied from the upstream repo.

**Files:**
- `command/context.md` — `/context` command definition
- `plugin/context-usage.ts` — Core plugin logic
- `plugin/tokenizer-aliases.json` — Model-to-tokenizer mappings
- `plugin/tokenizer-registry.d.ts` — Type declarations
- `plugin/tokenizer-registry.mjs` — Tokenizer resolution logic

**Dependencies:** `js-tiktoken`, `@huggingface/transformers` (listed in `package.json`)

**Update steps:**
1. Clone or download the latest release from `https://github.com/IgorWarzocha/Opencode-Context-Analysis-Plugin`
2. Copy the `.opencode/` contents into this directory, preserving the `command/` and `plugin/` subdirectories
3. Run `npm install` in this directory if `package.json` dependencies changed
4. Restart OpenCode

**Installed:** 2026-04-27
