# Dashboard Design

Composable HTML dashboard for data-wizard EDA. Read during **Viz Dashboard** mode.

## Pattern

Follows the wargame dashboard contract: static `templates/dashboard.html` + JSON data block. The LLM/scripts generate only JSON; template JS renders deterministically.

```html
<script id="data" type="application/json">{...}</script>
```

## Schema Subset

Defined in `data/visualization-grammar.json` → `dashboard_views`.

| View | Purpose | Key fields |
|------|---------|------------|
| `summary` | Dataset overview | `rows`, `columns`, `memory_mb`, `dtype_summary` |
| `quality` | Quality scores | `dimensions`, `overall` |
| `columns` | Column profiles | `column_profiles` |
| `correlations` | Strong correlations | `correlations` |
| `missing` | Missing/duplicate patterns | `missing_patterns`, `duplicates` |
| `charts` | Viz artifacts | `viz_plan`, `chart_outputs` |

### Required top-level fields

| Field | Type | Notes |
|-------|------|-------|
| `view` | string | Space-separated view names, e.g. `summary quality columns charts` |
| `title` | string | Dashboard heading |

### Optional cross-view fields

| Field | Source |
|-------|--------|
| `viz_plan` | `viz-planner.py` output |
| `chart_outputs` | `viz-renderer.py` → `outputs` array |
| `chart_output_dir` | Renderer output directory |

## Builder Usage

```bash
# Profile first
uv run python scripts/data-profiler.py data.csv > profile.json

# Optional viz pipeline
uv run python scripts/viz-planner.py data.csv --goal "distributions" > plan.json
uv run python scripts/viz-renderer.py plan.json data.csv --format png > render.json

# Build dashboard
uv run python scripts/dashboard-builder.py profile.json \
  --viz-plan plan.json \
  --render-result render.json \
  --output ./data-wizard-dashboard.html
```

`dashboard-builder.py` copies the template, injects JSON into `#data`, and prints:

```json
{"status": "success", "output": "./data-wizard-dashboard.html", "views": ["summary", "..."], "charts": 2}
```

## View Selection

Default views (no `--views`): all grammar views except `charts`; `charts` added when plan or render result is provided.

Override:

```bash
uv run python scripts/dashboard-builder.py profile.json --views summary quality charts
```

## Backward Compatibility

`view: "eda"` still renders all sections (legacy). New dashboards should use explicit space-separated views.

## Critical Rules

1. **Profile before dashboard** — run `data-profiler.py` (and optionally `data-quality-scorer.py`) on real data
2. **Do not read template into context** — use `dashboard-builder.py` or `cp` + JSON injection
3. **PNG paths must be absolute** — renderer returns resolved paths for `file://` opening
4. **Keep payload compact** — omit null/empty sections; builder strips missing optional fields