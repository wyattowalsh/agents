# Check — lint and house-style audit

Check is inspect-first. Do not overwrite formatting unless the user asks.
Manual: https://just.systems/man/en/

## Commands

| Command | Writes? | Use |
| --- | --- | --- |
| `just --version` | No | Version gate |
| `just --list` / `--groups` | No | Inventory |
| `just --show <recipe>` | No | Review body |
| `just --dump` / `--dump-format=json` | No | Structure |
| `just --check` | No | Fail if `--fmt` would change the file |
| `just --fmt` | **Yes** | Format in place — ask first |

## Check workflow

1. Confirm justfile path; run `--version`.
2. Parse / dump; ensure the file loads (`just --list` should succeed).
3. Run `just --check` to detect formatter drift without writing.
4. Audit house-style checklist (below); report findings with severity.
5. Apply `--fmt` only with explicit user intent after showing `--check` result.

## House-style checklist

Pass/fail against this repo's baseline:

- [ ] `set shell := ["bash", "-euo", "pipefail", "-c"]` (or documented exception)
- [ ] `set default-list` and safe `[default]` list recipe
- [ ] `set minimum-version` appropriate to features used (prefer `1.55.0`)
- [ ] Public recipes have `[doc("…")]`
- [ ] Related recipes share `[group("…")]`
- [ ] Hard tools use `require("…")` where appropriate
- [ ] Multi-line shell uses `[script]` without leading `@` on the recipe
- [ ] No Make-style `##` help system
- [ ] No hardcoded secrets / tokens
- [ ] Destructive recipes are clearly named and documented

## Severity guide

| Severity | Examples |
| --- | --- |
| error | File does not parse; `@` on `[script]`; secrets in file |
| warning | Missing docs/groups; no `minimum-version` while using new attrs; blind fmt needed |
| info | Could prefer `[script]`; optional `require()` improvements |
| style | Formatter drift (`--check` fails); comment noise |

## What check must not do

- Must not run deploy/clean/publish recipes as "validation"
- Must not delete Makefile or other runners
- Must not `--fmt` by default
- Must not claim Capital-J law or unrelated style religions

## Skill self-check (when editing this skill)

From `skills/justfile/`:

```bash
uv run python scripts/check.py
```

That validates SKILL.md / evals / package dry-run / audit — separate from
`just --check` on a project justfile.
