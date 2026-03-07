#!/usr/bin/env python3
"""Parse SQL DDL into structured JSON. Detect normalization level and structural issues.

Usage:
    python schema-analyzer.py --ddl <path>
    python schema-analyzer.py --ddl -        # read from stdin

Output (JSON to stdout):
    {
        "tables": [{
            "name": str,
            "columns": [{"name": str, "type": str, "nullable": bool, "default": str|null, "constraints": [str]}],
            "indexes": [{"name": str, "columns": [str], "unique": bool}],
            "foreign_keys": [{"columns": [str], "ref_table": str, "ref_columns": [str], "on_delete": str}],
            "primary_key": [str]
        }],
        "normalization_level": str,
        "issues": [{"severity": str, "table": str, "message": str}]
    }
"""

import argparse
import json
import re
import sys


def parse_ddl(sql: str) -> dict:
    """Parse CREATE TABLE statements from SQL DDL."""
    tables = []
    issues = []

    # Find all CREATE TABLE statements using paren-scanning to handle nested parens
    create_header = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?\s*\(",
        re.IGNORECASE,
    )
    for match in create_header.finditer(sql):
        table_name = match.group(1).lower()
        start = match.end()  # position after opening (
        depth = 1
        i = start
        while i < len(sql) and depth > 0:
            if sql[i] == "(":
                depth += 1
            elif sql[i] == ")":
                depth -= 1
            i += 1
        body = sql[start : i - 1]
        table = parse_table_body(table_name, body, issues)
        tables.append(table)

    # Find standalone CREATE INDEX statements
    index_pattern = re.compile(
        r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?\s+ON\s+[`\"]?(\w+)[`\"]?\s*(?:USING\s+\w+\s*)?\(([^)]+)\)",
        re.IGNORECASE,
    )
    for match in index_pattern.finditer(sql):
        idx_name = match.group(1)
        tbl_name = match.group(2).lower()
        cols = [c.strip().strip("`\"").split()[0] for c in match.group(3).split(",")]
        is_unique = "UNIQUE" in match.group(0).upper().split("INDEX")[0]

        for table in tables:
            if table["name"] == tbl_name:
                table["indexes"].append(
                    {"name": idx_name, "columns": cols, "unique": is_unique}
                )
                break

    normalization = assess_normalization(tables, issues)

    # Check for common issues
    check_issues(tables, issues)

    return {
        "tables": tables,
        "normalization_level": normalization,
        "issues": issues,
    }


def parse_table_body(table_name: str, body: str, issues: list) -> dict:
    """Parse the body of a CREATE TABLE statement."""
    columns = []
    indexes = []
    foreign_keys = []
    primary_key = []

    # Split by commas, but respect parentheses
    parts = split_respecting_parens(body)

    for part in parts:
        part = part.strip()
        upper = part.upper()

        if upper.startswith("PRIMARY KEY"):
            pk_match = re.search(r"\(([^)]+)\)", part)
            if pk_match:
                primary_key = [
                    c.strip().strip("`\"") for c in pk_match.group(1).split(",")
                ]
        elif upper.startswith("FOREIGN KEY") or (upper.startswith("CONSTRAINT") and "FOREIGN KEY" in upper):
            fk = parse_foreign_key(part)
            if fk:
                foreign_keys.append(fk)
        elif upper.startswith("UNIQUE"):
            uq_match = re.search(r"\(([^)]+)\)", part)
            if uq_match:
                cols = [
                    c.strip().strip("`\"") for c in uq_match.group(1).split(",")
                ]
                name = f"uq_{table_name}_{'_'.join(cols)}"
                indexes.append({"name": name, "columns": cols, "unique": True})
        elif upper.startswith("CONSTRAINT") and "UNIQUE" in upper:
            # Extract columns from CONSTRAINT name UNIQUE (col1, col2)
            uq_match = re.search(r"UNIQUE\s*\(([^)]+)\)", part, re.IGNORECASE)
            if uq_match:
                cols = [c.strip().strip("`\"'") for c in uq_match.group(1).split(",")]
                name = f"uq_{table_name}_{'_'.join(cols)}"
                indexes.append({"name": name, "columns": cols, "unique": True})
        elif upper.startswith("CHECK") or (upper.startswith("CONSTRAINT") and "CHECK" in upper):
            continue  # Skip check constraints for structural analysis
        elif upper.startswith("INDEX") or upper.startswith("KEY"):
            idx_match = re.search(r"(?:INDEX|KEY)\s+[`\"]?(\w+)[`\"]?\s*\(([^)]+)\)", part, re.IGNORECASE)
            if idx_match:
                cols = [c.strip().strip("`\"").split()[0] for c in idx_match.group(2).split(",")]
                indexes.append({"name": idx_match.group(1), "columns": cols, "unique": False})
        else:
            col = parse_column(part)
            if col:
                columns.append(col)
                if "PRIMARY KEY" in upper:
                    primary_key.append(col["name"])

    return {
        "name": table_name,
        "columns": columns,
        "indexes": indexes,
        "foreign_keys": foreign_keys,
        "primary_key": primary_key,
    }


def parse_column(definition: str) -> dict | None:
    """Parse a column definition."""
    # Match: column_name TYPE [constraints...]
    match = re.match(
        r"[`\"]?(\w+)[`\"]?\s+(\w+(?:\([^)]*\))?(?:\[\])?)",
        definition.strip(),
        re.IGNORECASE,
    )
    if not match:
        return None

    name = match.group(1).lower()
    col_type = match.group(2).upper()
    upper = definition.upper()

    nullable = "NOT NULL" not in upper
    default = None
    default_match = re.search(r"DEFAULT\s+(.+?)(?:\s+(?:NOT\s+NULL|NULL|PRIMARY|UNIQUE|CHECK|REFERENCES|CONSTRAINT)|$)", definition, re.IGNORECASE)
    if default_match:
        default = default_match.group(1).strip().rstrip(",")

    constraints = []
    if "NOT NULL" in upper:
        constraints.append("NOT NULL")
    if "PRIMARY KEY" in upper:
        constraints.append("PRIMARY KEY")
    if "UNIQUE" in upper and "PRIMARY" not in upper:
        constraints.append("UNIQUE")
    if "REFERENCES" in upper:
        constraints.append("REFERENCES")

    return {
        "name": name,
        "type": col_type,
        "nullable": nullable,
        "default": default,
        "constraints": constraints,
    }


def parse_foreign_key(definition: str) -> dict | None:
    """Parse a FOREIGN KEY constraint."""
    fk_match = re.search(
        r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+[`\"]?(\w+)[`\"]?\s*\(([^)]+)\)",
        definition,
        re.IGNORECASE,
    )
    if not fk_match:
        return None

    cols = [c.strip().strip("`\"") for c in fk_match.group(1).split(",")]
    ref_table = fk_match.group(2).lower()
    ref_cols = [c.strip().strip("`\"") for c in fk_match.group(3).split(",")]

    on_delete = "NO ACTION"
    del_match = re.search(r"ON\s+DELETE\s+(CASCADE|SET\s+NULL|SET\s+DEFAULT|RESTRICT|NO\s+ACTION)", definition, re.IGNORECASE)
    if del_match:
        on_delete = del_match.group(1).upper()

    return {
        "columns": cols,
        "ref_table": ref_table,
        "ref_columns": ref_cols,
        "on_delete": on_delete,
    }


def split_respecting_parens(text: str) -> list[str]:
    """Split by commas, respecting parenthesized groups."""
    parts = []
    depth = 0
    current = []
    for char in text:
        if char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current))
    return parts


