#!/usr/bin/env python3
"""Analyze migration files for safety. Flag destructive operations and reversibility.

Usage:
    python migration-validator.py --path <migration_dir>
    python migration-validator.py --sql <file>

Output (JSON to stdout):
    {
        "migrations": [{
            "file": str,
            "operations": [{
                "type": str,
                "table": str,
                "reversible": bool,
                "data_loss_risk": bool,
                "backwards_compatible": bool,
                "details": str
            }]
        }],
        "issues": [{"severity": str, "file": str, "message": str}],
        "summary": {"total_operations": int, "reversible": int, "data_loss_risks": int}
    }
"""

import argparse
import json
import os
import re
import sys

# Operation classification rules
OPERATION_RULES = {
    "ADD COLUMN": {
        "reversible": True,
        "data_loss_risk": False,
        "backwards_compatible": True,  # unless NOT NULL without default
    },
    "DROP COLUMN": {
        "reversible": False,
        "data_loss_risk": True,
        "backwards_compatible": False,
    },
    "RENAME COLUMN": {
        "reversible": True,
        "data_loss_risk": False,
        "backwards_compatible": False,
    },
    "ALTER COLUMN": {
        "reversible": True,  # depends on type change
        "data_loss_risk": False,  # depends on narrowing
        "backwards_compatible": True,
    },
    "CREATE TABLE": {
        "reversible": True,
        "data_loss_risk": False,
        "backwards_compatible": True,
    },
    "DROP TABLE": {
        "reversible": False,
        "data_loss_risk": True,
        "backwards_compatible": False,
    },
    "RENAME TABLE": {
        "reversible": True,
        "data_loss_risk": False,
        "backwards_compatible": False,
    },
    "CREATE INDEX": {
        "reversible": True,
        "data_loss_risk": False,
        "backwards_compatible": True,
    },
    "DROP INDEX": {
        "reversible": True,
        "data_loss_risk": False,
        "backwards_compatible": True,
    },
    "ADD CONSTRAINT": {
        "reversible": True,
        "data_loss_risk": False,
        "backwards_compatible": False,  # locks table during validation; FK may fail on existing data
    },
    "DROP CONSTRAINT": {
        "reversible": True,
        "data_loss_risk": False,
        "backwards_compatible": True,
    },
    "TRUNCATE": {
        "reversible": False,
        "data_loss_risk": True,
        "backwards_compatible": False,
    },
    "DELETE": {
        "reversible": False,
        "data_loss_risk": True,
        "backwards_compatible": True,
    },
    "UPDATE": {
        "reversible": False,
        "data_loss_risk": False,
        "backwards_compatible": True,
    },
}


