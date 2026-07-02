"""MCP server: release-provenance.

Read-only release and provenance signals from `planning/manifests/` and
`.github/workflows/*.yml`. No tool in this server mutates the repository.
"""

from __future__ import annotations

import json
from typing import Any

import yaml
from fastmcp import FastMCP

from wagents import ROOT
from wagents.mcp_shared.read_only_paths import PathNotAllowedError, read_text_within_allowlist

mcp = FastMCP("Release Provenance")

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

_MANIFEST_PREFIXES = ("planning/manifests",)
_WORKFLOW_PREFIXES = (".github/workflows",)
_PROVENANCE_KEYWORDS = ("provenance", "release", "attestation", "readiness")


def _manifest_dir():
    return ROOT / "planning" / "manifests"


def _workflow_dir():
    return ROOT / ".github" / "workflows"


def _manifest_matches(name: str) -> bool:
    lowered = name.lower()
    return any(keyword in lowered for keyword in _PROVENANCE_KEYWORDS)


@mcp.tool(annotations=_READ_ONLY)
def list_provenance_manifests() -> list[dict[str, str]]:
    """List planning manifests related to release or provenance.

    Returns basename, relative path, and file kind for JSON/MD manifests
    under `planning/manifests/` whose names mention release, provenance,
    attestation, or readiness.
    """
    manifest_dir = _manifest_dir()
    if not manifest_dir.is_dir():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(manifest_dir.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file() or path.suffix not in {".json", ".md"}:
            continue
        if not _manifest_matches(path.name):
            continue
        rows.append({
            "name": path.name,
            "relative_path": str(path.relative_to(ROOT)),
            "kind": path.suffix.removeprefix("."),
        })
    return rows


@mcp.tool(annotations=_READ_ONLY)
def get_provenance_manifest(name: str) -> dict[str, Any]:
    """Return one planning manifest by basename.

    *name* must live under `planning/manifests/` and be allowlisted via the
    shared read-only path guard. JSON manifests are parsed; Markdown
    manifests return raw text under `content`.
    """
    relative = f"planning/manifests/{name}"
    try:
        text = read_text_within_allowlist(relative, allowed_prefixes=_MANIFEST_PREFIXES)
    except PathNotAllowedError as exc:
        raise ValueError(str(exc)) from exc
    if name.endswith(".json"):
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object in {name!r}")
        return payload
    return {"name": name, "content": text}


@mcp.tool(annotations=_READ_ONLY)
def list_release_workflows() -> list[dict[str, str]]:
    """List GitHub workflow files that mention release or tag publishing."""
    workflow_dir = _workflow_dir()
    if not workflow_dir.is_dir():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(workflow_dir.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        if "release" not in lowered and "tags:" not in lowered and "package-and-release" not in lowered:
            continue
        rows.append({
            "name": path.name,
            "relative_path": str(path.relative_to(ROOT)),
        })
    return rows


@mcp.tool(annotations=_READ_ONLY)
def get_release_workflow_summary(filename: str) -> dict[str, Any]:
    """Summarize one `.github/workflows/<filename>` release-related workflow.

    Parses YAML and returns workflow name, triggers, job names, whether a
    release job exists, and top-level permissions. *filename* must end in
    `.yml`.
    """
    if not filename.endswith(".yml"):
        filename = f"{filename}.yml"
    relative = f".github/workflows/{filename}"
    try:
        text = read_text_within_allowlist(relative, allowed_prefixes=_WORKFLOW_PREFIXES)
    except PathNotAllowedError as exc:
        raise ValueError(str(exc)) from exc
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"Workflow root must be a mapping: {relative}")
    jobs = data.get("jobs", {})
    job_names = sorted(jobs.keys()) if isinstance(jobs, dict) else []
    release_jobs = [name for name in job_names if "release" in name.lower()]
    return {
        "filename": filename,
        "workflow_name": data.get("name"),
        "on": data.get("on"),
        "permissions": data.get("permissions"),
        "job_count": len(job_names),
        "jobs": job_names,
        "release_jobs": release_jobs,
        "has_tag_trigger": "tags" in json.dumps(data.get("on", {})),
    }


if __name__ == "__main__":
    mcp.run()
