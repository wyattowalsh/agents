# Skill Portability Contract

Portable skills must validate with bundled `scripts/asset_toolkit/` and `scripts/check.py`
without reaching into sibling skills or the repo `wagents` CLI.

## P5 — Bundled toolkit

Each skill ships copies of:

- `scripts/asset_toolkit/validate_skill.py`
- `scripts/asset_toolkit/validate_evals.py`
- `scripts/asset_toolkit/package.py`
- `scripts/asset_toolkit/_shared.py`

Sync source: `skills/skill-creator/scripts/sync_asset_toolkit.py`.

## P6 — Portable CI mode

When `SKILL_PORTABLE_CI=1` (or `PORTABLE_CI=1`):

- `check.py` must use bundled toolkit only (no sibling `skill-creator` fallback).
- `package.py --dry-run` runs via bundled `asset_toolkit/package.py`.
- Repo-only `audit.py` is skipped.

## P7 — Body operator paths

Outside fenced code blocks, SKILL.md prose must reference skill-local scripts as
`scripts/<file>` — never `skills/<name>/scripts/<file>`.

Enforced by `find_nonportable_body_operator_lines()` in `_shared.py`.