def assess_normalization(tables: list, issues: list) -> str:
    """Assess the normalization level of the schema."""
    if not tables:
        return "unknown"

    level = "3NF"  # Assume 3NF until violations found

    for table in tables:
        col_names = [c["name"] for c in table["columns"]]

        # Check 1NF: comma-separated values (heuristic: columns named *_list, *_csv, tags)
        for col in table["columns"]:
            if any(pattern in col["name"] for pattern in ["_list", "_csv", "_tags", "_ids"]):
                if col["type"].startswith(("TEXT", "VARCHAR", "CHARACTER VARYING", "NVARCHAR")):
                    issues.append({
                        "severity": "warning",
                        "table": table["name"],
                        "message": f"Column '{col['name']}' may contain comma-separated values (1NF violation). Consider a junction table.",
                    })
                    level = "1NF"

        # Check for repeated column groups (1NF violation)
        numbered = re.findall(r"(\w+?)(\d+)$", " ".join(col_names))
        if len(numbered) >= 3:
            groups = {}
            for prefix, num in numbered:
                groups.setdefault(prefix, []).append(num)
            for prefix, nums in groups.items():
                if len(nums) >= 3:
                    issues.append({
                        "severity": "warning",
                        "table": table["name"],
                        "message": f"Repeated column group '{prefix}1..{prefix}{max(nums)}' suggests 1NF violation. Consider a separate table.",
                    })
                    level = "1NF"

    return level


def check_issues(tables: list, issues: list) -> None:
    """Check for common structural issues."""
    table_names = {t["name"] for t in tables}

    for table in tables:
        # No primary key
        if not table["primary_key"]:
            issues.append({
                "severity": "critical",
                "table": table["name"],
                "message": "No primary key defined.",
            })

        # Foreign keys referencing non-existent tables
        for fk in table["foreign_keys"]:
            if fk["ref_table"] not in table_names:
                issues.append({
                    "severity": "warning",
                    "table": table["name"],
                    "message": f"Foreign key references table '{fk['ref_table']}' not found in this schema.",
                })

        # Columns with no type constraints that might benefit from NOT NULL
        for col in table["columns"]:
            if col["name"] in ("id", "created_at", "updated_at") and col["nullable"]:
                issues.append({
                    "severity": "info",
                    "table": table["name"],
                    "message": f"Column '{col['name']}' is nullable but is typically NOT NULL.",
                })

        # No indexes on foreign key columns
        indexed_cols = set()
        for idx in table["indexes"]:
            for c in idx["columns"]:
                indexed_cols.add(c)
        for pk_col in table["primary_key"]:
            indexed_cols.add(pk_col)

        for fk in table["foreign_keys"]:
            for fk_col in fk["columns"]:
                if fk_col not in indexed_cols:
                    issues.append({
                        "severity": "warning",
                        "table": table["name"],
                        "message": f"Foreign key column '{fk_col}' has no index. JOINs and cascading deletes will be slow.",
                    })


def main():
    parser = argparse.ArgumentParser(description="Analyze SQL DDL schema structure")
    parser.add_argument("--ddl", required=True, help="Path to DDL file or '-' for stdin")
    args = parser.parse_args()

    if args.ddl == "-":
        sql = sys.stdin.read()
    else:
        try:
            with open(args.ddl) as f:
                sql = f.read()
        except FileNotFoundError:
            print(json.dumps({"error": f"File not found: {args.ddl}"}), file=sys.stderr)
            sys.exit(1)

    result = parse_ddl(sql)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
