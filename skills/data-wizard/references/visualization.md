# Visualization Pipeline

Chart planning and rendering for data-wizard. Read during **Viz Plan**, **Viz Render**, or base **Visualization** mode.

## Pipeline

| Step | Script | Input | Output |
|------|--------|-------|--------|
| Plan | `scripts/viz-planner.py` | CSV/JSON path + goal | JSON chart plan |
| Render | `scripts/viz-renderer.py` | Plan JSON + data path | PNG (matplotlib) or HTML (plotly) |
| Dashboard | `scripts/dashboard-builder.py` | Profile JSON + optional plan/render | Single HTML file |

## Planning (`viz plan`)

```bash
uv run python scripts/viz-planner.py data.csv --goal "compare groups"
```

The planner:

1. Profiles column types (numeric, categorical, datetime)
2. Maps `--goal` keywords to grammar categories (`comparison`, `distribution`, `relationship`, `trend`, `composition`, `spatial`)
3. Selects chart types from `data/visualization-grammar.json`
4. Emits encodings (`x`, `y`, `color`, `columns`) and rationale per chart

Auto-goal heuristics when `--goal` is omitted:

- Datetime + numeric → **trend**
- 2+ numeric → **relationship**
- Categorical + numeric → **comparison**
- Numeric only → **distribution**
- Categorical only → **composition**

## Rendering (`viz render`)

```bash
uv run python scripts/viz-renderer.py plan.json data.csv --format png --output-dir ./viz-output
```

| Format | Engine | Use when |
|--------|--------|----------|
| `png` | matplotlib | Reports, slides, dashboard thumbnails |
| `html` | plotly | Interactive exploration in browser |

Missing dependencies return JSON errors on stdout (not stack traces):

- `matplotlib not installed. Run: uv pip install matplotlib`
- `plotly not installed. Run: uv pip install plotly`

Supported render types: `bar_chart`, `grouped_bar`, `stacked_bar`, `histogram`, `scatter_plot`, `line_chart`, `box_plot`, `heatmap`.

Grouped and stacked bars pivot on `x` + `color` encodings. More than 10 x categories falls back to a simple aggregated bar chart.

## Encoding Guidance

From `visualization-grammar.json`:

- **position_x** — primary comparison dimension (categories, time)
- **position_y** — measured value
- **color_hue** — categorical groups (≤10 levels)
- **color_intensity** — sequential numeric scale
- Default palette: viridis (colorblind-safe)

## When to Recommend vs Render

| Situation | Action |
|-----------|--------|
| User asks what chart to use | Base `viz` mode — grammar recommendations only |
| User wants executable artifacts | `viz plan` → `viz render` |
| User wants shareable EDA report | Profile data → `viz dashboard` |

## Critical Rules

1. **Plan before render** — never guess encodings; run `viz-planner.py` on actual columns
2. **Match data path** — renderer data file must match the planner's `file` field
3. **State assumptions** — high-cardinality categoricals may need aggregation before bar charts
4. **Prefer PNG for dashboards** — embed static assets; use HTML for interactive follow-up