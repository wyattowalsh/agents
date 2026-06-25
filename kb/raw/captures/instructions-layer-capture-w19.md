---
title: Instructions Layer Capture W19
tags:
  - kb
  - raw
  - instructions
aliases:
  - Instructions layer 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave19-pass3-2026-06-25
---

# Instructions Layer Capture W19

Explicit-path inventory of `instructions/` on 2026-06-25 (pass 3 wave 19).

## File count

Eight Markdown files:

| File | Role |
|------|------|
| `global.md` | Canonical cross-platform SSOT |
| `claude-code-global.md` | Claude compatibility overlay |
| `codex-global.md` | Codex overlay; generated mirror target |
| `copilot-global.md` | Copilot fleet/orchestration overlay |
| `gemini-cli-global.md` | Gemini tool-efficiency overlay |
| `grok-global.md` | Grok config/env/plannotator overlay |
| `opencode-global.md` | OpenCode model/plugin/DCP overlay |
| `opencode-agents-overlay.md` | OpenCode-only agent runtime keys |

## Bridge pattern

Platform overlays import `@./instructions/global.md` where supported. Claude `.claude/rules/` duplicates policy without `@` imports for native scoped-rule loading. Copilot projects generated `.github/copilot-instructions.md` from `copilot-global.md`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Eight instruction files | `ls instructions/*.md` | tool output |
| SSOT precedence | `instructions/global.md` | canonical repo |
| Prior hierarchy capture | `kb/raw/captures/instructions-hierarchy-capture-w08.md` | raw capture |