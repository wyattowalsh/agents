#!/usr/bin/env python3
"""Recommend indexes based on schema and query patterns.

Usage:
    python index-recommender.py --schema <path> --queries <path>
    python index-recommender.py --schema <path> --queries -    # queries from stdin

Output (JSON to stdout):
    {
        "recommendations": [{
            "table": str,
            "columns": [str],
            "type": str,
            "rationale": str,
            "estimated_impact": str,
            "write_overhead": str
        }],
        "existing_indexes": [{"table": str, "name": str, "columns": [str]}],
        "coverage": {"total_patterns": int, "covered": int, "uncovered": int}
    }
"""

import argparse
import json
import re
import sys


def parse_schema_indexes(sql: str) -> list[dict]:
    """Extract existing indexes from schema DDL."""
    indexes = []

    # Inline indexes in CREATE TABLE
    create_pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?\s*\((.*?)\)\s*;",
        re.IGNORECASE | re.DOTALL,
    )
    for match in create_pattern.finditer(sql):
        table = match.group(1).lower()
        body = match.group(2)

        # Primary key
        pk_match = re.search(r"PRIMARY\s+KEY\s*\(([^)]+)\)", body, re.IGNORECASE)
        if pk_match:
            cols = [c.strip().strip("`\"") for c in pk_match.group(1).split(",")]
            indexes.append({"table": table, "name": f"pk_{table}", "columns": cols})

        # Inline column PKs
        for col_match in re.finditer(r"[`\"]?(\w+)[`\"]?\s+\w+[^,]*PRIMARY\s+KEY", body, re.IGNORECASE):
            indexes.append({"table": table, "name": f"pk_{table}", "columns": [col_match.group(1).lower()]})

        # UNIQUE constraints
        for uq_match in re.finditer(r"UNIQUE\s*\(([^)]+)\)", body, re.IGNORECASE):
            cols = [c.strip().strip("`\"") for c in uq_match.group(1).split(",")]
            indexes.append({"table": table, "name": f"uq_{table}_{'_'.join(cols)}", "columns": cols})

    # Standalone CREATE INDEX
    idx_pattern = re.compile(
        r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?\s+ON\s+[`\"]?(\w+)[`\"]?\s*(?:USING\s+\w+\s*)?\(([^)]+)\)",
        re.IGNORECASE,
    )
    for match in idx_pattern.finditer(sql):
        name = match.group(1)
        table = match.group(2).lower()
        cols = [c.strip().strip("`\"").split()[0] for c in match.group(3).split(",")]
        indexes.append({"table": table, "name": name, "columns": cols})

    return indexes


def extract_query_patterns(queries_text: str) -> list[dict]:
    """Extract table and column access patterns from SQL queries."""
    patterns = []

    for line in queries_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("--"):
            continue

        pattern = analyze_query(line)
        if pattern:
            patterns.append(pattern)

    return patterns


def analyze_query(sql: str) -> dict | None:
    """Analyze a single SQL query for index opportunities."""
    sql_upper = re.sub(r"\s+", " ", sql).upper().strip()

    # Extract FROM table
    from_match = re.search(r"FROM\s+[`\"]?(\w+)[`\"]?", sql_upper)
    if not from_match:
        return None

    table = from_match.group(1).lower()

    # Extract WHERE columns
    where_cols = []
    where_match = re.search(r"WHERE\s+(.+?)(?:ORDER|GROUP|LIMIT|HAVING|UNION|$)", sql_upper)
    if where_match:
        where_clause = where_match.group(1)
        # Find column = ?, column > ?, column IN, column LIKE, etc.
        for col_match in re.finditer(r"[`\"]?(\w+)[`\"]?\s*(?:=|>|<|>=|<=|!=|<>|IN|LIKE|IS|BETWEEN)", where_clause):
            col = col_match.group(1).lower()
            if col not in ("and", "or", "not", "null", "true", "false", "select"):
                where_cols.append(col)

    # Extract ORDER BY columns
    order_cols = []
    order_match = re.search(r"ORDER\s+BY\s+(.+?)(?:LIMIT|OFFSET|$)", sql_upper)
    if order_match:
        for col_match in re.finditer(r"[`\"]?(\w+)[`\"]?", order_match.group(1)):
            col = col_match.group(1).lower()
            if col not in ("asc", "desc"):
                order_cols.append(col)

    # Extract JOIN columns
    join_cols = []
    for join_match in re.finditer(r"JOIN\s+[`\"]?(\w+)[`\"]?\s+\w+\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)", sql_upper):
        left_table = join_match.group(2).lower()
        left_col = join_match.group(3).lower()
        right_table = join_match.group(4).lower()
        right_col = join_match.group(5).lower()
        # Add each column to the correct table
        if left_table == table.lower():
            join_cols.append(left_col)
        if right_table == table.lower():
            join_cols.append(right_col)

    # Detect query type
    query_type = "point_lookup"
    if re.search(r"(>|<|>=|<=|BETWEEN)", sql_upper):
        query_type = "range_scan"
    if "GROUP BY" in sql_upper:
        query_type = "aggregation"
    if "JOIN" in sql_upper:
        query_type = "join"
    if "LIKE" in sql_upper:
        query_type = "pattern_match"

    return {
        "table": table,
        "where_columns": where_cols,
        "order_columns": order_cols,
        "join_columns": join_cols,
        "query_type": query_type,
        "raw": sql.strip()[:100],
    }


def recommend_indexes(patterns: list[dict], existing: list[dict]) -> list[dict]:
    """Generate index recommendations based on query patterns and existing indexes."""
    recommendations = []
    existing_by_table = {}
    for idx in existing:
        existing_by_table.setdefault(idx["table"], []).append(idx)

    seen = set()

    for pattern in patterns:
        table = pattern["table"]
        table_indexes = existing_by_table.get(table, [])

        # Check WHERE columns need indexing
        where_cols = pattern["where_columns"]
        if where_cols:
            # Check if existing index covers these columns (leftmost prefix)
            covered = False
            for idx in table_indexes:
                if idx["columns"][:len(where_cols)] == where_cols:
                    covered = True
                    break

            if not covered:
                key = (table, tuple(where_cols))
                if key not in seen:
                    seen.add(key)
                    idx_type = "B-tree"
                    if pattern["query_type"] == "pattern_match":
                        idx_type = "GIN (trigram)"

                    recommendations.append({
                        "table": table,
                        "columns": where_cols,
                        "type": idx_type,
                        "rationale": f"Covers WHERE clause on {', '.join(where_cols)} ({pattern['query_type']})",
                        "estimated_impact": "high" if len(where_cols) == 1 else "medium",
                        "write_overhead": "low" if len(where_cols) <= 2 else "medium",
                    })

        # Check ORDER BY columns need coverage
        order_cols = pattern["order_columns"]
        if order_cols and where_cols:
            composite = where_cols + [c for c in order_cols if c not in where_cols]
            covered = False
            for idx in table_indexes:
                if idx["columns"][:len(composite)] == composite:
                    covered = True
                    break
            if not covered:
                key = (table, tuple(composite))
                if key not in seen:
                    seen.add(key)
                    recommendations.append({
                        "table": table,
                        "columns": composite,
                        "type": "B-tree",
                        "rationale": "Composite index for WHERE + ORDER BY (avoids sort)",
                        "estimated_impact": "medium",
                        "write_overhead": "medium",
                    })

        # Check JOIN columns
        for jc in pattern["join_columns"]:
            covered = False
            for idx in table_indexes:
                if idx["columns"][0] == jc:
                    covered = True
                    break
            if not covered:
                key = (table, (jc,))
                if key not in seen:
                    seen.add(key)
                    recommendations.append({
                        "table": table,
                        "columns": [jc],
                        "type": "B-tree",
                        "rationale": f"Index on JOIN column '{jc}' for efficient lookups",
                        "estimated_impact": "high",
                        "write_overhead": "low",
                    })

    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Recommend indexes based on schema and queries")
    parser.add_argument("--schema", required=True, help="Path to schema DDL file")
    parser.add_argument("--queries", required=True, help="Path to file with SQL queries (one per line), or '-' for stdin")
    args = parser.parse_args()

    # Read schema
    try:
        with open(args.schema) as f:
            schema_sql = f.read()
    except FileNotFoundError:
        print(json.dumps({"error": f"Schema file not found: {args.schema}"}), file=sys.stderr)
        sys.exit(1)

    # Read queries
    if args.queries == "-":
        queries_text = sys.stdin.read()
    else:
        try:
            with open(args.queries) as f:
                queries_text = f.read()
        except FileNotFoundError:
            print(json.dumps({"error": f"Queries file not found: {args.queries}"}), file=sys.stderr)
            sys.exit(1)

    existing = parse_schema_indexes(schema_sql)
    patterns = extract_query_patterns(queries_text)
    recommendations = recommend_indexes(patterns, existing)

    # Coverage calculation
    covered = 0
    for pattern in patterns:
        where_cols = pattern["where_columns"]
        if not where_cols:
            covered += 1
            continue
        table = pattern["table"]
        for idx in existing:
            if idx["table"] == table and idx["columns"][:len(where_cols)] == where_cols:
                covered += 1
                break

    result = {
        "recommendations": recommendations,
        "existing_indexes": existing,
        "coverage": {
            "total_patterns": len(patterns),
            "covered": covered,
            "uncovered": len(patterns) - covered,
        },
    }

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
