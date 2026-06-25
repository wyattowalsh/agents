---
title: Skill Creator Scripts Capture W19
tags:
  - kb
  - raw
  - skills
aliases:
  - Skill creator scripts 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave19-pass3-2026-06-25
---

# Skill Creator Scripts Capture W19

Inventory of `skills/skill-creator/scripts/` on 2026-06-25.

## Layout

| Path | Role |
|------|------|
| `audit.py` | Quality scoring (target ≥80) |
| `check.py` | Per-skill portable validator entry |
| `package.py` | ZIP packaging helper |
| `scaffold_skill.py` | `wagents new skill` backend |
| `verify.py` | Post-scaffold verification |
| `generate_check.py` | Check script generator |
| `asset_toolkit/validate_skill.py` | Fallback portable validator |
| `asset_toolkit/validate_hooks.py` | Hook schema checks |
| `asset_toolkit/validate_evals.py` | Eval manifest checks |

## Validation chain

1. `uv run python skills/<name>/scripts/check.py` when present
2. Else `uv run python skills/skill-creator/scripts/asset_toolkit/validate_skill.py skills/<name>`
3. `uv run python skills/skill-creator/scripts/audit.py <skill-name>` for score gate

## Counts

- **14** Python files under `skills/skill-creator/scripts/` (including templates and `_shared.py`)
- **56** skill directories at repo root

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Script roles | `skills/skill-creator/scripts/` listing | repo evidence |
| Audit threshold | `.claude/rules/skill-validation.md` | scoped rule |