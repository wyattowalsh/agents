#!/usr/bin/env python3
"""Automated EDA profiler. Input: CSV/JSON file path. Output: JSON profile."""

import argparse
import json
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print(json.dumps({"error": "pandas not installed. Run: uv pip install pandas"}))
    sys.exit(1)


def load_data(path: str, max_rows: int | None = None) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        print(json.dumps({"error": f"File not found: {path}"}), file=sys.stderr)
        sys.exit(1)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(p, nrows=max_rows)
    elif suffix in (".json", ".jsonl"):
        df = pd.read_json(p, lines=suffix == ".jsonl")
        if max_rows is not None:
            df = df.head(max_rows)
        return df
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(p, nrows=max_rows)
        return df
    elif suffix == ".parquet":
        df = pd.read_parquet(p)
        if max_rows is not None:
            df = df.head(max_rows)
        return df
    elif suffix == ".tsv":
        return pd.read_csv(p, sep="\t", nrows=max_rows)
    else:
        print(
            json.dumps({"error": f"Unsupported format: {suffix}"}), file=sys.stderr
        )
        sys.exit(1)


def profile_column(series: pd.Series) -> dict:
    info = {
        "dtype": str(series.dtype),
        "null_count": int(series.isnull().sum()),
        "null_pct": round(float(series.isnull().mean() * 100), 2),
        "unique_count": int(series.nunique()),
    }
    if pd.api.types.is_numeric_dtype(series):
        desc = series.describe()
        info["stats"] = {
            "mean": round(float(desc.get("mean", 0)), 4),
            "std": round(float(desc.get("std", 0)), 4),
            "min": float(desc.get("min", 0)),
            "25%": float(desc.get("25%", 0)),
            "50%": float(desc.get("50%", 0)),
            "75%": float(desc.get("75%", 0)),
            "max": float(desc.get("max", 0)),
        }
        skew = series.skew()
        kurt = series.kurtosis()
        info["skewness"] = round(float(skew), 4) if pd.notna(skew) else None
        info["kurtosis"] = round(float(kurt), 4) if pd.notna(kurt) else None
    elif pd.api.types.is_string_dtype(series) or series.dtype.name == "category":
        top_values = series.value_counts().head(5)
        info["top_values"] = {str(k): int(v) for k, v in top_values.items()}
        info["is_potential_id"] = info["unique_count"] == len(series)
    elif pd.api.types.is_datetime64_any_dtype(series):
        info["min_date"] = str(series.min())
        info["max_date"] = str(series.max())
        info["date_range_days"] = (series.max() - series.min()).days
    return info


def compute_correlations(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) < 2:
        return {}
    corr = df[numeric_cols].corr()
    pairs = []
    for i, c1 in enumerate(numeric_cols):
        for c2 in numeric_cols[i + 1 :]:
            val = corr.loc[c1, c2]
            if pd.notna(val) and abs(val) > 0.3:
                pairs.append(
                    {"col1": c1, "col2": c2, "correlation": round(float(val), 4)}
                )
    pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return pairs[:20]


def detect_missing_patterns(df: pd.DataFrame) -> dict:
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if missing.empty:
        return {"pattern": "no_missing", "columns": []}
    total = len(df)
    categories = {"high_missing": [], "moderate_missing": [], "low_missing": []}
    for col, count in missing.items():
        pct = count / total * 100
        entry = {"column": str(col), "count": int(count), "pct": round(pct, 2)}
        if pct > 50:
            categories["high_missing"].append(entry)
        elif pct > 10:
            categories["moderate_missing"].append(entry)
        else:
            categories["low_missing"].append(entry)
    # Check for co-occurrence
    if len(missing) >= 2:
        missing_cols = missing.index.tolist()[:10]
        co_missing = df[missing_cols].isnull()
        co_occur = []
        for i, c1 in enumerate(missing_cols):
            for c2 in missing_cols[i + 1 :]:
                both = (co_missing[c1] & co_missing[c2]).sum()
                if both > 0:
                    co_occur.append(
                        {"col1": str(c1), "col2": str(c2), "co_missing": int(both)}
                    )
        categories["co_occurrence"] = co_occur[:10]
    return categories


def detect_duplicates(df: pd.DataFrame) -> dict:
    total = len(df)
    dup_count = df.duplicated().sum()
    return {
        "total_rows": total,
        "duplicate_rows": int(dup_count),
        "duplicate_pct": round(float(dup_count / total * 100), 2) if total > 0 else 0,
    }


def profile_dataset(path: str, selected_columns: list[str] | None = None, max_rows: int | None = None) -> dict:
    df = load_data(path, max_rows=max_rows)
    result = {
        "file": path,
        "rows": len(df),
        "columns": len(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "column_profiles": {},
        "correlations": [],
        "missing_patterns": {},
        "duplicates": {},
        "dtype_summary": {},
    }
    # Dtype summary
    dtype_counts = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
    result["dtype_summary"] = dtype_counts

    # Column profiles
    profile_cols = df.columns
    if selected_columns:
        profile_cols = [c for c in profile_cols if c in selected_columns]
    for col in profile_cols:
        result["column_profiles"][col] = profile_column(df[col])

    # Correlations
    result["correlations"] = compute_correlations(df)

    # Missing patterns
    result["missing_patterns"] = detect_missing_patterns(df)

    # Duplicates
    result["duplicates"] = detect_duplicates(df)

    return result


def main():
    parser = argparse.ArgumentParser(description="Profile a dataset for EDA")
    parser.add_argument("path", help="Path to CSV, JSON, JSONL, XLSX, Parquet, or TSV file")
    parser.add_argument(
        "--columns", nargs="*", help="Specific columns to profile (default: all)"
    )
    parser.add_argument(
        "--max-rows", type=int, default=None, help="Maximum rows to read (for large files)"
    )
    args = parser.parse_args()

    try:
        result = profile_dataset(args.path, selected_columns=args.columns, max_rows=args.max_rows)
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
