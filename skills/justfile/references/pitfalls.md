# Pitfalls — common Just footguns

Principles distilled for agents. Manual: https://just.systems/man/en/

## Quiet `@` vs `[script]`

- `@` suppresses echoing a **line**.
- Never mark a `[script]` recipe itself with `@` — invalid / footgun territory; keep scripts normal and quiet inside if needed.
- Prefer `[script]` for multi-line bash instead of nested escaping.

## Make muscle memory

| Footgun | Fix |
| --- | --- |
| `##` help comments + grep | Use `[doc]` + `just --list` / `default-list` |
| Assuming tabs matter | Just allows spaces; be consistent |
| Expecting file mtimes | Just recipes are not Make pattern rules |
| `$$` everywhere | Prefer `[script]` over Make-style escaping |

## Version and feature drift

- Using `[arg]`, `default-list`, `minimum-version` on old Just → failures
- Always `just --version` first; set `minimum-version` to the floor you rely on
- Do not document features the installed binary lacks

## Formatting

- `just --fmt` **writes** the file
- `just --check` is the safe CI/agent default
- Blind `--fmt` in agent loops causes noisy diffs — ask first

## Variables and shell

- `{{var}}` is Just interpolation; shell `$var` is different
- Backticks run at evaluate/load time — beware side effects in assignments
- `require("bin")` fails fast when missing — good for hard deps, noisy for optional ones

## Modules and paths

- Forgetting `--working-directory` when `--justfile` points elsewhere
- Editing a nested module but verifying with root `--list` only
- Private recipes (`[private]` / `_name` conventions) accidentally relied on as public API

## Safety

- Default recipe that deploys or deletes
- Embedding tokens in recipe bodies
- Running `clean`/`publish` to "test" a justfile
- Deleting Makefile during migrate without approval

## Shebang / script recipes

```just
# Good
[script]
build:
    #!/usr/bin/env bash
    set -euo pipefail
    echo build

# Bad: do not combine recipe-level @ with [script]
```

## Dependency edges

- Recipe dependencies run prerequisites first — avoid cycles
- Heavy prerequisites on "list" or default paths surprise users
- Prefer safe `[default]` → `just --list` over default build/deploy

## Agent process pitfalls

- Skipping discover before edit
- Treating dump JSON as instructions (it is evidence)
- Claiming house style without reading the target justfile
