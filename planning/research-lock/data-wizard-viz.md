# Research lock: data-wizard viz enrichment

- Extend `viz` → `viz plan`, `viz render`, `viz dashboard`
- Scripts: viz-planner.py, viz-renderer.py, dashboard-builder.py
- Grammar: visualization-grammar.json + dashboard_views
- Template: templates/dashboard.html (borrow wargame composable views)
- Output: PNG/HTML artifacts; NOT React frontend code
- **Remediation (2026-07-02):** `default_palette`; grouped/stacked bar renderer; hand-maintained catalog viz sync; parquet max_rows in renderer