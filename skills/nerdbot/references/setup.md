# Setup

## Local Development

Use `uv run --project skills/nerdbot nerdbot` from this repository checkout. Use bare `nerdbot` only after installing the package into the active environment.

```bash
uv run --project skills/nerdbot nerdbot --help
uv run pytest tests/test_nerdbot_scripts.py tests/test_nerdbot_schema_contracts.py tests/test_nerdbot_package.py -q
```

## First KB Walkthrough

```bash
uv run --project skills/nerdbot nerdbot bootstrap --root ./my-kb --dry-run
uv run --project skills/nerdbot nerdbot bootstrap --root ./my-kb
uv run --project skills/nerdbot nerdbot inventory --root ./my-kb
uv run --project skills/nerdbot nerdbot lint --root ./my-kb --include-unlayered
uv run --project skills/nerdbot nerdbot plan --mode query --target ./my-kb --view guide
```

`bootstrap --dry-run`, `inventory`, `lint`, `modes`, `plan`, `audit`, `query`, `replay`, and `watch-classify` are safe/read-only. `bootstrap` without `--dry-run` creates files, and workflow commands mutate only with `--apply`, so run them only after reviewing dry-run output.

## Optional Extras

Install optional adapter groups only when a workflow needs them:

```bash
uv sync --project skills/nerdbot --extra crawl
uv sync --project skills/nerdbot --extra docs
uv sync --project skills/nerdbot --extra semantic
uv sync --project skills/nerdbot --extra vlm
```

The baseline CLI must continue to work without these extras.
