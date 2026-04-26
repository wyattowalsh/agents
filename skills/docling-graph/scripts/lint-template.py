#!/usr/bin/env python3
"""Static checks for Docling Graph Pydantic template files."""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Finding:
    level: str
    code: str
    line: int | None
    message: str


def _base_names(node: ast.ClassDef) -> set[str]:
    names: set[str] = set()
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.add(base.id)
        elif isinstance(base, ast.Attribute):
            names.add(base.attr)
    return names


def _is_pydantic_model(node: ast.ClassDef) -> bool:
    return bool(_base_names(node) & {"BaseModel"})


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _has_field_description(value: ast.AST | None) -> bool:
    if not isinstance(value, ast.Call):
        return False
    if _call_name(value) != "Field":
        return False
    for keyword in value.keywords:
        if keyword.arg == "description":
            return True
    return False


def _uses_edge(value: ast.AST | None) -> bool:
    return isinstance(value, ast.Call) and _call_name(value) == "edge"


def _model_config_info(node: ast.ClassDef) -> tuple[bool, bool]:
    has_config = False
    has_graph_id_fields = False
    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            targets = [target.id for target in stmt.targets if isinstance(target, ast.Name)]
            if "model_config" not in targets:
                continue
            has_config = True
            source = ast.unparse(stmt.value) if hasattr(ast, "unparse") else ""
            has_graph_id_fields = "graph_id_fields" in source
    return has_config, has_graph_id_fields


def _field_name(stmt: ast.AST) -> str | None:
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        return stmt.target.id
    return None


def analyze(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    findings: list[Finding] = []
    models: list[dict[str, Any]] = []

    imports_edge = "docling_graph.utils" in source and "edge" in source
    pydantic_models = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and _is_pydantic_model(node)]

    if not pydantic_models:
        findings.append(Finding("error", "no-pydantic-models", None, "No Pydantic BaseModel classes found"))

    for model in pydantic_models:
        has_config, has_graph_id_fields = _model_config_info(model)
        field_count = 0
        described_fields = 0
        edge_fields = 0
        relationship_like = 0

        for stmt in model.body:
            name = _field_name(stmt)
            if name is None:
                continue
            field_count += 1
            value = stmt.value if isinstance(stmt, ast.AnnAssign) else None
            if _has_field_description(value) or _uses_edge(value):
                described_fields += 1
            if _uses_edge(value):
                edge_fields += 1
            annotation = ast.unparse(stmt.annotation) if isinstance(stmt, ast.AnnAssign) and hasattr(ast, "unparse") else ""
            if "list[" in annotation or "List[" in annotation or any(ch.isupper() for ch in annotation):
                relationship_like += 1

        if not has_config:
            findings.append(Finding("warning", "missing-model-config", model.lineno, f"{model.name} has no model_config"))
        if field_count and described_fields < field_count:
            findings.append(
                Finding(
                    "warning",
                    "weak-field-guidance",
                    model.lineno,
                    f"{model.name} describes {described_fields}/{field_count} fields",
                )
            )
        if relationship_like and not edge_fields:
            findings.append(
                Finding(
                    "info",
                    "implicit-relationships",
                    model.lineno,
                    f"{model.name} has relationship-like fields but no explicit edge() labels",
                )
            )
        if has_config and not has_graph_id_fields:
            findings.append(
                Finding(
                    "info",
                    "review-stable-id",
                    model.lineno,
                    f"{model.name} has model_config but no graph_id_fields",
                )
            )

        models.append(
            {
                "name": model.name,
                "line": model.lineno,
                "field_count": field_count,
                "described_fields": described_fields,
                "edge_fields": edge_fields,
                "has_model_config": has_config,
                "has_graph_id_fields": has_graph_id_fields,
            }
        )

    if any(model["edge_fields"] for model in models) and not imports_edge:
        findings.append(Finding("warning", "edge-import-not-detected", None, "edge() is used but docling_graph.utils import was not detected"))

    levels = [finding.level for finding in findings]
    if "error" in levels:
        status = "error"
    elif "warning" in levels:
        status = "warning"
    else:
        status = "ok"

    return {
        "tool": "docling-graph lint-template",
        "path": str(path),
        "status": status,
        "model_count": len(models),
        "models": models,
        "findings": [asdict(finding) for finding in findings],
        "notes": [
            "This is a static heuristic lint, not a substitute for importing the template and running extraction.",
            "Review entity/component choices and stable IDs against real sample documents.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Lint a Docling Graph Pydantic template file")
    parser.add_argument("path", help="Python template file")
    parser.add_argument("--format", choices=["json", "pretty"], default="json")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(json.dumps({"tool": "docling-graph lint-template", "status": "error", "error": f"Path not found: {path}"}))
        sys.exit(1)
    if path.suffix != ".py":
        print(json.dumps({"tool": "docling-graph lint-template", "status": "error", "error": "Template path must be a .py file"}))
        sys.exit(1)

    try:
        report = analyze(path)
    except SyntaxError as exc:
        report = {
            "tool": "docling-graph lint-template",
            "path": str(path),
            "status": "error",
            "findings": [
                {
                    "level": "error",
                    "code": "syntax-error",
                    "line": exc.lineno,
                    "message": str(exc),
                }
            ],
        }

    if args.format == "pretty":
        print(f"status: {report['status']}")
        for finding in report.get("findings", []):
            line = finding.get("line") or "-"
            print(f"{finding['level']:7} line {line}: {finding['code']} - {finding['message']}")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))

    if report["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
