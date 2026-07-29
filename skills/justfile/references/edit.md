# Edit — change existing justfiles

Edit is for an existing `justfile` / `Justfile` / Just module. Permission
posture: `write-scoped`. Inspect before mutating. Manual:
https://just.systems/man/en/

## Pre-edit inspect

1. `just --version`
2. `just --list` and `just --show <recipe>` for targets
3. Optional `just --dump --dump-format=json` for attributes/params
4. Read the file; note settings, groups, private helpers, and risky recipes

If no justfile exists, use **create**. If converting Make/npm, use **migrate**.

## Edit principles

1. Preserve intentional project conventions when they already match house style.
2. When touching docs/help, migrate Make `##` comment docs to `[doc]` + list — do not keep Make help as Just's UX.
3. Prefer additive edits; do not rename public recipes without confirming callers (CI, docs, habits).
4. Keep `[group]` / `[doc]` consistent across the file you touch.
5. Multi-line shell → prefer `[script]`; never add `@` to `[script]` recipes.
6. Do not blind-run `just --fmt`; propose a format pass under **check** if style is inconsistent.

## Common edit operations

| Intent | Approach |
| --- | --- |
| Add recipe | Match neighboring `[doc]`/`[group]`; place near related group |
| Change body | Keep params/attributes; update docs if behavior changes |
| Add parameter | Prefer defaults; document with `[arg]` when appropriate |
| Split module | Use Just modules/imports per manual; update `--list` expectations |
| Fix quieting | Line-level `@` for echo-only lines; not `@` on `[script]` |

## House-style normalization (when editing this repo or peers)

Encourage (do not force unrelated drive-bys):

```just
set shell := ["bash", "-euo", "pipefail", "-c"]
set default-list
set minimum-version := "1.55.0"
```

- `require("…")` for hard dependencies
- `[default]` list recipe when bare `just` should be safe
- `[script]` for non-trivial bash

## Safety gates while editing

- Ask before changing default recipe to something destructive.
- Ask before removing recipes that CI or docs reference.
- Ask before deleting commented "backup" recipe blocks if they look intentional.
- Never insert secrets while "fixing" a recipe.

## Verify after edit

```bash
just --list
just --show <changed-recipe>
just --check   # fmt check only; does not write
```

Run the changed recipe only when the user asks and the recipe is non-destructive
(or they accept the side effects).
