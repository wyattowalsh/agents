# Create — new justfiles and recipes

House style = this repository's root `justfile`. Distill casey principles; do
not vendor third-party skill prose. Manual: https://just.systems/man/en/

## Opt-in gate (required before write)

Ask / confirm all of the following that apply:

1. **Target path** — `justfile` vs `Justfile` vs nested module path.
2. **Overwrite** — refuse silent overwrite of an existing justfile.
3. **Scope** — greenfield file vs append recipes to an existing file (prefer **edit** for appends).
4. **Side effects** — any recipe that deletes, deploys, publishes, or hits the network needs explicit user intent later; do not auto-run them after create.
5. **Toolchain** — which binaries must be `require()`'d vs optional.

If the user only wants discovery, switch to **discover**. If they already have
a justfile, switch to **edit**.

Permission posture remains `write-scoped`: write the file after the gate; do
not run mutating recipes unless the user explicitly asks.

## Scaffold template (house baseline)

```just
set shell := ["bash", "-euo", "pipefail", "-c"]
set default-list
set minimum-version := "1.55.0"

# uv := require("uv")  # uncomment hard deps

[default]
[doc("List available recipes")]
default:
    @just --list

[doc("Example check recipe")]
[group("checks")]
check:
    @echo "ok"
```

## Creation rules

1. Run `just --version` first; set `minimum-version` to a floor the environment supports (prefer `1.55.0`).
2. Set `shell` to bash with `-euo pipefail` unless the project standard differs.
3. Provide `[default]` + `default-list` so bare `just` lists safely.
4. Document recipes with `[doc("…")]`; group with `[group("…")]`.
5. Prefer `[script]` for multi-line logic; never prefix `[script]` recipes with `@`.
6. Use `require("bin")` for mandatory tools; avoid hardcoding absolute paths.
7. Use `[arg("name", long, …)]` for CLI-style parameters when version allows.
8. Keep secrets out of the file; use dotenv only when the project already does.

## Parameters and recipes

```just
[doc("Run tests with optional args")]
[group("checks")]
test *args="":
    uv run pytest {{args}}

[script]
[doc("Multi-line helper")]
[group("checks")]
smoke:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "smoke"
```

## After writing

1. `just --list` to verify the gallery.
2. `just --show <recipe>` for each new public recipe.
3. Optional: `just --dump --dump-format=json` for structural sanity.
4. Do not run `just --fmt` unless the user asks (see check.md).

## Anti-patterns to avoid at create time

- Make-style `##` help comments as the documentation system
- `@` on `[script]` recipes
- Quieting entire multi-line recipes with leading `@` on every fragile line when `[script]` is clearer
- Committing API keys, tokens, or `.env` contents into recipes
- Default recipe that deploys or destroys data
