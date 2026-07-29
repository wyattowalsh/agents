# Patterns — house-style Just recipes

Patterns mirror this repository's root `justfile`. Link:
https://just.systems/man/en/

## Settings block

```just
set shell := ["bash", "-euo", "pipefail", "-c"]
set default-list
set minimum-version := "1.55.0"
```

Optional when the project already uses dotenv:

```just
set dotenv-load
```

## Required tools

```just
npx := require("npx")
uv := require("uv")
```

Use `require` for hard dependencies. For optional tools, check in-recipe and
print an install hint instead of failing parse.

## Safe default

```just
[default]
[doc("List available recipes")]
default:
    @just --list
```

Bare `just` should be safe. Pair with `set default-list`.

## Documented grouped recipes

```just
[doc("Lint Python code")]
[group("checks")]
lint:
    uv run ruff check

[doc("Run test suite")]
[group("checks")]
test:
    uv run pytest
```

## Long CLI args

When Just version supports it:

```just
[arg("agent", long, pattern="^[a-z0-9][a-z0-9-]*$", help="Harness id")]
[doc("Install skills to one agent")]
[group("install")]
install-agent:
    npx -y skills add {{repo}} --skill '*' -a "{{agent}}" -g -y
```

Confirm with `just --version` before relying on `[arg]`.

## Multi-line `[script]`

```just
[script]
[doc("Smoke a local service")]
[group("checks")]
smoke:
    #!/usr/bin/env bash
    set -euo pipefail
    curl -fsS "http://127.0.0.1:46683/health" >/dev/null
    echo "ok"
```

No recipe-level `@` on `[script]`.

## Variadic passthrough

```just
[doc("Run pytest with optional args")]
[group("checks")]
test *args="":
    uv run pytest {{args}}
```

## Composition with dependencies

```just
[doc("Lint, format-check, and type-check")]
[group("checks")]
check-python: lint format typecheck
```

Keep dependency graphs shallow and obvious.

## Platform attributes

```just
[macos]
[doc("macOS-only setup hint")]
[group("setup")]
setup-hints:
    @echo "use brew for native deps"
```

## Private helpers

```just
[private]
_assert-uv:
    @command -v uv >/dev/null
```

Do not publish helpers in the public gallery without need.

## Anti-pattern: Make help paste

Do not add:

```just
# help: ## bad Make style
```

Use `[doc]` + list instead.

## Choosing a pattern quickly

| Need | Pattern |
| --- | --- |
| Safe bare `just` | `[default]` + `default-list` |
| Multi-line bash | `[script]` |
| Grouped UX | `[group]` + `[doc]` |
| Hard binary | `require("…")` |
| Optional args | `*args=""` |
| Format CI | `just --check` (not `--fmt`) |
