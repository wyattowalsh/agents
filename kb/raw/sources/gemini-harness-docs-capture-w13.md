---
title: Gemini Harness Docs Capture W13
tags:
  - kb
  - source
  - external
  - gemini
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave13-gap-sweep-2026-06-25
---

# Gemini Harness Docs Capture W13

| Field | Value |
|-------|-------|
| source_id | `gemini-harness-docs-capture-w13` |
| original_location | `https://github.com/google-gemini/gemini-cli`; `GEMINI.md` bridge in repo root |
| capture_method | official repo pointer + repo bridge read |
| captured_at | 2026-06-25 |

## Summary

Gemini CLI is the official Google terminal agent with MCP support, `GEMINI.md` context files, and non-interactive mode. This repo bridges via root `GEMINI.md` → `@./AGENTS.md` → `@instructions/global.md`, sharing the Antigravity instruction path. Skills install target: `make install-gemini` / `npx skills add ... -a gemini-cli`.

## Repo alignment

| Upstream | Repo surface |
|----------|--------------|
| `GEMINI.md` context | Root `GEMINI.md` import bridge |
| MCP | MCPHub projection via registry (not duplicate Chrome plugin owner) |
| Skills | Skills CLI `gemini-cli` adapter |

## Provenance

| Claim | Source |
|-------|--------|
| URL + GEMINI bridge | `kb/raw/sources/external-harness-docs.md`; `GEMINI.md` |