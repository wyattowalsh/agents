#!/usr/bin/env python3
"""Static lint helper for Docling Graph Pydantic templates."""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ENTITY_NAME_HINTS = {
    "account",
    "asset",
    "claim",
    "company",
    "contract",
    "customer",
    "document",
    "entity",
    "filing",
    "instrument",
    "invoice",
    "obligation",
    "organization",
    "party",
    "person",
    "policy",
    "vendor",
}

HIGH_CARDINALITY_FIELD_HINTS = {
    "items",
    "lines",
    "observations",
    "pages",
    "records",
    "rows",
    "transactions",
}


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    model: str | None = None
    field: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.model:
            data["model"] = self.model
        if self.field:
            data["field"] = self.field
        return data


@dataclass
class FieldInfo:
    name: str
    annotation: str
    has_field_call: bool
    has_description: bool
    uses_edge_helper: bool
    references_models: set[str] = field(default_factory=set)
    list_depth: int = 0
    uses_any_or_dict: bool = False


@dataclass
class ModelInfo:
    name: str
    node: ast.ClassDef
    fields: list[FieldInfo]
    docstring: str | None
    model_config_keys: set[str]
    graph_id_fields: list[str]


def unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - ast.unparse exists on supported Python
        return ""


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def is_basemodel(class_node: ast.ClassDef) -> bool:
    for base in class_node.bases:
        text = unparse(base)
        if text == "BaseModel" or text.endswith(".BaseModel"):
            return True
    return False


