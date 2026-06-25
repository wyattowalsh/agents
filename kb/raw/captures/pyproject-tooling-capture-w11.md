---
title: Pyproject Tooling Capture W11
tags:
  - kb
  - raw
  - ruff
  - ty
  - uv
aliases:
  - Pyproject tooling 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave11-gap-sweep-2026-06-25
---

# Pyproject Tooling Capture W11

Read-only capture from `pyproject.toml` on 2026-06-25. Aligns repo gates with upstream Ruff/ty/uv configuration semantics documented in `external-tooling-docs`.

## Ruff (`[tool.ruff]`)

| Setting | Value |
|---------|-------|
| `target-version` | `py313` |
| `line-length` | `120` |
| `required-version` | `>=0.11` |
| `preview` | `true` |
| `include` | `wagents/**`, `tests/**`, `scripts/**`, `skills/**/scripts/**`, `skills/nerdbot/src/**`, `hooks/wagents-hook.py` |
| `extend-exclude` | `mcp/**`, `skills/**/evals/**` |
| `select` | `E`, `F`, `I`, `UP`, `B`, `SIM`, `C4`, `RUF`, `TC`, `PT`, `RET` |
| Notable per-file ignores | `scripts/validate/**` → `E402`; `skills/**/scripts/**` → `E402`, `E501`, … |

CI runs: `uv run ruff check` and `uv run ruff format --check` (`.github/workflows/ci.yml` lint job).

## Ty (`[tool.ty]`)

| Setting | Value |
|---------|-------|
| `environment.python-version` | `3.13` |
| `environment.root` | `[".", "skills/nerdbot/src"]` |
| `environment.extra-paths` | `skills/skill-creator/scripts`, `skills/nerdbot/scripts` |
| `analysis.allowed-unresolved-imports` | `audit`, `progress`, `package`, `asset_toolkit.**`, `kb_bootstrap`, `kb_inventory`, `kb_lint` |
| `src.include` | `wagents`, `scripts`, `tests`, `skills/nerdbot/src`, `skills/nerdbot/scripts` |
| `src.exclude` | `scripts/validate/**`, `tests/docs_ui/**` |
| `overrides` | `tests/**` → `possibly-unresolved-reference = warn` |
| `terminal.error-on-warning` | `true` |
| Dev pin | `ty==0.0.52` in `[dependency-groups] dev` |

CI runs: `uv run ty check --output-format github --no-progress` (typecheck job).

## uv workspace

| Setting | Value |
|---------|-------|
| `[tool.uv.workspace].members` | `["mcp/mcphub"]` |

## Upstream mapping

| Repo choice | Upstream doc anchor |
|-------------|---------------------|
| Scoped `include`/`extend-exclude` | Ruff `include` must match files not directories |
| `allowed-unresolved-imports` globs | ty `analysis.allowed-unresolved-imports` module patterns |
| `requires-python >=3.13` | ty infers `python-version` from `project.requires-python` when unset |

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Ruff/ty tables | `pyproject.toml` | canonical repo |
| CI command pairing | `.github/workflows/ci.yml` | canonical repo |
| Upstream semantics | `https://docs.astral.sh/ruff/configuration/`; `https://docs.astral.sh/ty/reference/configuration/` | external docs |