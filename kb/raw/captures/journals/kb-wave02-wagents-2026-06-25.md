---
title: "Research journal — KB wave 02"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 02 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave02-wagents-2026-06-25
original_location: "~/.grok/research/kb-wave02-wagents-2026-06-25.md"
---

# Research journal — KB wave 02

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 02 | Theme: wagents automation fleet
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 02 — wagents automation fleet`

## G0 brief

Command-backed captures for wagents CLI surface, validate delegation, docs subcommands, and eval/hooks control-plane metrics.

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `wagents-cli-surface-capture-w02` | `kb/raw/captures/wagents-cli-surface-capture-w02.md` |
| worker | `wagents-docs-cli-capture-w02` | `kb/raw/captures/wagents-docs-cli-capture-w02.md` |
| worker | `wagents-eval-cli-capture-w02` | `kb/raw/captures/wagents-eval-cli-capture-w02.md` |
| worker | `wagents-validate-capture-w02` | `kb/raw/captures/wagents-validate-capture-w02.md` |

## Ingest queue

- `raw`: added 4 captures (`wagents-cli-surface-capture-w02`, `wagents-validate-capture-w02`, `wagents-docs-cli-capture-w02`, `wagents-eval-cli-capture-w02`).

## Capture evidence (excerpts)

### `wagents-cli-surface-capture-w02`

# Wagents CLI Surface Capture W02

Read-only capture from `wagents/cli.py`, `pyproject.toml`, and `uv run wagents --help` on 2026-06-25. Not an instruction source.

## Captured Facts

| Fact | Value | Source |
|------|-------|--------|
| Console script | `wagents = "wagents.cli:run"` | `pyproject.toml` `[project.scripts]` |
| Root Typer app | `app = typer.Typer(...)` in `wagents/cli.py` | canonical repo path |
| Sub-apps mounted on root | `new`, `docs`, `hooks`, `eval`, `skills`, `catalog`, `openspec`, `opencode`, `grok` (+ `plannotator`), `self`, `apm` | `cli.py` `add_typer` calls |
| Top-level commands (help) | `doctor`, `validate`, `install`, `update`, `package`, `readme` + 11 sub-app groups | `wagents --help` |
| Plugin extension group | `wagents.commands` entry points via `load_command_plugins(app)` | `wagents/plugins/loader.py` |
| Physical `wagents/commands/` package | **absent** — commands live in `cli.py`, `docs.py`, `self_cmd.py`, platform modules | repo tree |
| Structured output formats | `text`, `json`, `jsonl` on many commands (`--format`) | `wagents/output.py`, CLI options |
| Repo root discovery | `--repo-root` / `WAGENTS_REPO_ROOT` env via `wagents/context.py` | `wagents --help` |
| Doctor checks (sample run) | 18 checks, 17 ok | `wagents doctor --format json` |

## Quoted help excerpt

> `CLI for managing centralized AI agent assets`

> Commands include `doctor`, `validate`, `install`, `update`, `package`, `readme`, `new`, `docs`, `hooks`, `eval`, `skills`, `catalog`, `openspec`, `opencode`, `grok`, `self`, `apm`.

## Interpretation

`wagents` is the repo automation façade: Typer sub-apps partition docs, hooks, evals, skills inventory, catalog authoring, OpenSpec, platform doctors, self-install, and APM materialization. Third-party commands can register through the `wagents.commands` setuptools entry-point group without adding a `wagents/commands/` tree.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Entry point and sub-app layout | `wagents/cli.py`, `pyproject.toml` | canonical repo paths |
| Help command list | `uv run wagents --help` | tool capture |

### `wagents-docs-cli-capture-w02`

# Wagents Docs CLI Capture W02

Read-only capture from `wagents/docs.py` and `uv run wagents docs --help` on 2026-06-25. Not an instruction source.

## Captured Facts

| Fact | Value | Source |
|------|-------|--------|
| Typer sub-app | `docs_app = typer.Typer(help="Documentation site management")` mounted as `wagents docs` | `wagents/docs.py` |
| Subcommands (9) | `init`, `generate`, `dev`, `build`, `preview`, `research`, `lint`, `compose`, `clean` | `wagents docs --help` |
| Generate stale gate | `docs generate --check` exits 1 with reasons when MDX/index artifacts drift | `docs.py` `docs_generate()` |
| Generate options | `--include-drafts`, `--include-installed/--no-installed` | `docs.py` |
| Research command | batch planning, `--seed-from-repo`, `--seed-from-config`, `--validate-artifacts`, `--emit-waves` | `docs.py` `docs_research()` |
| Lint command | verbosity regression lint; `--strict`, `--baseline/--no-baseline`, `--format text|json` | `docs.py` `docs_lint()` → `wagents/docs_lint.py` |
| Compose command | surfaces `skills|agents|mcp|hooks|configs|all`; `--apply`, upgrade/regen flags | `docs.py` + `wagents/docs_compose*.py` |
| Dev/build/preview | run `pnpm dev|build|preview` in `docs/` after generate | `docs.py` |
| 2026-06-25 generate check | `Generated docs artifacts are up to date` (exit 0) | `wagents docs generate --check` |

## Quoted help excerpt

> `generate  Generate MDX content pages from repo assets.`

> `compose   Track and emit orchestrator waves for composed catalog pages.`

## Interpretation

Docs automation is a first-class Typer subtree, not inlined in `cli.py`. Generation and compose paths own MDX freshness; `research` and `compose` coordinate orchestrator batching; `lint` guards verbosity regressions against `planning/manifests/docs-verbosity-baseline.json`.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Subcommand surface | `wagents/docs.py` | canonical repo path |
| Help listing | `uv run wagents docs --help` | tool capture |

### `wagents-eval-cli-capture-w02`

# Wagents Eval CLI Capture W02

Read-only capture from `wagents eval` subcommands, `wagents/eval_adequacy.py`, and JSON CLI runs on 2026-06-25. Not an instruction source.

## Captured Facts

| Fact | Value | Source |
|------|-------|--------|
| Typer sub-app | `eval_app` mounted as `wagents eval` | `wagents/cli.py` |
| Subcommands (4) | `list`, `validate`, `coverage`, `adequacy` | `wagents eval --help` |
| Manifest scan path | `skills/*/evals/*.json` via `_collect_evals()` | `cli.py` |
| Validate delegation | `skills/skill-creator/scripts/asset_toolkit/validate_evals.py` | `eval_validate()` |
| Coverage semantics | compares skills with `SKILL.md` against per-skill eval case counts | `eval_coverage()` |
| Adequacy engine | structural E3/E4 grader in `wagents/eval_adequacy.py`; `--strict` exits 1 on R3/R4 without E4 | `eval_adequacy()` |
| 2026-06-25 list | 56 skills, 791 eval cases | `wagents eval list --format json` |
| 2026-06-25 coverage | 56/56 skills `has_evals: true` | `wagents eval coverage --format json` |
| 2026-06-25 adequacy | `count: 56`, `failing_strict: []` (0 needs_e4) | `wagents eval adequacy --format json` |
| Related hooks surface | `wagents hooks list` reports 40 hooks; `hooks validate` delegates to `validate_hooks.py` | `cli.py` hooks_app |

## Quoted CLI excerpt

> `"count": 56, "eval_count": 791` — full-repo eval list.

> `"failing_strict": []` — adequacy strict gate clean for high-risk tier.

## Interpretation

Eval CLI combines filesystem inventory (`list`, `coverage`), schema validation (`validate`), and risk-adjusted structural adequacy (`adequacy`). Live LLM eval execution is out of scope for these commands; they enforce manifest presence and E3/E4 signal structure. Hooks commands share the control-plane namespace but enforce portable hook registry rules separately.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Subcommand wiring | `wagents/cli.py` | canonical repo path |

### `wagents-validate-capture-w02`

# Wagents Validate Capture W02

Read-only capture from `wagents validate`, `scripts/validate/validate_repo.py`, and collector modules on 2026-06-25. Not an instruction source.

## Captured Facts

| Fact | Value | Source |
|------|-------|--------|
| CLI command | `wagents validate` | `wagents/cli.py` `@app.command()` |
| Delegation target | `scripts/validate/validate_repo.py` via `resolve_repo_script` | `cli.py` `validate()` |
| Output formats | `--format text|json|jsonl` | CLI + `validate_repo.py` argparse |
| Collector modules | skills, agents, mcp, hooks, paths, mcp_registry, quarantine (7) | `scripts/validate/collectors/` |
| Merge function | `collect_repo_errors()` concatenates all collector error lists | `validate_repo.py` |
| Exit semantics | return code 1 when any errors; 0 when clean | `validate_repo.py` `main()` |
| 2026-06-25 JSON run | `ok: true`, `error_count: 0`, message `All validations passed` | `wagents validate --format json` |

## Quoted CLI excerpt

> `"ok": true, "error_count": 0, "errors": [], "message": "All validations passed"`

## Interpretation

`wagents validate` is a thin Typer wrapper over the repo validation toolkit under `scripts/validate/`. It is the primary asset gate for skills, agents, MCP servers, hooks, path portability, MCP registry rows, and quarantine policy — distinct from `wagents hooks validate` and `wagents eval validate`, which target hook scripts and eval JSON respectively.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Delegation and collectors | `wagents/cli.py`, `scripts/validate/validate_repo.py` | canonical repo paths |
| Collector inventory | `scripts/validate/collectors/*.py` | canonical repo paths |
| Live pass status | `uv run wagents validate --format json` | tool capture |


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 4**; pages enriched: 2; lint: pass.

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