def classify_sql(sql: str) -> list[dict]:
    """Classify SQL statements into operations."""
    operations = []
    # Normalize whitespace
    sql_clean = re.sub(r"\s+", " ", sql).strip()

    patterns = [
        (r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+ADD\s+COLUMN", "ADD COLUMN"),
        (r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+DROP\s+COLUMN", "DROP COLUMN"),
        (r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+RENAME\s+COLUMN", "RENAME COLUMN"),
        (r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+ALTER\s+COLUMN", "ALTER COLUMN"),
        (r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+(?:MODIFY|CHANGE)\s+COLUMN", "ALTER COLUMN"),
        (r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+ADD\s+(?:CONSTRAINT|FOREIGN|UNIQUE|CHECK)", "ADD CONSTRAINT"),
        (r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+DROP\s+CONSTRAINT", "DROP CONSTRAINT"),
        (r"ALTER\s+TABLE\s+[`\"]?(\w+)[`\"]?\s+RENAME\s+TO", "RENAME TABLE"),
        (r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)", "CREATE TABLE"),
        (r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?[`\"]?(\w+)", "DROP TABLE"),
        (r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)", "CREATE INDEX"),
        (r"DROP\s+INDEX\s+(?:IF\s+EXISTS\s+)?(?:CONCURRENTLY\s+)?[`\"]?(\w+)", "DROP INDEX"),
        (r"TRUNCATE\s+(?:TABLE\s+)?[`\"]?(\w+)", "TRUNCATE"),
        (r"DELETE\s+FROM\s+[`\"]?(\w+)", "DELETE"),
        (r"UPDATE\s+[`\"]?(\w+)", "UPDATE"),
    ]

    for pattern, op_type in patterns:
        for match in re.finditer(pattern, sql_clean, re.IGNORECASE):
            table = match.group(1).lower()
            rules = OPERATION_RULES.get(op_type, {})
            details = extract_details(sql_clean, match, op_type)

            # Adjust for NOT NULL without default
            backwards_compat = rules.get("backwards_compatible", True)
            if op_type == "ADD COLUMN":
                context = sql_clean[match.start():match.start() + 200]
                if "NOT NULL" in context.upper() and "DEFAULT" not in context.upper():
                    backwards_compat = False
                    details += " (NOT NULL without DEFAULT breaks existing inserts)"

            operations.append({
                "type": op_type,
                "table": table,
                "reversible": rules.get("reversible", True),
                "data_loss_risk": rules.get("data_loss_risk", False),
                "backwards_compatible": backwards_compat,
                "details": details,
            })

    return operations


def extract_details(sql: str, match: re.Match, op_type: str) -> str:
    """Extract human-readable details for an operation."""
    context = sql[match.start():min(match.start() + 150, len(sql))]
    # Truncate at semicolon
    semi = context.find(";")
    if semi > 0:
        context = context[:semi]
    return context.strip()


def validate_migration_file(filepath: str) -> dict:
    """Validate a single migration file."""
    with open(filepath) as f:
        sql = f.read()

    operations = classify_sql(sql)
    return {
        "file": os.path.basename(filepath),
        "operations": operations,
    }


def check_issues(migrations: list) -> list[dict]:
    """Check for issues across all migrations."""
    issues = []

    for mig in migrations:
        has_drop = False
        has_create = False
        for op in mig["operations"]:
            if op["data_loss_risk"]:
                issues.append({
                    "severity": "critical",
                    "file": mig["file"],
                    "message": f"{op['type']} on '{op['table']}' has data loss risk.",
                })
            if not op["reversible"]:
                issues.append({
                    "severity": "warning",
                    "file": mig["file"],
                    "message": f"{op['type']} on '{op['table']}' is not reversible.",
                })
            if not op["backwards_compatible"]:
                issues.append({
                    "severity": "warning",
                    "file": mig["file"],
                    "message": f"{op['type']} on '{op['table']}' is not backwards compatible. Use expand-contract pattern.",
                })
            if op["type"] == "DROP TABLE":
                has_drop = True
            if op["type"] == "CREATE TABLE":
                has_create = True

        # Check for mixed create+drop (possible rename via recreate)
        if has_drop and has_create:
            issues.append({
                "severity": "info",
                "file": mig["file"],
                "message": "Migration contains both CREATE TABLE and DROP TABLE. Verify this is intentional (rename via recreate?).",
            })

        # Check naming convention
        name = mig["file"]
        if not re.match(r"^\d{4}[_-]", name) and not re.match(r"^\d{14}", name):
            issues.append({
                "severity": "info",
                "file": name,
                "message": "Migration filename does not follow NNNN_description or timestamp convention.",
            })

    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate SQL migration files for safety")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--path", help="Directory containing migration files")
    group.add_argument("--sql", help="Single SQL file to validate")
    args = parser.parse_args()

    migrations = []

    if args.sql:
        if args.sql == "-":
            sql = sys.stdin.read()
            ops = classify_sql(sql)
            migrations.append({"file": "stdin", "operations": ops})
        else:
            if not os.path.isfile(args.sql):
                print(json.dumps({"error": f"File not found: {args.sql}"}), file=sys.stderr)
                sys.exit(1)
            migrations.append(validate_migration_file(args.sql))
    else:
        if not os.path.isdir(args.path):
            print(json.dumps({"error": f"Directory not found: {args.path}"}), file=sys.stderr)
            sys.exit(1)
        for fname in sorted(os.listdir(args.path)):
            if fname.endswith(".sql"):
                migrations.append(validate_migration_file(os.path.join(args.path, fname)))

    issues = check_issues(migrations)

    total_ops = sum(len(m["operations"]) for m in migrations)
    reversible = sum(1 for m in migrations for op in m["operations"] if op["reversible"])
    data_loss = sum(1 for m in migrations for op in m["operations"] if op["data_loss_risk"])

    result = {
        "migrations": migrations,
        "issues": issues,
        "summary": {
            "total_operations": total_ops,
            "reversible": reversible,
            "data_loss_risks": data_loss,
        },
    }

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
