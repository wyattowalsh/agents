---
title: Developer Commands Extract
tags:
  - kb
  - raw
  - commands
aliases:
  - Commands extract
kind: source-summary
status: active
updated: 2026-05-01
source_count: 4
---

# Developer Commands Extract

## Verified Command Sources

| Command | Source | Notes |
|---------|--------|-------|
| `uv run wagents validate` | `justfile`; `README.md`; `AGENTS.md` | Skill and agent validation. |
| `uv run pytest` | `justfile` | Test suite. |
| `uv run ruff check` | `justfile` | Python lint recipe. |
| `uv run ty check` | `justfile`; `pyproject.toml` | Type-check recipe with Ty config discovery. |
| `uv run wagents readme --check` | `README.md`; `AGENTS.md`; `openspec/config.yaml` | Generated README freshness. |
| `uv run wagents docs generate` | `README.md`; `AGENTS.md`; `openspec/config.yaml` | Generated docs pages. |
| `uv run wagents openspec validate` | `justfile`; `README.md`; `openspec/config.yaml` | OpenSpec validation. |
| `uv run --project skills/nerdbot nerdbot inventory --root ./kb` | `skills/nerdbot/README.md` | KB inventory. |
| `uv run --project skills/nerdbot nerdbot lint --root ./kb --include-unlayered` | `skills/nerdbot/README.md`; loaded Nerdbot skill contract | KB lint including adjacent Markdown participation. |
