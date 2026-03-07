#!/usr/bin/env python3
"""Static analysis for algorithmic complexity estimation via AST parsing."""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path


def _walk_skip_nested(node: ast.AST):
    """Walk AST nodes, skipping nested FunctionDef/AsyncFunctionDef bodies."""
    yield node
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue  # don't descend into nested functions
        yield from _walk_skip_nested(child)


def estimate_complexity(node: ast.AST, depth: int = 0) -> tuple[str, list[str]]:
    """Estimate Big-O complexity of a function by analyzing loop nesting and recursion."""
    max_depth = depth
    evidence: list[str] = []
    has_recursion = False
    func_name = getattr(node, "name", "")

    for child in _walk_skip_nested(node):
        if isinstance(child, (ast.For, ast.While)):
            current_depth = _loop_nesting_depth(child)
            if current_depth > max_depth:
                max_depth = current_depth
                evidence.append(f"loop nesting depth {current_depth} at line {child.lineno}")
        elif isinstance(child, ast.Call):
            call_name = _get_call_name(child)
            if call_name == func_name:
                has_recursion = True
                evidence.append(f"recursive call at line {child.lineno}")
        elif isinstance(child, ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp):
            comp_depth = _comprehension_depth(child)
            if comp_depth > max_depth:
                max_depth = comp_depth
                evidence.append(f"nested comprehension depth {comp_depth} at line {child.lineno}")

    if has_recursion and max_depth == 0:
        return "O(n)", evidence + ["recursive without loop — likely O(n) or O(log n)"]
    if has_recursion and max_depth >= 1:
        return f"O(n^{max_depth + 1})", evidence + ["recursion with loops"]

    complexity_map = {0: "O(1)", 1: "O(n)", 2: "O(n^2)", 3: "O(n^3)"}
    complexity = complexity_map.get(max_depth, f"O(n^{max_depth})")
    return complexity, evidence


def _loop_nesting_depth(node: ast.AST) -> int:
    """Count maximum loop nesting depth from a given node."""
    max_d = 1
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While)):
            d = 1 + _loop_nesting_depth(child)
            if d > max_d:
                max_d = d
    return max_d


def _comprehension_depth(node: ast.AST) -> int:
    """Count nested comprehension depth."""
    generators = getattr(node, "generators", [])
    depth = len(generators)
    for gen in generators:
        for child in ast.walk(gen):
            if isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                depth += _comprehension_depth(child)
    return depth


def _get_call_name(node: ast.Call) -> str:
    """Extract function name from a Call node."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _hotspot_score(complexity: str, loc: int) -> float:
    """Score hotspot risk based on complexity and function size."""
    complexity_weights = {
        "O(1)": 0.1, "O(log n)": 0.2, "O(n)": 0.4,
        "O(n log n)": 0.6, "O(n^2)": 0.8, "O(n^3)": 1.0,
    }
    base = complexity_weights.get(complexity, 0.9)
    size_factor = min(loc / 100, 1.0)
    return round(base * (0.5 + 0.5 * size_factor), 2)


def analyze_file(file_path: Path) -> list[dict]:
    """Analyze all functions in a Python file."""
    source = file_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        print(f"SyntaxError in {file_path}: {exc}", file=sys.stderr)
        return []

    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, "end_lineno", node.lineno)
            loc = end_line - node.lineno + 1
            complexity, evidence = estimate_complexity(node)
            results.append({
                "name": node.name,
                "file": str(file_path),
                "line": node.lineno,
                "end_line": end_line,
                "loc": loc,
                "estimated_complexity": complexity,
                "evidence": evidence,
                "hotspot_score": _hotspot_score(complexity, loc),
            })
    return results


def analyze_path(path: Path) -> list[dict]:
    """Analyze a file or directory."""
    if path.is_file() and path.suffix == ".py":
        return analyze_file(path)

    results = []
    if path.is_dir():
        for py_file in sorted(path.rglob("*.py")):
            if any(part.startswith(".") or part in {"node_modules", "__pycache__", ".venv", "venv"}
                   for part in py_file.parts):
                continue
            results.extend(analyze_file(py_file))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate algorithmic complexity via AST analysis")
    parser.add_argument("path", help="Python file or directory to analyze")
    parser.add_argument("--min-score", type=float, default=0.0,
                        help="Minimum hotspot score to include (0.0-1.0)")
    parser.add_argument("--sort", choices=["complexity", "hotspot", "name"], default="hotspot",
                        help="Sort results by field")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(json.dumps({"error": f"Path not found: {args.path}", "functions": []}))
        sys.exit(1)

    functions = analyze_path(target)

    if args.min_score > 0:
        functions = [f for f in functions if f["hotspot_score"] >= args.min_score]

    if args.sort == "hotspot":
        functions.sort(key=lambda f: f["hotspot_score"], reverse=True)
    elif args.sort == "complexity":
        functions.sort(key=lambda f: f["estimated_complexity"], reverse=True)
    else:
        functions.sort(key=lambda f: f["name"])

    output = {
        "path": str(target),
        "total_functions": len(functions),
        "functions": functions,
        "summary": {
            "by_complexity": {},
            "avg_hotspot_score": round(
                sum(f["hotspot_score"] for f in functions) / max(len(functions), 1), 2
            ),
        },
    }
    for f in functions:
        c = f["estimated_complexity"]
        output["summary"]["by_complexity"][c] = output["summary"]["by_complexity"].get(c, 0) + 1

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
