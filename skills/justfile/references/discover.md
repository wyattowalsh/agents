# Discover — inspect Just recipes (read-only)

Prefer inspect-first discovery. Do not run side-effecting recipes while
discovering. Casey manual: https://just.systems/man/en/

## Version gate

```bash
just --version
```

Record the version. House baseline expects ≥1.55.0 for `minimum-version`,
`default-list`, `[arg]`, and related mid-2026 features. If older, avoid
recommending unavailable attributes and note the gap.

## Primary inspect commands

| Command | Purpose |
| --- | --- |
| `just --list` / `just -l` | List public recipes (respects `default-list` / `[default]`) |
| `just --list <module>` | List recipes in a submodule |
| `just --groups` | List recipe groups |
| `just --show <recipe>` | Show recipe source |
| `just --dump` | Print effective justfile |
| `just --dump --dump-format=json` | Machine-readable dump for agents |
| `just --evaluate` | Show assignment values |
| `just --summary` | Compact recipe names |

## Discover workflow

1. Confirm `just` is on PATH; run `--version`.
2. From the project root (or `--justfile` / `--working-directory` if needed), run `--list`.
3. If the user names a recipe, `--show <recipe>` before proposing edits or runs.
4. For structural analysis (modules, parameters, attributes), prefer `--dump-format=json`.
5. Summarize: default recipe, groups, private helpers, risky recipes (deploy, clean, publish).

## Working directory and justfile selection

- Just searches upward for `justfile` / `Justfile` unless overridden.
- Use `--justfile PATH` and `--working-directory PATH` when the target is not cwd.
- Do not assume the first recipe is safe to run; treat discovery as read-only.

## Interpreting house-style dumps

Expect settings similar to this repo:

```just
set shell := ["bash", "-euo", "pipefail", "-c"]
set default-list
set minimum-version := "1.55.0"
```

Look for `require("…")` assignments, `[doc]` / `[group]` / `[arg]` attributes,
and `[script]` multi-line bodies. Flag Make-flavored `##` comment documentation
as a migrate/edit opportunity (Just uses `[doc]` + list, not Make help hacks).

## Safety while discovering

- Never run `clean`, `deploy`, `publish`, `install -g`, or network recipes as part of discover.
- If the user asks "what does X do?", prefer `--show` over executing X.
- If dump JSON is huge, summarize groups and high-risk names; do not paste entire dumps into chat.

## Output shape for agents

Return:

1. Just version
2. Default / first recipe behavior
3. Grouped recipe inventory (name + doc)
4. Notable settings (`dotenv-load`, `positional-arguments`, modules)
5. Open questions (missing just binary, version too old, multiple justfiles)
