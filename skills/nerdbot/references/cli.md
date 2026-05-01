# CLI Reference

## Implemented Commands

Use bare `nerdbot` after installing the package. From this repository checkout, prefix examples with `uv run --project skills/nerdbot` to run the local package:

```bash
uv run --project skills/nerdbot nerdbot bootstrap --root ./kb --dry-run
```

Installed-package examples:

```bash
nerdbot bootstrap --root ./kb --dry-run
nerdbot inventory --root ./kb
nerdbot lint --root ./kb --include-unlayered
nerdbot modes
nerdbot plan --mode ingest --target ./incoming/source.pdf
nerdbot plan --mode query --target ./kb --view guide
nerdbot create --root ./kb --apply
nerdbot ingest --root ./kb --source ./incoming/source.md --apply
nerdbot enrich --root ./kb --target raw/sources/src-example.md --apply
nerdbot audit --root ./kb --include-unlayered
nerdbot query --root ./kb "vendor pricing risk"
nerdbot derive --root ./kb --artifact all --apply
nerdbot improve --root ./kb --apply
nerdbot migrate --root ./kb --target wiki/old.md --approval-token APPROVE-MIGRATION --apply
nerdbot replay --root ./kb
nerdbot watch-classify wiki/index.md --stable
```

## Command Contracts

- `bootstrap` may mutate, but `--dry-run` must write nothing.
- `inventory` is read-only.
- `lint` is read-only and exits non-zero according to `--fail-on`.
- `plan` is read-only and returns the required gates, safety promises, and next command.
- `modes` is read-only and presents a polished workflow gallery for humans or JSON callers.
- `create`, `ingest`, `enrich`, `derive`, `improve`, and `migrate` default to dry-run unless `--apply` is present.
- `audit`, `query`, `replay`, and `watch-classify` are read-only workflows.
- Applied mutating workflows append `activity/operations.jsonl` with replayable changed paths.
- `migrate --apply` writes only an additive migration plan and requires `--approval-token APPROVE-MIGRATION`; it does not move, delete, or rewrite canonical files.

## First KB Walkthrough

```bash
uv run --project skills/nerdbot nerdbot bootstrap --root ./my-kb --dry-run
uv run --project skills/nerdbot nerdbot bootstrap --root ./my-kb
uv run --project skills/nerdbot nerdbot inventory --root ./my-kb
uv run --project skills/nerdbot nerdbot lint --root ./my-kb --include-unlayered
uv run --project skills/nerdbot nerdbot plan --mode query --target ./my-kb --view guide
uv run --project skills/nerdbot nerdbot plan --mode ingest --target ./incoming/source.pdf --view guide
uv run --project skills/nerdbot nerdbot query --root ./my-kb "what do we know?"
uv run --project skills/nerdbot nerdbot derive --root ./my-kb --artifact graph --apply
```

Review dry-run output before every `--apply`. `bootstrap` remains the compatibility scaffold command; `create` is the workflow command that wraps scaffold creation and records an operation journal entry. Use `query` and `audit` for read-only work, then use applied `ingest`, `enrich`, `derive`, `improve`, or approved `migrate` batches when the planned changes are acceptable.

## Output Contract

Operational commands emit JSON so other agents, hooks, and CI jobs can consume results without parsing prose. Workflow commands share an envelope with `command`, `mode`, `target`, `status`, `dry_run`, `applied`, `planned_changes`, `changed_paths`, `operation`, `journal_path`, `warnings`, `errors`, `suggested_next_actions`, and command-specific `payload`. Human-facing discovery commands support `--view guide` for dependency-free terminal cards with risk posture, gate path, safety promises, roadmap lanes, and copy-friendly next commands while preserving JSON with `--view json`.
