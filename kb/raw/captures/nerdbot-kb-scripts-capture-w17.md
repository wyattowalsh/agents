---
title: Nerdbot KB Scripts Capture W17
tags:
  - kb
  - raw
  - nerdbot
aliases:
  - Nerdbot scripts 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave17-pass2-2026-06-25
---

# Nerdbot KB Scripts Capture W17

Explicit listing of `skills/nerdbot/scripts/` on 2026-06-25.

| Script | Role |
|--------|------|
| `kb_inventory.py` | Layer/inventory report (`--root kb`) |
| `kb_lint.py` | Wiki/link/frontmatter lint (`--root kb --fail-on warning`) |
| `kb_bootstrap.py` | KB bootstrap helpers |
| `kb_path_policy.py` | Path policy checks |
| `check.py` | Skill portable validator entry |

## Invocation pattern

```bash
uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning
uv run python skills/nerdbot/scripts/kb_inventory.py --root kb
```

Package layout also includes `skills/nerdbot/src/` (ty-gated).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Script list | `ls skills/nerdbot/scripts/` | tool capture |
| Contract | `kb/raw/sources/nerdbot-runtime-contracts.md` | raw source note |