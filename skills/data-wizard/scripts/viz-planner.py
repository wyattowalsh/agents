#!/usr/bin/env python3
"""Visualization planner. Input: CSV/JSON path + goal. Output: JSON chart plan."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print(json.dumps({"error": "pandas not installed. Run: uv pip install pandas"}))
    sys.exit(1)

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_GRAMMAR = SKILL_DIR / "data" / "visualization-grammar.json"

GOAL_ALIASES = {
    "compare": "comparison",
    "comparison": "comparison",
    "distribution": "distribution",
    "distributions": "distribution",
    "relationship": "relationship",
    "relationships": "relationship",
    "correlation": "relationship",
    "correlations": "relationship",
    "trend": "trend",
    "time": "trend",
    "timeseries": "trend",
    "time-series": "trend",
    "composition": "composition",
    "proportion": "composition",
    "proportions": "composition",
    "spatial": "spatial",
    "map": "spatial",
    "geo": "spatial",
}


def load_data(path: str, max_rows: int | None = None) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        print(json.dumps({"error": f"File not found: {path}"}), file=sys.stderr)
        sys.exit(1)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(p, nrows=max_rows)
    if suffix in (".json", ".jsonl"):
        df = pd.read_json(p, lines=suffix == ".jsonl")
        if max_rows is not None:
            df = df.head(max_rows)
        return df
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(p, nrows=max_rows)
    if suffix == ".parquet":
        df = pd.read_parquet(p)
        if max_rows is not None:
            df = df.head(max_rows)
        return df
    if suffix == ".tsv":
        return pd.read_csv(p, sep="\t", nrows=max_rows)
    print(json.dumps({"error": f"Unsupported format: {suffix}"}), file=sys.stderr)
    sys.exit(1)


def load_grammar(path: Path) -> dict:
    if not path.exists():
        print(json.dumps({"error": f"Grammar file not found: {path}"}), file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def classify_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    numeric: list[str] = []
    categorical: list[str] = []
    datetime_cols: list[str] = []
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(str(col))
        elif pd.api.types.is_numeric_dtype(series):
            numeric.append(str(col))
        else:
            categorical.append(str(col))
    return {
        "numeric_columns": numeric,
        "categorical_columns": categorical,
        "datetime_columns": datetime_cols,
    }


def infer_goal_category(goal: str | None, summary: dict[str, list[str]]) -> str:
    if goal:
        tokens = re.findall(r"[a-z0-9-]+", goal.lower())
        for token in tokens:
            if token in GOAL_ALIASES:
                return GOAL_ALIASES[token]
        for token in tokens:
            for alias, category in GOAL_ALIASES.items():
                if alias in token or token in alias:
                    return category

    numeric = summary["numeric_columns"]
    categorical = summary["categorical_columns"]
    datetime_cols = summary["datetime_columns"]

    if datetime_cols and numeric:
        return "trend"
    if len(numeric) >= 2:
        return "relationship"
    if categorical and numeric:
        return "comparison"
    if numeric:
        return "distribution"
    if categorical:
        return "composition"
    return "comparison"


def pick_chart_type(category: str, grammar: dict, summary: dict[str, list[str]], index: int) -> dict:
    selector = grammar.get("chart_selector", {})
    charts = selector.get(category, {}).get("charts", [])
    if not charts:
        charts = selector.get("comparison", {}).get("charts", [{"type": "bar_chart"}])
    return charts[min(index, len(charts) - 1)]


def build_chart_specs(
    category: str,
    grammar: dict,
    summary: dict[str, list[str]],
    goal: str | None,
) -> list[dict]:
    numeric = summary["numeric_columns"]
    categorical = summary["categorical_columns"]
    datetime_cols = summary["datetime_columns"]
    charts: list[dict] = []

    if category == "trend" and datetime_cols and numeric:
        charts.append(
            {
                "id": "chart_trend_primary",
                "type": "line_chart",
                "title": f"{numeric[0]} over time",
                "encodings": {"x": datetime_cols[0], "y": numeric[0], "color": None},
                "library": "matplotlib",
                "rationale": "Datetime column with numeric measure suggests temporal trend",
            }
        )
        if len(numeric) > 1:
            charts.append(
                {
                    "id": "chart_trend_secondary",
                    "type": "line_chart",
                    "title": f"{numeric[1]} over time",
                    "encodings": {"x": datetime_cols[0], "y": numeric[1], "color": None},
                    "library": "matplotlib",
                    "rationale": "Secondary metric for multi-series trend comparison",
                }
            )
        return charts

    if category == "relationship" and len(numeric) >= 2:
        charts.append(
            {
                "id": "chart_scatter_primary",
                "type": "scatter_plot",
                "title": f"{numeric[0]} vs {numeric[1]}",
                "encodings": {
                    "x": numeric[0],
                    "y": numeric[1],
                    "color": categorical[0] if categorical else None,
                },
                "library": "matplotlib",
                "rationale": "Pairwise relationship between continuous variables",
            }
        )
        if len(numeric) >= 3:
            charts.append(
                {
                    "id": "chart_heatmap_corr",
                    "type": "heatmap",
                    "title": "Numeric correlation matrix",
                    "encodings": {"columns": numeric[:8]},
                    "library": "matplotlib",
                    "rationale": "Multiple numeric columns warrant correlation overview",
                }
            )
        return charts

    if category == "comparison" and categorical and numeric:
        charts.append(
            {
                "id": "chart_bar_compare",
                "type": "bar_chart",
                "title": f"{numeric[0]} by {categorical[0]}",
                "encodings": {"x": categorical[0], "y": numeric[0], "color": None},
                "library": "matplotlib",
                "rationale": "Categorical grouping with numeric magnitude comparison",
            }
        )
        if len(categorical) > 1:
            chart_def = pick_chart_type(category, grammar, summary, 1)
            charts.append(
                {
                    "id": "chart_grouped_bar",
                    "type": chart_def.get("type", "grouped_bar"),
                    "title": f"{numeric[0]} across {categorical[0]} and {categorical[1]}",
                    "encodings": {
                        "x": categorical[0],
                        "y": numeric[0],
                        "color": categorical[1],
                    },
                    "library": "matplotlib",
                    "rationale": chart_def.get("when", "Two categorical dimensions"),
                }
            )
        return charts

    if category == "distribution" and numeric:
        charts.append(
            {
                "id": "chart_hist_primary",
                "type": "histogram",
                "title": f"Distribution of {numeric[0]}",
                "encodings": {"x": numeric[0], "bins": 30},
                "library": "matplotlib",
                "rationale": "Single continuous variable distribution",
            }
        )
        if categorical:
            charts.append(
                {
                    "id": "chart_box_by_group",
                    "type": "box_plot",
                    "title": f"{numeric[0]} by {categorical[0]}",
                    "encodings": {"x": categorical[0], "y": numeric[0]},
                    "library": "matplotlib",
                    "rationale": "Compare distributions and outliers across groups",
                }
            )
        return charts

    if category == "composition" and categorical:
        charts.append(
            {
                "id": "chart_composition",
                "type": "bar_chart",
                "title": f"Counts by {categorical[0]}",
                "encodings": {"x": categorical[0], "y": "__count__", "color": None},
                "library": "matplotlib",
                "rationale": "Category frequency composition",
            }
        )
        return charts

    # Fallback
    chart_def = pick_chart_type(category, grammar, summary, 0)
    encodings: dict = {}
    if numeric:
        encodings["y"] = numeric[0]
    if categorical:
        encodings["x"] = categorical[0]
    charts.append(
        {
            "id": "chart_fallback",
            "type": chart_def.get("type", "bar_chart"),
            "title": goal or f"{category} overview",
            "encodings": encodings,
            "library": "matplotlib",
            "rationale": chart_def.get("when", "Best-effort chart from available columns"),
        }
    )
    return charts


def build_plan(path: str, goal: str | None, grammar_path: Path, max_rows: int | None) -> dict:
    grammar = load_grammar(grammar_path)
    df = load_data(path, max_rows=max_rows)
    column_summary = classify_columns(df)
    category = infer_goal_category(goal, column_summary)

    charts = build_chart_specs(category, grammar, column_summary, goal)
    encoding_notes = grammar.get("encoding_channels", {})

    return {
        "file": path,
        "goal": goal or f"auto:{category}",
        "goal_category": category,
        "data_summary": {
            "rows": len(df),
            "columns": len(df.columns),
            **column_summary,
        },
        "charts": charts,
        "encoding_guidance": encoding_notes,
        "color_palette": grammar.get("default_palette", "viridis"),
        "layout": "grid",
        "grammar_version": grammar.get("version", "unknown"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan visualizations from data characteristics and goal")
    parser.add_argument("path", help="Path to CSV, JSON, JSONL, XLSX, Parquet, or TSV file")
    parser.add_argument("--goal", default=None, help="Analysis goal (e.g. compare groups, show trend)")
    parser.add_argument(
        "--grammar",
        default=str(DEFAULT_GRAMMAR),
        help="Path to visualization-grammar.json",
    )
    parser.add_argument("--max-rows", type=int, default=None, help="Maximum rows to sample for planning")
    args = parser.parse_args()

    try:
        result = build_plan(args.path, args.goal, Path(args.grammar), args.max_rows)
        print(json.dumps(result, indent=2, default=str))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()