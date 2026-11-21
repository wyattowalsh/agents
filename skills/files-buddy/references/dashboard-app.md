# Dashboard

## Contents

1. [Implementation](#implementation)
2. [Render a report](#render-a-report)
3. [Panels and semantics](#panels-and-semantics)
4. [Accessibility and lifecycle](#accessibility-and-lifecycle)
5. [Validation](#validation)

## Implementation

`templates/dashboard.html` is the maintained, self-contained HTML/CSS/JavaScript
implementation. It has no React build, CDN, network dependency, or mutation
controls. The renderer embeds validated data and the report schema. A restrictive
content security policy disables network connections, external resources, forms,
and base-URL changes.

The visual design uses a dark or light system theme, restrained green accents,
dense evidence tables, binary byte units, and explicit unknown values. No chart
color or inferred default substitutes for risk evidence. Directory sizes appear
in a table. Category bars have adjacent textual values.

## Render a Report

Run from the installed skill directory:

```bash
python scripts/dashboard-renderer.py --data report.json
python scripts/dashboard-renderer.py --data report.json --output new-report.html
python scripts/dashboard-renderer.py --data report.json --progress progress.json --open
```

Default output is a unique file under
`~/.files-buddy/runs/<run-id>/dashboard-<unique-id>.html`. Explicit output paths
must not exist. Reports are created with owner-only permissions and existing
files are never overwritten. Default state directories reject symlinks and must
belong to the current user. Explicit destinations are caller-selected. Successful stdout includes the output path, run ID,
normalized source digest, actual browser-open result, and refresh mode.

`--progress` records a suggested source path for the reader; it does not grant
browser access or start polling. `--open` is opt-in. `--template` is for an
explicitly trusted local template containing the three required data, progress
configuration, and schema placeholders. Malformed input fails before output is
created. JSON inside script elements and all displayed text are escaped.

## Panels and Semantics

| Panel | Evidence shown |
| --- | --- |
| Summary | Inventoried logical bytes, candidate estimate, verified reclaimed bytes, observed free-space delta |
| Run and coverage | Status, captured time, stale state, exact scope, phase, source digest, omissions and normalization warnings |
| Storage accounting | Independent metrics, including retained quarantine/Trash and historical ambiguous values |
| Category observations | Reported category sizes with textual values |
| Recommendation risk | Supplied recommendation counts and known estimates, including Unknown risk |
| Recommendations | Explicit action, local estimate, dependency evidence, repercussions and recovery |
| Directory sizes | Reported logical/allocated estimates without claiming a proportional treemap |
| Duplicate review | Exact/similar/unknown kind, paths, keeper evidence and risk; never fabricated actions |
| Cache impact | Owner, dependency evidence, regeneration and recovery |
| Cloud offload | Consistent `local_bytes`/`cloud_bytes` fields for rows and totals |
| Inventory | Supplied paths, object kind, category, size and eligibility |
| Progress timeline | Producer events with timestamps |
| Manifest evidence | Structured manifest path/status and recorded operations |

A missing metric displays **Unknown**. Explicit zero stays zero. Unknown
recommendation totals remain unknown if any contributing row lacks the metric.
The dashboard does not infer reclaimable physical space from logical size,
completed operations, staging, Trash, or exact content equality.

## Accessibility and Lifecycle

- Semantic headings, table captions, scoped table headers, and a keyboard skip link.
- Explicit labels for file import, search and sort; native buttons and selects.
- Visible focus treatment and keyboard-focusable scroll regions for wide tables.
- Narrow-screen stacking, wrapped long paths, system color themes and reduced-motion CSS.
- Textual chart values, Unknown risk labels and accessible import/error status.
- Filter and sort controls retain focus while report sections update.

See `progress-reporting.md` for the bounded file-handle refresh lifecycle.
Import failures retain the last valid snapshot. The browser never executes
manifest operations, starts a watcher, or requests network access.

## Validation

The synthetic report fixture is `tests/fixtures/reports/storage-audit.json`.
It includes zero verified bytes despite completed work, unknown cloud risk,
partial coverage, a structured manifest, cache uncertainty, and long Unicode paths.

```bash
uv run python -m pytest tests/test_reporting.py -q
node tests/dashboard-behavior.cjs
node tests/dashboard-browser.cjs
```

The first two commands verify serialization, normalization, markup and event
behavior. The optional browser command needs an existing Playwright/Chromium
runtime. It uses Playwright's bundled Chromium by default; set
`FILES_BUDDY_BROWSER_PATH` to an installed browser when needed. Set
`FILES_BUDDY_PLAYWRIGHT_MODULE` to the installed Node module path when it is
outside Node's normal resolution path (CI uses the locked Python Playwright
package's `driver/package`).
It returns exit 2 when browser launch is blocked. Report actual rendered evidence
separately from static or simulated-DOM checks.
