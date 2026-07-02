#!/usr/bin/env python3
"""Emit SARIF 2.1.0 logs for wagents validate results."""

from __future__ import annotations

import json
from typing import Any

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
RULE_ID = "asset-validation"


def build_sarif_log(
    errors: list[dict[str, str]],
    *,
    tool_name: str = "wagents-validate",
    information_uri: str = "https://github.com/wyattowalsh/agents",
) -> dict[str, Any]:
    """Build a SARIF 2.1.0 log document from normalized validation errors."""
    results: list[dict[str, Any]] = []
    for error in errors:
        source = error.get("source", "unknown")
        message = error.get("message", "validation error")
        results.append(
            {
                "ruleId": RULE_ID,
                "level": "error",
                "message": {"text": message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": source},
                        }
                    }
                ],
            }
        )

    return {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "informationUri": information_uri,
                        "rules": [
                            {
                                "id": RULE_ID,
                                "name": "AssetValidation",
                                "shortDescription": {"text": "Repository asset validation"},
                                "fullDescription": {
                                    "text": "Validates skills, agents, MCP servers, hooks, and related repo assets.",
                                },
                            }
                        ],
                    }
                },
                "results": results,
            }
        ],
    }


def emit_sarif_log(errors: list[dict[str, str]], *, indent: int = 2) -> None:
    """Print SARIF JSON to stdout."""
    print(json.dumps(build_sarif_log(errors), indent=indent))
