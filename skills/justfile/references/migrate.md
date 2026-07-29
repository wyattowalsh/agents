# Migrate — Makefile / npm scripts → just

Migrate task runners into Just. Distill principles only. Manual:
https://just.systems/man/en/

## Gate before destructive cutover

1. Inventory sources (Makefile, `package.json` scripts, other task files).
2. Produce a mapping table (old → new recipe) and show it to the user.
3. Write the justfile (or update it) **before** deleting sources.
4. Ask explicitly before deleting Makefile / removing npm scripts.
5. Do not run migrated deploy/publish recipes during migration.

Permission posture: `write-scoped` for justfile writes; deletion is
ask-first / side-effect gated.

## Mapping cheat sheet

| Source | Just |
| --- | --- |
| Make `.PHONY` | Unnecessary (recipes are not file targets by default) |
| Make `.DEFAULT_GOAL` | `[default]` recipe and/or first recipe + `default-list` |
| Make `##` help / grep help | `[doc("…")]` + `just --list` / `default-list` |
| Make `$(VAR)` | `{{var}}` |
| Make `$(shell cmd)` | `` `cmd` `` backtick recipe deps / assignments |
| Make tabs | Spaces OK in Just |
| npm `scripts.test` | `test:` recipe calling the same command |
| File-timestamp Make builds | Often **not** a Just migration — see when-not-just.md |

## Migration workflow

1. `just --version` on the target machine.
2. Parse Makefile targets or `package.json` scripts into an inventory.
3. Classify each item: task recipe (migrate), file build (maybe keep Make), CI-only (leave to devops-engineer), dangerous (migrate with strong docs + no auto-run).
4. Scaffold house-style settings (`shell`, `default-list`, `minimum-version`).
5. Create recipes with `[doc]` / `[group]`; prefer `[script]` for multi-line.
6. `just --list` and spot-check `--show`.
7. Only after user approval: remove or shrink legacy files.

## npm scripts notes

- Keep `package.json` scripts if other tools require them; Just can call `npm run …` or invoke the underlying binary directly.
- Prefer calling `uv` / `pnpm` / project CLIs directly when that matches house style.
- Avoid duplicating divergent logic in both places without a stated source of truth.

## Makefile pitfalls to leave behind

- Do not reimplement Make's `##` help grep in Just.
- Do not treat Just as a Make replacement for pattern rules and precise mtimes.
- Do not quiet `[script]` with `@`.
- Do not copy Make's `$$` escaping blindly — Just recipe shell rules differ; prefer `[script]`.

## Example skeleton after Makefile task migration

```just
set shell := ["bash", "-euo", "pipefail", "-c"]
set default-list
set minimum-version := "1.55.0"

[default]
[doc("List available recipes")]
default:
    @just --list

[doc("Run unit tests")]
[group("checks")]
test:
    uv run pytest
```

## Done criteria

- Mapping table reviewed
- `just --list` shows migrated tasks with docs
- Legacy deletion only if user approved
- No secrets copied from old scripts into the justfile
