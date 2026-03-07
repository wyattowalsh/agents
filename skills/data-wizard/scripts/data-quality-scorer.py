#!/usr/bin/env python3
"""Data quality assessment across 5 dimensions. Dependency: pandas.

Input: CSV/JSON file path
Output: JSON with dimension scores and overall quality score.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print(json.dumps({"error": "pandas not installed. Run: uv pip install pandas"}))
    sys.exit(1)


def load_data(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        print(json.dumps({"error": f"File not found: {path}"}), file=sys.stderr)
        sys.exit(1)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(p)
    elif suffix in (".json", ".jsonl"):
        return pd.read_json(p, lines=suffix == ".jsonl")
    elif suffix in (".xlsx", ".xls"):
        return pd.read_excel(p)
    elif suffix == ".parquet":
        return pd.read_parquet(p)
    elif suffix == ".tsv":
        return pd.read_csv(p, sep="\t")
    else:
        print(json.dumps({"error": f"Unsupported format: {suffix}"}), file=sys.stderr)
        sys.exit(1)


def score_completeness(df: pd.DataFrame) -> dict:
    """Missing values and null patterns."""
    total_cells = df.shape[0] * df.shape[1]
    missing_cells = df.isnull().sum().sum()
    completeness_ratio = 1 - (missing_cells / total_cells) if total_cells > 0 else 1.0

    col_scores = {}
    for col in df.columns:
        null_pct = df[col].isnull().mean()
        col_scores[col] = round(1 - null_pct, 4)

    worst_cols = sorted(col_scores.items(), key=lambda x: x[1])[:5]

    return {
        "score": round(completeness_ratio * 100, 2),
        "total_cells": int(total_cells),
        "missing_cells": int(missing_cells),
        "missing_pct": round(float(missing_cells / total_cells * 100), 2) if total_cells > 0 else 0,
        "worst_columns": [{"column": c, "completeness": round(s * 100, 2)} for c, s in worst_cols if s < 1.0],
    }


def score_consistency(df: pd.DataFrame) -> dict:
    """Type uniformity and format violations."""
    issues = []
    total_checks = 0
    passed_checks = 0

    for col in df.columns:
        total_checks += 1
        # Check mixed types
        non_null = df[col].dropna()
        if len(non_null) == 0:
            passed_checks += 1
            continue

        types = non_null.apply(type).nunique()
        if types > 1:
            type_counts = non_null.apply(type).value_counts().head(3)
            issues.append({
                "column": col,
                "issue": "mixed_types",
                "types": {str(t.__name__): int(c) for t, c in type_counts.items()},
            })
        elif df[col].dtype == "object":
            # Check casing only for string columns
            unique_raw = non_null.nunique()
            unique_lower = non_null.str.lower().nunique()
            if unique_raw > unique_lower:
                issues.append({
                    "column": col,
                    "issue": "inconsistent_casing",
                    "unique_raw": int(unique_raw),
                    "unique_normalized": int(unique_lower),
                })
            else:
                passed_checks += 1
        else:
            passed_checks += 1

    score = (passed_checks / total_checks * 100) if total_checks > 0 else 100
    return {
        "score": round(score, 2),
        "total_checks": total_checks,
        "passed": passed_checks,
        "issues": issues[:10],
    }


def score_accuracy(df: pd.DataFrame) -> dict:
    """Range violations and statistical outliers."""
    issues = []
    total_checks = 0
    passed_checks = 0

    for col in df.select_dtypes(include="number").columns:
        total_checks += 1
        series = df[col].dropna()
        if len(series) < 4:
            passed_checks += 1
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 3 * iqr
        upper = q3 + 3 * iqr
        outliers = ((series < lower) | (series > upper)).sum()
        outlier_pct = outliers / len(series) * 100

        if outlier_pct > 5:
            issues.append({
                "column": col,
                "issue": "high_outlier_rate",
                "outlier_count": int(outliers),
                "outlier_pct": round(outlier_pct, 2),
                "range": [float(series.min()), float(series.max())],
            })
        else:
            passed_checks += 1

    # Check for negative values in typically non-negative columns
    for col in df.select_dtypes(include="number").columns:
        if any(hint in col.lower() for hint in ["age", "price", "count", "quantity", "amount", "revenue", "salary"]):
            total_checks += 1
            neg_count = (df[col].dropna() < 0).sum()
            if neg_count > 0:
                issues.append({
                    "column": col,
                    "issue": "unexpected_negatives",
                    "count": int(neg_count),
                })
            else:
                passed_checks += 1

    score = (passed_checks / total_checks * 100) if total_checks > 0 else 100
    return {
        "score": round(score, 2),
        "total_checks": total_checks,
        "passed": passed_checks,
        "issues": issues[:10],
    }


def score_timeliness(df: pd.DataFrame) -> dict:
    """Stale records and temporal gaps."""
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    # Try to parse object columns as dates
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().sum() > len(df) * 0.5:
                datetime_cols.append(col)
                df[col + "_parsed"] = parsed
        except (ValueError, TypeError):
            pass

    if not datetime_cols:
        return {
            "score": 100.0,
            "note": "No datetime columns detected — timeliness not assessed",
            "datetime_columns": [],
        }

    issues = []
    total_checks = 0
    passed_checks = 0

    for col in datetime_cols:
        total_checks += 1
        parsed_col = col + "_parsed" if col + "_parsed" in df.columns else col
        series = pd.to_datetime(df[parsed_col], errors="coerce").dropna()
        if len(series) == 0:
            passed_checks += 1
            continue

        max_date = series.max()
        now = pd.Timestamp.now()
        staleness_days = (now - max_date).days

        if staleness_days > 365:
            issues.append({
                "column": col,
                "issue": "stale_data",
                "most_recent": str(max_date.date()),
                "days_old": int(staleness_days),
            })
        else:
            passed_checks += 1

    score = (passed_checks / total_checks * 100) if total_checks > 0 else 100
    return {
        "score": round(score, 2),
        "datetime_columns": datetime_cols,
        "issues": issues[:10],
    }


def score_uniqueness(df: pd.DataFrame) -> dict:
    """Duplicates and near-duplicates."""
    total = len(df)
    if total == 0:
        return {"score": 100.0, "total_rows": 0, "duplicate_rows": 0}

    dup_count = df.duplicated().sum()
    dup_pct = dup_count / total * 100

    # Check for potential ID columns with non-unique values
    id_issues = []
    for col in df.columns:
        if any(hint in col.lower() for hint in ["id", "key", "uuid", "code"]):
            if df[col].nunique() < total * 0.99:
                id_issues.append({
                    "column": col,
                    "unique_count": int(df[col].nunique()),
                    "total_rows": total,
                    "unique_pct": round(df[col].nunique() / total * 100, 2),
                })

    score = max(0, 100 - dup_pct * 2)
    return {
        "score": round(score, 2),
        "total_rows": total,
        "duplicate_rows": int(dup_count),
        "duplicate_pct": round(dup_pct, 2),
        "potential_id_issues": id_issues,
    }


def compute_overall(dimensions: dict) -> dict:
    weights = {
        "completeness": 0.25,
        "consistency": 0.20,
        "accuracy": 0.20,
        "timeliness": 0.15,
        "uniqueness": 0.20,
    }
    weighted_sum = sum(
        dimensions[dim]["score"] * weights[dim] for dim in weights
    )
    grade = (
        "A" if weighted_sum >= 90
        else "B" if weighted_sum >= 75
        else "C" if weighted_sum >= 60
        else "D" if weighted_sum >= 40
        else "F"
    )
    return {
        "overall_score": round(weighted_sum, 2),
        "grade": grade,
        "weights": weights,
    }


def main():
    parser = argparse.ArgumentParser(description="Score data quality across 5 dimensions")
    parser.add_argument("path", help="Path to CSV, JSON, JSONL, XLSX, Parquet, or TSV file")
    args = parser.parse_args()

    try:
        df = load_data(args.path)
        dimensions = {
            "completeness": score_completeness(df),
            "consistency": score_consistency(df),
            "accuracy": score_accuracy(df),
            "timeliness": score_timeliness(df),
            "uniqueness": score_uniqueness(df),
        }
        overall = compute_overall(dimensions)
        result = {
            "file": args.path,
            "rows": len(df),
            "columns": len(df.columns),
            "dimensions": dimensions,
            "overall": overall,
        }
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
