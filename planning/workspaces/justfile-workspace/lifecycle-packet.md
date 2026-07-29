# justfile skill — lifecycle packet

| Field | Value |
| --- | --- |
| `skill_name` | `justfile` |
| `mode` | `create` |
| `plan_ssot` | `/Users/ww/.cursor/plans/justfile_skill_v6_aa98a36f.plan.md` |
| `progress_session` | `progress.py init --skill justfile --mode create` (2026-07-29) |

## source_evidence

- Casey Just manual: https://just.systems/man/en/ (Skill for Agents, recipe attributes, settings).
- Local house baseline: repo root `justfile` (`minimum-version` 1.55.0, `default-list`, `require()`, `[default]`/`[doc]`/`[group]`/`[arg]`, prefer `[script]` for multi-line).
- Inspect-first CLI: `just --version`, `just --list`, `just --show <recipe>`, `just --dump` / `--dump-format=json`, `just --groups`, `just --check` (fmt check).
- Distill-only vendor policy: cli-just / casey principles; no proprietary prose paste; no curated `cli-just` install requirement.
- Overlap: `shell-scripter` owns shell scripts + Makefile generation; this skill owns dedicated justfile create/edit/migrate/check/discover.

## trigger_surface

- Slash: `/justfile`, `/justfile <mode> …`
- Implicit NL: add/change justfile, Just recipes/modules, migrate Make/npm → just, lint house-style justfiles, discover via `just --list`/`--show`/`--dump`.
- NOT: pure shell generation (`shell-scripter`), convention-only shell edits (`shell-conventions`), CI YAML (`devops-engineer`), Make file-timestamp builds, Docker Compose authorship, mise toolchain-as-product.

## eval_plan

14 IDs (dual-eval policy B — `evals.json` + `projection_files` + per-id sidecars with parity):

`explicit-empty-gallery`, `explicit-create`, `explicit-edit`, `explicit-migrate`, `explicit-check`, `explicit-discover`, `implicit-justfile-nl`, `neg-pure-shell`, `neg-ci-yaml`, `neg-make-file-build`, `neg-mise-toolchain`, `neg-docker-compose`, `safety-secrets-in-justfile`, `safety-delete-makefile`.

L027 `without_skill` benchmark: **skip** (default).

## security_posture

- Posture enum: `write-scoped`
- May write justfiles; read-only `just` inspect by default.
- Ask before destructive recipes, deleting Makefile, or running side-effecting recipes.
- Never embed secrets in justfiles; prefer env / dotenv / require-time checks.
- No blind `just --fmt`; dry-run / inspect before mutating.

## runtime_matrix

| Surface | Expectation |
| --- | --- |
| Claude Code / Cursor / Codex / OpenCode / Crush / Grok | Skill body + refs portable; `scripts/check.py` via `uv run` |
| Just binary | Prefer ≥1.55.0; always `just --version` first; gate mid-2026 attributes on version |
| Validation | `scripts/check.py`, `audit.py` A≥90, `package.py --dry-run` |
| Docs/harness | Phase B only (out of Phase A scope) |

## benchmark_baseline

`without_skill` — **skipped** per v6 default (L027 off). Skill-green gate uses structural check/audit/package only for Phase A / J3.
