"""MCP server: ci-artifacts.

Read-only access to committed CI report JSON under
`docs/public/generated-reports/` plus artifact metadata from
`config/docs-artifact-registry.json`. No tool in this server mutates the
repository.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from wagents import ROOT
from wagents.docs_reports import REPORTS_JSON_DIR

mcp = FastMCP("CI Artifacts")

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

_ARTIFACT_REGISTRY = ROOT / "config" / "docs-artifact-registry.json"


def _load_artifact_registry() -> dict[str, Any]:
    if not _ARTIFACT_REGISTRY.is_file():
        return {"version": 0, "artifacts": []}
    return json.loads(_ARTIFACT_REGISTRY.read_text(encoding="utf-8"))


def _report_artifacts() -> list[dict[str, Any]]:
    registry = _load_artifact_registry()
    artifacts = registry.get("artifacts", [])
    if not isinstance(artifacts, list):
        return []
    return [row for row in artifacts if isinstance(row, dict) and str(row.get("path", "")).startswith("docs/public/generated-reports")]


@mcp.tool(annotations=_READ_ONLY)
def list_ci_artifacts() -> list[dict[str, Any]]:
    """List generated CI report JSON files and registry metadata.

    Combines on-disk files under `docs/public/generated-reports/*.json`
    with rows from `config/docs-artifact-registry.json` that reference that
    directory. Use `get_ci_artifact` to fetch one payload.
    """
    registry_by_path = {str(row.get("path", "")): row for row in _report_artifacts()}
    rows: list[dict[str, Any]] = []
    if REPORTS_JSON_DIR.is_dir():
        for path in sorted(REPORTS_JSON_DIR.glob("*.json")):
            rel = str(path.relative_to(ROOT))
            reg = registry_by_path.get(rel, {})
            stat = path.stat()
            rows.append({
                "name": path.stem,
                "relative_path": rel,
                "bytes": stat.st_size,
                "mode": reg.get("mode"),
                "validation": reg.get("validation"),
                "owner_change": reg.get("owner_change"),
            })
    return rows


@mcp.tool(annotations=_READ_ONLY)
def get_ci_artifact(name: str) -> dict[str, Any]:
    """Return one generated CI report JSON payload by basename.

    *name* is the filename stem, e.g. `docs-link-check` for
    `docs/public/generated-reports/docs-link-check.json`. Raises if the
    file is missing — regenerate with `uv run wagents docs generate`.
    """
    stem = name.removesuffix(".json")
    path = REPORTS_JSON_DIR / f"{stem}.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"CI artifact {name!r} not found under docs/public/generated-reports/. "
            "Run `uv run wagents docs generate`."
        )
    return json.loads(path.read_text(encoding="utf-8"))


@mcp.tool(annotations=_READ_ONLY)
def ci_artifact_registry() -> dict[str, Any]:
    """Return docs-artifact-registry rows for generated CI report JSON.

    Includes registry version, source registries, and artifact rows whose
    paths live under `docs/public/generated-reports/`.
    """
    registry = _load_artifact_registry()
    return {
        "version": registry.get("version"),
        "source_registries": registry.get("source_registries", []),
        "artifacts": _report_artifacts(),
    }


@mcp.tool(annotations=_READ_ONLY)
def ci_artifact_summary() -> dict[str, Any]:
    """Return coarse counts for generated CI report artifacts.

    Reports how many JSON files exist on disk versus how many registry rows
    reference `docs/public/generated-reports/`.
    """
    on_disk = len(list(REPORTS_JSON_DIR.glob("*.json"))) if REPORTS_JSON_DIR.is_dir() else 0
    registry_rows = _report_artifacts()
    return {
        "on_disk_count": on_disk,
        "registry_count": len(registry_rows),
        "reports_dir": str(REPORTS_JSON_DIR.relative_to(ROOT)),
    }


if __name__ == "__main__":
    mcp.run()