def imported_edge_names(tree: ast.Module) -> set[str]:
    names = {"edge", "Edge"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "docling_graph" in node.module:
            for alias in node.names:
                if alias.name in {"edge", "Edge"}:
                    names.add(alias.asname or alias.name)
    return names


def has_field_description(value: ast.AST | None) -> bool:
    if not isinstance(value, ast.Call) or call_name(value.func) != "Field":
        return False
    for keyword in value.keywords:
        if keyword.arg == "description" and not is_empty_constant(keyword.value):
            return True
    return False


def is_empty_constant(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value in (None, "")


def uses_edge_helper(value: ast.AST | None, edge_names: set[str]) -> bool:
    if value is None:
        return False
    for node in ast.walk(value):
        if isinstance(node, ast.Call) and call_name(node.func) in edge_names:
            return True
    return False


def list_depth(annotation: ast.AST | None) -> int:
    if annotation is None:
        return 0
    text = unparse(annotation).replace("typing.", "")
    return text.count("list[") + text.count("List[")


def annotation_uses_any_or_dict(annotation: ast.AST | None) -> bool:
    text = unparse(annotation)
    tokens = {"Any", "dict", "Dict", "Mapping", "MutableMapping"}
    return any(token in text.replace("[", " ").replace("]", " ").replace(",", " ").split() for token in tokens)


def extract_graph_id_fields(value: ast.AST | None) -> list[str]:
    if value is None:
        return []

    if isinstance(value, ast.Call):
        for keyword in value.keywords:
            if keyword.arg == "json_schema_extra":
                fields = extract_graph_id_fields(keyword.value)
                if fields:
                    return fields

    for node in ast.walk(value):
        if isinstance(node, ast.Dict):
            for key, item in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == "graph_id_fields":
                    return string_list(item)
    return []


def string_list(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.List, ast.Tuple)):
        values = []
        for element in node.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                values.append(element.value)
        return values
    return []


def model_config_keys(value: ast.AST | None) -> set[str]:
    keys: set[str] = set()
    if value is None:
        return keys
    if isinstance(value, ast.Call):
        for keyword in value.keywords:
            if keyword.arg:
                keys.add(keyword.arg)
    for node in ast.walk(value):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.add(key.value)
    return keys


def references_models(annotation: ast.AST | None, model_names: set[str]) -> set[str]:
    if annotation is None:
        return set()
    text = unparse(annotation)
    found = set()
    for name in model_names:
        if name in text:
            found.add(name)
    return found


def collect_models(tree: ast.Module) -> list[ModelInfo]:
    edge_names = imported_edge_names(tree)
    class_nodes = [node for node in tree.body if isinstance(node, ast.ClassDef) and is_basemodel(node)]
    model_names = {node.name for node in class_nodes}
    models: list[ModelInfo] = []

    for class_node in class_nodes:
        fields: list[FieldInfo] = []
        config_value: ast.AST | None = None
        for stmt in class_node.body:
            if (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == "model_config"
            ):
                config_value = stmt.value
                continue
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if stmt.target.id == "model_config":
                    config_value = stmt.value
                    continue
                if stmt.target.id.startswith("_"):
                    continue
                fields.append(
                    FieldInfo(
                        name=stmt.target.id,
                        annotation=unparse(stmt.annotation),
                        has_field_call=isinstance(stmt.value, ast.Call)
                        and call_name(stmt.value.func) == "Field",
                        has_description=has_field_description(stmt.value),
                        uses_edge_helper=uses_edge_helper(stmt.value, edge_names),
                        references_models=references_models(stmt.annotation, model_names),
                        list_depth=list_depth(stmt.annotation),
                        uses_any_or_dict=annotation_uses_any_or_dict(stmt.annotation),
                    )
                )

        models.append(
            ModelInfo(
                name=class_node.name,
                node=class_node,
                fields=fields,
                docstring=ast.get_docstring(class_node),
                model_config_keys=model_config_keys(config_value),
                graph_id_fields=extract_graph_id_fields(config_value),
            )
        )

    return models


def root_candidates(models: list[ModelInfo]) -> list[str]:
    referenced: set[str] = set()
    for model in models:
        for info in model.fields:
            referenced.update(info.references_models)

    candidates = [model.name for model in models if model.name not in referenced]
    if candidates:
        return candidates

    scored = sorted(
        models,
        key=lambda model: (
            sum(bool(field.references_models) for field in model.fields),
            len(model.fields),
        ),
        reverse=True,
    )
    return [model.name for model in scored[:2]]


def looks_entity_like(name: str) -> bool:
    lowered = name.lower()
    return any(hint in lowered for hint in ENTITY_NAME_HINTS)


def analyze(path: Path, root: str | None = None) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    models = collect_models(tree)
    findings: list[Finding] = []

    if not models:
        findings.append(
            Finding(
                "error",
                "no-pydantic-models",
                "No Pydantic BaseModel classes were found.",
            )
        )

    candidates = root_candidates(models)
    model_names = {model.name for model in models}
    if root and root not in model_names:
        findings.append(
            Finding(
                "error",
                "root-missing",
                f"Requested root model {root} was not found.",
                root,
            )
        )
    elif not root and len(candidates) != 1 and models:
        findings.append(
            Finding(
                "warning",
                "ambiguous-root",
                f"Root model is ambiguous; candidates: {', '.join(candidates)}.",
            )
        )

    for model in models:
        if not model.docstring:
            findings.append(
                Finding(
                    "info",
                    "missing-docstring",
                    "Model has no docstring; add one to anchor extraction intent.",
                    model.name,
                )
            )

        if looks_entity_like(model.name) and not model.graph_id_fields:
            findings.append(
                Finding(
                    "warning",
                    "missing-stable-id",
                    "Entity-like model has no graph_id_fields in model_config.",
                    model.name,
                )
            )

        if "json_schema_extra" not in model.model_config_keys and model.graph_id_fields:
            findings.append(
                Finding(
                    "info",
                    "nonstandard-graph-id-location",
                    "graph_id_fields were found outside a visible json_schema_extra key.",
                    model.name,
                )
            )

        for info in model.fields:
            if not info.has_field_call:
                findings.append(
                    Finding(
                        "info",
                        "missing-field-call",
                        "Field is not wrapped in Field(...); descriptions may not reach the extractor.",
                        model.name,
                        info.name,
                    )
                )
            elif not info.has_description:
                findings.append(
                    Finding(
                        "warning",
                        "missing-field-description",
                        "Field has no non-empty description.",
                        model.name,
                        info.name,
                    )
                )

            if info.uses_any_or_dict:
                findings.append(
                    Finding(
                        "warning",
                        "loose-graph-field",
                        "Graph-critical templates should avoid Any/dict-style fields.",
                        model.name,
                        info.name,
                    )
                )

            if info.references_models and not info.uses_edge_helper:
                findings.append(
                    Finding(
                        "info",
                        "relationship-without-edge-helper",
                        "Relationship-like field references another model but does not use an edge helper.",
                        model.name,
                        info.name,
                    )
                )

            if info.list_depth >= 2:
                findings.append(
                    Finding(
                        "warning",
                        "deep-list-nesting",
                        "Nested list-of-model structures often need staged or delta extraction.",
                        model.name,
                        info.name,
                    )
                )

            if info.name.lower() in HIGH_CARDINALITY_FIELD_HINTS:
                findings.append(
                    Finding(
                        "info",
                        "high-cardinality-field",
                        "High-cardinality fields should have a staged/delta contract and QA sampling.",
                        model.name,
                        info.name,
                    )
                )

    severity_rank = {"error": 3, "warning": 2, "info": 1}
    max_severity = max((severity_rank[item.severity] for item in findings), default=0)
    return {
        "ok": max_severity < severity_rank["error"],
        "path": str(path),
        "root": root,
        "root_model_candidates": candidates,
        "models": [
            {
                "name": model.name,
                "field_count": len(model.fields),
                "has_docstring": bool(model.docstring),
                "graph_id_fields": model.graph_id_fields,
                "model_config_keys": sorted(model.model_config_keys),
            }
            for model in models
        ],
        "summary": {
            "model_count": len(models),
            "error_count": sum(item.severity == "error" for item in findings),
            "warning_count": sum(item.severity == "warning" for item in findings),
            "info_count": sum(item.severity == "info" for item in findings),
        },
        "staged_delta_risks": [
            item.as_dict()
            for item in findings
            if item.code in {"deep-list-nesting", "high-cardinality-field", "missing-stable-id"}
        ],
        "findings": [item.as_dict() for item in findings],
    }


def print_pretty(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "ERROR"
    print(f"Docling Graph template lint: {status}")
    print(f"- path: {report['path']}")
    print(f"- root candidates: {', '.join(report['root_model_candidates']) or 'none'}")
    for finding in report["findings"]:
        location = ""
        if finding.get("model"):
            location += f" {finding['model']}"
        if finding.get("field"):
            location += f".{finding['field']}"
        print(f"- {finding['severity']} {finding['code']}{location}: {finding['message']}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path, help="Path to a Python template file")
    parser.add_argument("--root", help="Expected root model name")
    parser.add_argument("--format", choices=("pretty", "json"), default="pretty")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = analyze(args.template, args.root)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_pretty(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
