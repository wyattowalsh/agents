#!/usr/bin/env python3
"""Visualization renderer. Input: chart plan JSON + data path. Output: PNG/HTML assets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
except ImportError:
    print(json.dumps({"error": "pandas not installed. Run: uv pip install pandas"}))
    sys.exit(1)

MAX_BAR_CATEGORIES = 10


def load_data(path: str, max_rows: int | None = None) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
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
    raise ValueError(f"Unsupported format: {suffix}")


def load_plan(plan_arg: str) -> dict:
    plan_path = Path(plan_arg)
    if plan_path.exists():
        return json.loads(plan_path.read_text(encoding="utf-8"))
    return json.loads(plan_arg)


def import_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except ImportError:
        return None


def import_plotly():
    try:
        import plotly.express as px
        import plotly.graph_objects as go

        return px, go
    except ImportError:
        return None, None


def safe_filename(chart_id: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in chart_id)


def _validate_bar_columns(df: pd.DataFrame, x_col: str, y_col: str, color_col: str | None) -> None:
    if x_col not in df.columns:
        raise ValueError(f"Column not found for bar chart x: {x_col}")
    if y_col != "__count__" and y_col not in df.columns:
        raise ValueError(f"Column not found for bar chart y: {y_col}")
    if color_col and color_col not in df.columns:
        raise ValueError(f"Column not found for bar chart color: {color_col}")


def _limit_bar_categories(
    pivot: pd.DataFrame,
    chart_type: str,
    max_categories: int = MAX_BAR_CATEGORIES,
) -> tuple[pd.DataFrame, str]:
    """Cap x-axis categories; fall back to simple bar when over limit."""
    if len(pivot.index) <= max_categories:
        return pivot, chart_type
    totals = pivot.sum(axis=1).sort_values(ascending=False)
    limited = pivot.loc[totals.head(max_categories).index]
    return limited, "bar_chart"


def prepare_bar_chart_data(
    df: pd.DataFrame,
    enc: dict,
    chart_type: str,
) -> tuple[pd.DataFrame, str, str, str | None, str]:
    """Return pivot table, effective chart type, x/y/color columns, and y label."""
    x_col = enc.get("x")
    y_col = enc.get("y")
    color_col = enc.get("color")
    _validate_bar_columns(df, x_col, y_col, color_col)

    effective_type = chart_type
    use_color = (
        color_col
        and effective_type in ("grouped_bar", "stacked_bar")
    )

    if y_col == "__count__":
        if use_color:
            grouped = (
                df.groupby([x_col, color_col], dropna=False)
                .size()
                .reset_index(name="count")
            )
            pivot = grouped.pivot(index=x_col, columns=color_col, values="count").fillna(0)
            y_label = "count"
        else:
            counts = df[x_col].value_counts().sort_index()
            pivot = counts.to_frame(name="count")
            effective_type = "bar_chart"
            y_label = "count"
    else:
        if use_color:
            grouped = (
                df.groupby([x_col, color_col], dropna=False)[y_col]
                .mean()
                .reset_index()
            )
            pivot = grouped.pivot(index=x_col, columns=color_col, values=y_col).fillna(0)
            y_label = y_col
        else:
            means = df.groupby(x_col, dropna=False)[y_col].mean().sort_index()
            pivot = means.to_frame(name=y_col)
            effective_type = "bar_chart"
            y_label = y_col

    pivot, effective_type = _limit_bar_categories(pivot, effective_type)
    if effective_type == "bar_chart":
        if pivot.shape[1] > 1:
            pivot = pivot.sum(axis=1).to_frame(name=y_label)
        color_col = None

    return pivot, effective_type, x_col, color_col, y_label


def render_with_matplotlib(df: pd.DataFrame, chart: dict, output_path: Path) -> None:
    plt = import_matplotlib()
    if plt is None:
        raise RuntimeError("matplotlib not installed. Run: uv pip install matplotlib")

    chart_type = chart.get("type", "bar_chart")
    enc = chart.get("encodings", {})
    title = chart.get("title", chart.get("id", "chart"))

    fig, ax = plt.subplots(figsize=(8, 5))

    if chart_type == "histogram":
        col = enc.get("x")
        if col not in df.columns:
            raise ValueError(f"Column not found for histogram: {col}")
        bins = enc.get("bins", 30)
        ax.hist(df[col].dropna(), bins=bins, edgecolor="black", alpha=0.75)
        ax.set_xlabel(col)
        ax.set_ylabel("count")

    elif chart_type in ("bar_chart", "grouped_bar", "stacked_bar"):
        pivot, effective_type, x_col, color_col, y_label = prepare_bar_chart_data(df, enc, chart_type)
        categories = pivot.index.astype(str)
        value_col = pivot.columns[0]

        if effective_type == "grouped_bar" and pivot.shape[1] > 1:
            x_pos = np.arange(len(categories))
            n_groups = len(pivot.columns)
            width = 0.8 / max(n_groups, 1)
            for i, series_name in enumerate(pivot.columns):
                offset = (i - n_groups / 2 + 0.5) * width
                ax.bar(
                    x_pos + offset,
                    pivot[series_name].values,
                    width,
                    label=str(series_name),
                )
            ax.set_xticks(x_pos)
            ax.set_xticklabels(categories, rotation=45, ha="right")
            ax.legend(fontsize=8)
        elif effective_type == "stacked_bar" and pivot.shape[1] > 1:
            bottom = np.zeros(len(categories))
            for series_name in pivot.columns:
                values = pivot[series_name].values
                ax.bar(categories, values, bottom=bottom, label=str(series_name))
                bottom = bottom + values
            ax.legend(fontsize=8)
            plt.xticks(rotation=45, ha="right")
        else:
            ax.bar(categories, pivot[value_col].values)
            plt.xticks(rotation=45, ha="right")

        ax.set_xlabel(x_col)
        ax.set_ylabel(y_label)

    elif chart_type == "scatter_plot":
        x_col = enc.get("x")
        y_col = enc.get("y")
        color_col = enc.get("color")
        for col in (x_col, y_col):
            if col not in df.columns:
                raise ValueError(f"Column not found for scatter plot: {col}")
        subset = df[[x_col, y_col] + ([color_col] if color_col and color_col in df.columns else [])].dropna()
        if color_col and color_col in df.columns:
            for label, group in subset.groupby(color_col):
                ax.scatter(group[x_col], group[y_col], label=str(label), alpha=0.7)
            ax.legend(fontsize=8)
        else:
            ax.scatter(subset[x_col], subset[y_col], alpha=0.7)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)

    elif chart_type == "line_chart":
        x_col = enc.get("x")
        y_col = enc.get("y")
        for col in (x_col, y_col):
            if col not in df.columns:
                raise ValueError(f"Column not found for line chart: {col}")
        series = df[[x_col, y_col]].dropna().sort_values(x_col)
        ax.plot(series[x_col], series[y_col], marker="o", linewidth=1.5)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        plt.xticks(rotation=45, ha="right")

    elif chart_type == "box_plot":
        x_col = enc.get("x")
        y_col = enc.get("y")
        for col in (x_col, y_col):
            if col not in df.columns:
                raise ValueError(f"Column not found for box plot: {col}")
        groups = []
        labels = []
        for label, group in df.groupby(x_col, dropna=False):
            values = group[y_col].dropna()
            if len(values) == 0:
                continue
            groups.append(values)
            labels.append(str(label))
        ax.boxplot(groups, labels=labels)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        plt.xticks(rotation=45, ha="right")

    elif chart_type == "heatmap":
        cols = enc.get("columns", [])
        numeric = df.select_dtypes(include="number")
        if cols:
            missing = [c for c in cols if c not in df.columns]
            if missing:
                raise ValueError(f"Columns not found for heatmap: {missing}")
            numeric = df[cols]
        if numeric.shape[1] < 2:
            raise ValueError("Heatmap requires at least two numeric columns")
        corr = numeric.corr()
        im = ax.imshow(corr.values, cmap="viridis", aspect="auto", vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right")
        ax.set_yticklabels(corr.columns)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    else:
        raise ValueError(f"Unsupported chart type for matplotlib: {chart_type}")

    ax.set_title(title)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def render_with_plotly(df: pd.DataFrame, chart: dict, output_path: Path) -> None:
    px, go = import_plotly()
    if px is None or go is None:
        raise RuntimeError("plotly not installed. Run: uv pip install plotly")

    chart_type = chart.get("type", "bar_chart")
    enc = chart.get("encodings", {})
    title = chart.get("title", chart.get("id", "chart"))
    fig = None

    if chart_type == "histogram":
        col = enc.get("x")
        fig = px.histogram(df, x=col, title=title, nbins=enc.get("bins", 30))
    elif chart_type in ("bar_chart", "grouped_bar", "stacked_bar"):
        pivot, effective_type, x_col, color_col, y_label = prepare_bar_chart_data(df, enc, chart_type)
        value_col = pivot.columns[0]

        if effective_type in ("grouped_bar", "stacked_bar") and color_col and pivot.shape[1] > 1:
            plot_df = pivot.reset_index().melt(
                id_vars=[x_col],
                var_name=color_col,
                value_name=y_label,
            )
            barmode = "stack" if effective_type == "stacked_bar" else "group"
            fig = px.bar(
                plot_df,
                x=x_col,
                y=y_label,
                color=color_col,
                title=title,
                barmode=barmode,
            )
        else:
            plot_df = pivot.reset_index()
            fig = px.bar(plot_df, x=x_col, y=value_col, title=title)
    elif chart_type == "scatter_plot":
        fig = px.scatter(
            df,
            x=enc.get("x"),
            y=enc.get("y"),
            color=enc.get("color"),
            title=title,
        )
    elif chart_type == "line_chart":
        fig = px.line(df.sort_values(enc.get("x")), x=enc.get("x"), y=enc.get("y"), title=title)
    elif chart_type == "box_plot":
        fig = px.box(df, x=enc.get("x"), y=enc.get("y"), title=title)
    elif chart_type == "heatmap":
        cols = enc.get("columns", [])
        numeric = df.select_dtypes(include="number")
        if cols:
            numeric = df[cols]
        corr = numeric.corr()
        fig = px.imshow(corr, text_auto=True, title=title, color_continuous_scale="Viridis")
    else:
        raise ValueError(f"Unsupported chart type for plotly: {chart_type}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path), include_plotlyjs="cdn")


def render_chart(
    df: pd.DataFrame,
    chart: dict,
    output_dir: Path,
    fmt: str,
) -> dict:
    chart_id = chart.get("id", "chart")
    stem = safe_filename(chart_id)
    if fmt == "html":
        output_path = output_dir / f"{stem}.html"
        try:
            render_with_plotly(df, chart, output_path)
            engine = "plotly"
        except RuntimeError as plotly_err:
            # Fallback: matplotlib cannot write interactive HTML; surface dependency error.
            raise plotly_err
    else:
        output_path = output_dir / f"{stem}.png"
        render_with_matplotlib(df, chart, output_path)
        engine = "matplotlib"

    return {
        "chart_id": chart_id,
        "path": str(output_path.resolve()),
        "format": fmt,
        "engine": engine,
        "type": chart.get("type"),
        "title": chart.get("title"),
    }


def render_plan(
    plan: dict,
    data_path: str,
    output_dir: Path,
    fmt: str,
    max_rows: int | None,
) -> dict:
    charts = plan.get("charts", [])
    if not charts:
        return {"error": "Plan contains no charts", "outputs": []}

    df = load_data(data_path, max_rows=max_rows)
    outputs: list[dict] = []
    errors: list[dict] = []

    for chart in charts:
        try:
            outputs.append(render_chart(df, chart, output_dir, fmt))
        except Exception as exc:
            errors.append({"chart_id": chart.get("id"), "error": str(exc)})

    result = {
        "status": "success" if outputs and not errors else ("partial" if outputs else "error"),
        "file": data_path,
        "output_dir": str(output_dir.resolve()),
        "format": fmt,
        "outputs": outputs,
    }
    if errors:
        result["errors"] = errors
    if not outputs:
        result["error"] = errors[0]["error"] if errors else "No charts rendered"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Render charts from a visualization plan")
    parser.add_argument("plan", help="Path to plan JSON or inline JSON string")
    parser.add_argument("data", help="Path to dataset used by the plan")
    parser.add_argument(
        "--output-dir",
        default="./data-wizard-viz",
        help="Directory for rendered chart files",
    )
    parser.add_argument(
        "--format",
        choices=["png", "html"],
        default="png",
        help="Output format (png=matplotlib, html=plotly)",
    )
    parser.add_argument("--max-rows", type=int, default=None, help="Maximum rows to read from data")
    args = parser.parse_args()

    if args.format == "png" and import_matplotlib() is None:
        print(json.dumps({"error": "matplotlib not installed. Run: uv pip install matplotlib"}))
        sys.exit(1)
    if args.format == "html" and import_plotly()[0] is None:
        print(json.dumps({"error": "plotly not installed. Run: uv pip install plotly"}))
        sys.exit(1)

    try:
        plan = load_plan(args.plan)
        result = render_plan(plan, args.data, Path(args.output_dir), args.format, args.max_rows)
        print(json.dumps(result, indent=2, default=str))
        if result.get("status") == "error":
            sys.exit(1)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()