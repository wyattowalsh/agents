#!/usr/bin/env python3
"""Extract actionable errors from CI failure logs.

Output: JSON with categorized errors, summary, and suggested fixes.
Stdlib only.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Error patterns by category
ERROR_PATTERNS = {
    "dependency": [
        (r"(?:npm |yarn |pnpm )?ERR!.*(?:peer dep|ERESOLVE|404|registry)", "Package resolution or registry error"),
        (r"(?:pip|uv).*(?:Could not find|No matching distribution|ResolutionImpossible)", "Python package not found or version conflict"),
        (r"error\[E\d+\].*(?:unresolved|not found).*crate", "Rust crate dependency error"),
        (r"(?:go|module).*(?:cannot find|ambiguous import|unknown revision)", "Go module resolution error"),
        (r"Could not resolve dependencies", "Dependency resolution failure"),
        (r"ETIMEOUT|ECONNREFUSED|ECONNRESET|ETIMEDOUT", "Network timeout connecting to registry"),
        (r"lockfile.*out of date|lock file.*not up to date", "Lockfile out of sync"),
    ],
    "build": [
        (r"error(?:\[.*?\])?:.*(?:cannot find|not found|undefined|undeclared)", "Compilation error: missing symbol"),
        (r"(?:Type|Syntax)Error:.*", "Type or syntax error"),
        (r"error:.*(?:out of memory|OOM|Cannot allocate)", "Out of memory during build"),
        (r"FATAL ERROR:.*(?:heap|allocation|memory)", "Node.js heap allocation failure"),
        (r"error\[E\d+\]:", "Rust compiler error"),
        (r"error:.*expected.*found", "Type mismatch"),
        (r"(?:Build|Compile|Compilation) (?:failed|error)", "Build process failure"),
    ],
    "test": [
        (r"FAIL(?:ED)?[:\s].*(?:test|spec|describe)", "Test assertion failure"),
        (r"(?:AssertionError|AssertError|assert).*", "Assertion failure"),
        (r"Error:.*(?:timeout|timed out).*(?:test|spec|it\()", "Test timeout"),
        (r"(?:flaky|intermittent|retry).*(?:test|spec)", "Flaky test detected"),
        (r"(?:\d+) (?:failing|failed)", "Multiple test failures"),
        (r"ENOSPC|no space left on device", "Disk space exhaustion during tests"),
    ],
    "lint": [
        (r"(?:error|warning):.*(?:eslint|prettier|black|ruff|pylint|clippy)", "Linter rule violation"),
        (r"\d+ error.*\d+ warning", "Multiple lint violations"),
        (r"(?:formatting|format) (?:check|diff).*(?:fail|error)", "Code formatting violation"),
    ],
    "deploy": [
        (r"(?:permission|access) denied", "Permission denied during deployment"),
        (r"(?:health check|healthcheck).*(?:fail|timeout|unhealthy)", "Health check failure"),
        (r"(?:resource|quota|limit).*(?:exceeded|exhausted)", "Resource limit exceeded"),
        (r"(?:kubectl|helm|terraform).*(?:error|fail)", "Infrastructure tool failure"),
        (r"(?:docker|container).*(?:error|fail|exit code)", "Container operation failure"),
        (r"(?:rollback|revert).*(?:triggered|initiated)", "Deployment rollback triggered"),
    ],
}

SUGGESTED_FIXES = {
    "dependency": {
        "Package resolution or registry error": "Pin conflicting packages to compatible versions. Add retry logic to install step.",
        "Python package not found or version conflict": "Check package name spelling. Pin version constraints in requirements/pyproject.toml.",
        "Network timeout connecting to registry": "Add retry logic (retry: 3) to install step. Consider caching dependencies.",
        "Lockfile out of sync": "Run package manager lock command locally and commit updated lockfile.",
    },
    "build": {
        "Out of memory during build": "Increase runner memory (use larger runner) or add NODE_OPTIONS=--max-old-space-size=4096.",
        "Node.js heap allocation failure": "Set NODE_OPTIONS=--max-old-space-size=4096 in env. Consider larger runner.",
        "Build process failure": "Check build command output. Verify all dependencies are installed before build step.",
    },
    "test": {
        "Test timeout": "Increase test timeout. Check for deadlocks or infinite loops. Consider splitting test suites.",
        "Flaky test detected": "Add retry mechanism. Investigate race conditions. Consider test isolation.",
        "Disk space exhaustion during tests": "Add cleanup step between jobs. Use larger runner or prune Docker images.",
    },
    "lint": {
        "Code formatting violation": "Run formatter locally before committing. Add pre-commit hook.",
        "Multiple lint violations": "Run linter locally with --fix flag. Update lint configuration if rules are too strict.",
    },
    "deploy": {
        "Permission denied during deployment": "Check service account permissions. Verify secrets are correctly configured.",
        "Health check failure": "Verify application starts correctly. Check health endpoint. Increase health check timeout.",
        "Resource limit exceeded": "Increase resource limits or optimize application resource usage.",
    },
}


def parse_log(content: str) -> dict:
    """Parse CI log content and extract errors."""
    lines = content.split("\n")
    errors = []
    seen_messages = set()
    error_index = {}  # key -> index in errors list

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue

        # Remove ANSI color codes
        clean_line = re.sub(r"\x1b\[[0-9;]*m", "", stripped)

        for category, patterns in ERROR_PATTERNS.items():
            for pattern, description in patterns:
                if re.search(pattern, clean_line, re.IGNORECASE):
                    # Deduplicate similar errors
                    key = f"{category}:{description}"
                    if key in seen_messages:
                        # Update line reference but don't duplicate — O(1) lookup
                        idx = error_index[key]
                        if line_num not in errors[idx].get("additional_lines", []):
                            errors[idx].setdefault("additional_lines", []).append(line_num)
                        continue

                    seen_messages.add(key)
                    suggested_fix = SUGGESTED_FIXES.get(category, {}).get(
                        description,
                        f"Review the {category} configuration and error context."
                    )

                    error_index[key] = len(errors)
                    errors.append({
                        "line": line_num,
                        "message": description,
                        "category": category,
                        "raw": clean_line[:200],  # Truncate long lines
                        "suggested_fix": suggested_fix,
                    })
                    break  # One match per line

    # Build summary
    category_counts = {}
    for e in errors:
        category_counts[e["category"]] = category_counts.get(e["category"], 0) + 1

    # Determine primary failure category
    primary_category = max(category_counts, key=category_counts.get) if category_counts else "unknown"

    summary = {
        "total_errors": len(errors),
        "categories": category_counts,
        "primary_failure_category": primary_category,
        "total_lines_analyzed": len(lines),
    }

    return {
        "errors": errors,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="Parse CI failure logs for actionable errors")
    parser.add_argument("file", nargs="?", help="Path to log file (reads stdin if not provided)")
    parser.add_argument("--max-lines", type=int, default=1000, help="Max lines to analyze (default: 1000)")
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(json.dumps({"error": f"File not found: {args.file}"}))
            sys.exit(1)
        content = path.read_text(errors="replace")
    else:
        content = sys.stdin.read()

    # Truncation strategy for large logs
    lines = content.split("\n")
    if len(lines) > args.max_lines:
        # Keep first 50 + last 200 + sample middle around error-like patterns
        head = lines[:50]
        tail = lines[-200:]
        middle = []
        for i, line in enumerate(lines[50:-200]):
            if any(kw in line.lower() for kw in ["error", "fail", "fatal", "exception", "panic"]):
                start = max(0, i + 50 - 2)
                end = min(len(lines) - 200, i + 50 + 3)
                middle.extend(lines[start:end])

        seen = set()
        middle_deduped = []
        for line in middle:
            if line not in seen:
                seen.add(line)
                middle_deduped.append(line)
        truncated_lines = head + middle_deduped + tail
        content = "\n".join(truncated_lines)
        print(f"Log truncated: {len(lines)} -> {len(truncated_lines)} lines (kept head/tail + error context)", file=sys.stderr)

    result = parse_log(content)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
