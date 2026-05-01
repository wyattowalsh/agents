---
title: Instructions Hierarchy
tags:
  - kb
  - source
  - instructions
aliases:
  - Instruction source hierarchy
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Instructions Hierarchy

## Source Record

| Field | Value |
|-------|-------|
| source_id | `instructions-hierarchy` |
| original_location | `AGENTS.md`; `instructions/global.md`; `instructions/opencode-global.md`; platform bridge files under `instructions/`; `.github/copilot-instructions.md`; `GEMINI.md`; `opencode.json` |
| raw_path | `kb/raw/sources/instructions-hierarchy.md` |
| capture_method | repo-local pointer summary from read-only inspection |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local canonical and generated material |
| intended_wiki_coverage | [[canonical-generated-surfaces]], [[harness-and-platform-sync]], [[opencode-runtime-policy]] |

## Summary

`instructions/global.md` is the canonical cross-platform instruction source. Platform-specific files in `instructions/` import or adapt it where a harness needs different runtime guidance. `AGENTS.md` is the repo-local standards entrypoint used by multiple harnesses. Some downstream surfaces, such as `.github/copilot-instructions.md`, are generated or mirrored from platform-specific sources.

Instruction changes can affect many harnesses and should use OpenSpec when they change public asset formats, downstream tooling, generated docs, sync behavior, validation behavior, or coordinated surfaces. Keep model selection out of repo-managed OpenCode config and agents unless explicitly requested.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `instructions/global.md` is the canonical shared instruction source. | `AGENTS.md`; `instructions/global.md` | canonical material | Platform files layer on top. |
| Some harness instruction surfaces are generated mirrors. | `config/sync-manifest.json`; `.github/copilot-instructions.md` | canonical/generated material | Do not hand-edit generated surfaces without sync context. |
| OpenSpec is required for non-trivial workflow/tooling/instruction behavior changes. | `instructions/global.md`; `AGENTS.md`; `openspec/config.yaml` | canonical material | Reinforces governance. |
