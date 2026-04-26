# Debugging

## Contents

1. Triage Order
2. Environment Problems
3. Template Problems
4. Backend and Provider Problems
5. Extraction Problems
6. Graph Problems
7. Batch Recovery

## Triage Order

Use this reference in **Debug**, **API**, and **Batch** modes.

Debug in this order:

1. Install and import.
2. CLI availability.
3. Template importability.
4. Backend/inference compatibility.
5. Provider credentials and rate limits.
6. Source document conversion.
7. Extraction/validation.
8. Graph conversion/export.

Do not skip ahead to template redesign until basic environment and import checks are proven.

## Environment Problems

Run:

```bash
uv run python skills/docling-graph/scripts/check-env.py --format json
```

Common signals:

| Symptom | Likely cause | Next step |
|---|---|---|
| package missing | `docling-graph` not installed in active environment | install in project env or switch env |
| CLI missing but import works | scripts path not exposed | use `uv run docling-graph` or env-specific executable |
| API key missing | remote provider env var absent | set provider env var, do not print secret |
| Python too old | package requires modern Python | upgrade env |

## Template Problems

For local files:

```bash
uv run python skills/docling-graph/scripts/lint-template.py templates.py --format json
```

For import paths:

```bash
uv run python skills/docling-graph/scripts/check-env.py \
  --template templates.BillingDocument \
  --format json
```

Common fixes:

1. Add project root to `PYTHONPATH`.
2. Use a full dotted import path.
3. Ensure class name matches exactly.
4. Add missing package `__init__.py` when needed.
5. Fix syntax/import errors in the template module.

## Backend and Provider Problems

Common mismatches:

| Problem | Fix |
|---|---|
| VLM with remote inference | Use local inference or switch to LLM |
| GPU memory failure | Smaller model, chunking, OCR pipeline, or LLM fallback |
| provider auth failure | Check env var presence and provider name |
| rate limit | retry with backoff, reduce concurrency, or switch provider |
| poor layout extraction | revisit Docling pipeline before rewriting schema |

## Extraction Problems

If extraction fails:

1. Re-run with debug enabled.
2. Inspect partial outputs before deleting anything.
3. Check whether source conversion succeeded.
4. Check whether the template is too strict.
5. Compare one small sample against expected graph facts.

For partial success, preserve the extracted model, graph files, metadata, and debug traces. Partial data can be useful for template repair.

## Graph Problems

| Symptom | Likely cause | Fix |
|---|---|---|
| Empty graph | no entity models, extraction empty, or conversion failed | inspect extracted model and entity configs |
| Missing edges | relationship fields not nested or edge labels absent | add explicit relationship fields |
| Duplicate nodes | weak stable IDs | add or improve `graph_id_fields` |
| Noisy graph | components modeled as entities | mark value objects as components |
| Bad labels | field names too generic | add explicit edge labels |

## Batch Recovery

For batch failures:

1. Do not rerun the whole corpus first.
2. Build a failed-document list.
3. Preserve successful output directories.
4. Retry only failed documents after changing config/template.
5. Record old and new command/config for comparison.
6. Flag documents with outlier node/edge counts for manual review.
