---
title: Instructions Hierarchy Capture W08
tags:
  - kb
  - raw
  - instructions
  - harness
aliases:
  - Instructions hierarchy 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave08-platforms-2026-06-25
---

# Instructions Hierarchy Capture W08

Read-only inventory of `instructions/*` and harness instruction mirrors on 2026-06-25. Metadata only — no live home config paths read.

## Canonical fleet (`instructions/`)

| File | Bytes | Pattern | Role |
|------|-------|---------|------|
| `global.md` | 8158 | SSOT | Cross-platform operating rules (trust boundaries, OpenSpec, skills install) |
| `codex-global.md` | 9079 | **full generated copy** | Codex entrypoint; duplicates `global.md` body + Codex overrides (no `@` import) |
| `opencode-global.md` | 13088 | `@global` + overrides | OpenCode runtime/plugin/model policy (largest bridge) |
| `grok-global.md` | 4314 | `@global` + overrides | Grok config surfaces, LSP, subagent depth, Plannotator |
| `gemini-cli-global.md` | 1488 | `@global` + overrides | Gemini tool-efficiency and fleet dispatch |
| `copilot-global.md` | 963 | `@global` + overrides | Copilot fleet/model policy |
| `opencode-agents-overlay.md` | 3936 | overlay only | OpenCode-only agent frontmatter (`mode`, `temperature`, etc.) |
| `claude-code-global.md` | 105 | `@global` shim | Points active configs at `global.md` |

Five of six platform bridges import `global.md` via `@./instructions/global.md`. `codex-global.md` is the exception: sync generates a standalone file symlinked to `~/.codex/AGENTS.md`.

## Harness mirrors (downstream projections)

| Surface | Count | Notes |
|---------|-------|-------|
| `.github/instructions/*.instructions.md` | 14 | Copilot workspace instructions |
| `.apm/instructions/*.instructions.md` | 14 | APM package compile targets |
| `.cursor/rules/*.mdc` | includes `codex`, `grok`, `opencode` overlays | Cursor rule injection |
| `opencode.json` `instructions` array | 3 paths | `AGENTS.md`, `opencode-global.md`, `opencode-agents-overlay.md` |

APM materialization mapping (`wagents/apm.py`): `codex-global.md` → `codex.instructions.md`, `grok-global.md` → `grok.instructions.md`, `opencode-global.md` → `opencode.instructions.md`.

## Sync-manifest modes (selected)

| Path | Mode |
|------|------|
| `instructions/global.md` | symlink (home entrypoints) |
| `instructions/codex-global.md` | generated + symlink |
| `instructions/opencode-global.md` | generated |
| `instructions/grok-global.md` | canonical |
| `instructions/copilot-global.md` | canonical |

## Governance hooks

- Instruction changes affecting public asset formats, downstream tooling, generated docs, or sync behavior require OpenSpec (`instructions/global.md`, `AGENTS.md`).
- OpenCode model-neutral policy lives in `opencode-global.md` — repo-managed config must not add model selectors to agent frontmatter; overlay keys isolated to `opencode-agents-overlay.md`.
- Grok subagent depth hard-capped at **1** in `grok-global.md`; env-only toggles documented via `config/grok-env.sh`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| File sizes and import patterns | `instructions/*.md` | canonical repo paths |
| Mirror counts | `.github/instructions/`, `.apm/instructions/` | canonical repo paths |
| Sync modes | `config/sync-manifest.json` | canonical repo path |
| APM compile mapping | `wagents/apm.py` | canonical repo path |