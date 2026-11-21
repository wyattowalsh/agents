# Progress Reporting

## Contents

1. [Producer contract](#producer-contract)
2. [Accounting](#accounting)
3. [Legacy reports](#legacy-reports)
4. [Refresh lifecycle](#refresh-lifecycle)
5. [Verification](#verification)

## Producer Contract

Use `scripts/files_buddy_report.py` as the shared normalizer. The machine-readable
normalized format is `assets/report.schema.json`. It describes reports, not
execution plans or consent. Valid structure does not certify an observation.

```python
from files_buddy_report import new_report, normalize_report

report = new_report("storage-audit", ["/Users/example/Downloads"])
report["coverage"] = {"status": "partial", "omissions": ["Cloud content was not read."]}
report["counts"] = {"files_seen": 12, "skipped": 2, "errors": 0}
report["savings"]["logical_bytes"] = 4096
report["status"] = "completed"
report = normalize_report(report)
```

A producer updates `updated_at` after each observation batch, then normalizes and
atomically publishes a complete snapshot. Use a unique run directory such as
`~/.files-buddy/runs/<run-id>/`; partial output is never a valid snapshot. The
inventory and execution helpers own their state. A dashboard is a derived view.

| Field | Contract |
| --- | --- |
| `schema_version` | Exactly `"2.0"` for new reports |
| `run_id` | Unique 1–128 character identifier starting with a letter/digit, followed by letters, digits, dot, underscore or hyphen |
| `mode` | Producer's operation label |
| `updated_at` | RFC 3339 timestamp (`YYYY-MM-DDTHH:MM:SS[.fraction]Z` or a numeric timezone offset); null means capture time is unknown |
| `status` | `unknown`, `running`, `waiting-for-approval`, `executing`, `completed`, `partial`, `failed`, or `cancelled` |
| `scope` | Explicit array of path strings |
| `coverage` | `status`: complete, partial, unavailable or unknown; `omissions`: array of reasons |
| `counts` | Nonnegative integer counts; include skipped, errors, and truncation when known |
| `savings` | Named accounting metrics below; null means unknown |
| `source_digest` | SHA-256 of canonical normalized content, excluding this field; evidence identity, never consent |
| `manifest` | Null or an object with a nullable `path` and optional status/evidence |

Collections are arrays of objects: `files`, `directories`, `duplicates`,
`recommendations`, `categories`, `events`, `operations`, `cloud`, and `caches`.
Preserve tool version, scan limits, provenance, dependency evidence and metadata
in rows. Cap exported collections; keep the full inventory in its owning store.
The renderer rejects reports over 16 MiB or collections above 100,000 rows.
Its tables display at most 200 filtered rows while retaining all supplied rows
for filtering and sorting.

Recommendation and cloud rows use **`local_bytes`** consistently for local
estimates, **`cloud_bytes`** for remote impact, and **`restore_path`** for recovery
evidence. Missing values stay null. Risk is `unknown`, `low`, `medium`, `high`, or
`critical`. Duplicate `kind` is `exact`, `similar`, or `unknown`. A duplicate group
never creates a recommendation, keeper, Low risk, or restore guarantee by itself.

## Accounting

All byte metrics are integer bytes, displayed with binary units such as GiB.
Unknown differs from zero. Negative values are valid only for the observed
free-space delta. Metrics must fit a JavaScript safe integer for exact rendering.

| Metric | Meaning |
| --- | --- |
| `logical_bytes` | Sum of observed file lengths, with inventory coverage/link accounting disclosed |
| `allocated_bytes` | Allocated estimate from metadata, when available |
| `eligible_bytes` | Bytes passing the producer's eligibility rules, when separately measured |
| `candidate_bytes` | Candidate estimate after the producer's recommendation review |
| `selected_bytes` | Bytes selected in an exact reviewed plan |
| `acted_bytes` | Bytes involved in completed effects; not evidence of reclaimed space |
| `quarantined_bytes` | Bytes retained in a staging location |
| `trash_retained_bytes` | Bytes retained in Trash |
| `verified_reclaimed_bytes` | Explicitly evidenced reclaimed bytes; leave unknown when attribution is unsupported |
| `observed_free_space_delta_bytes` | Measured volume free-space change, which may include concurrent activity |
| `cloud_bytes_affected` | Observed or estimated remote storage impact; unknown when unavailable |
| `legacy_verified_local_bytes` | Historical 1.1 metric that conflated verified moves and savings; informational only |

Do not add these stages together or convert a move into reclaimed bytes. APFS
clones, sparse files, snapshots, purgeable storage, and concurrent work limit
attribution. Emptying Trash is a separate operation with separate authorization.

## Legacy Reports

Published unversioned and `1.1` reports are normalized explicitly. Unknown
versions, null roots, wrong collection types, invalid numbers, unknown metric
names, and malformed timestamps fail with a JSON error and a nonzero exit.
Legacy directory/duplicate aliases are accepted only on the legacy route.

Legacy `completed_local_bytes` maps to `acted_bytes`. Legacy
`verified_local_bytes`, including zero, maps only to
`legacy_verified_local_bytes`: its old definition included moves. It never
supplies `verified_reclaimed_bytes`. Legacy recommendation
`local_bytes_saved` maps to the canonical `local_bytes` field. Normalization
warnings remain visible. Renderer output and exports use the normalized schema.

## Refresh Lifecycle

The default HTML displays its embedded snapshot. Merely displaying a progress
path does not make that snapshot live. **Import snapshot** validates and replaces
the displayed data with a selected v2 JSON file. Invalid input keeps the previous
valid view and displays an error. Re-render legacy input through the Python CLI
before importing it through the browser.

On browsers supporting the File System Access API, selecting one file grants
read access to that file. **Refresh selected file** reads its current contents.
**Start auto refresh** polls that selected handle every three seconds, stops
within one hour, pauses when the tab is hidden, and stops on read/validation
failure. No write handles, network requests, cleanup actions or background
services are used. Other browsers offer explicit file selection for each update.
Running snapshots older than five minutes are labeled stale; capture time is
always visible.

## Verification

Run Python behavioral tests and the Node dashboard event tests independently of
structural skill evals:

```bash
uv run python -m pytest tests/test_reporting.py -q
node tests/dashboard-behavior.cjs
```

`tests/dashboard-browser.cjs` is an optional rendered acceptance suite requiring
an existing Playwright/Chromium runtime. It covers desktop/mobile layout, long
paths, keyboard focus, filtering, invalid import, reduced motion and console
errors. A blocked browser launch is missing evidence, not a passed UI check.
