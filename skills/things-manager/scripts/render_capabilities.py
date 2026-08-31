#!/usr/bin/env python3
"""Render and verify the Things++ capability ledger from the frozen OpenSpec contract."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from importlib import import_module
from pathlib import Path
from typing import Any, cast

SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_DIR.parent.parent
SOURCE_PATH = (
    REPO_ROOT / "openspec" / "changes" / "replace-supathings-with-things-plus-plus" / "capability-manifest.json"
)
SOURCE_SCHEMA_PATH = SOURCE_PATH.with_suffix(".schema.json")
CAPABILITIES_JSON = SKILL_DIR / "references" / "capabilities.json"
CAPABILITIES_MD = SKILL_DIR / "references" / "capabilities.md"
CHATGPT_CAPABILITIES_MD = REPO_ROOT / "platforms" / "chatgpt" / "things-plus-plus" / "CAPABILITY_MATRIX.md"
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ADAPTED_SCHEMA_HASH_KEYS = {
    "inputSchemaSha256",
    "outputSchemaSha256",
    "status",
}

DEGRADED_BEHAVIOR = {
    "things-core": (
        "Fail closed and report the missing core prerequisite. Do not claim a read or write, and do not switch "
        "backends unless the selected workflow explicitly maps an equivalent closed typed route."
    ),
    "things-shortcuts": (
        "Report the fixed Things++ bridge or TCC prerequisite as unavailable with the manual next action. Do not "
        "fall back to a generic Shortcut, raw JSON, caller-provided URL, AppleScript, shell, or another backend."
    ),
    "things-native": (
        "Report the fixed native script or URL-builder prerequisite as unavailable with the manual next action. "
        "Do not fall back to arbitrary AppleScript, a caller-provided URL, shell, database access, or UI automation."
    ),
}


class CapabilityError(ValueError):
    """Raised when the skill ledger diverges from the frozen contract."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CapabilityError(f"missing capability source: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CapabilityError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CapabilityError(f"capability source must be a JSON object: {path}")
    return payload


def _validate_source_schema(source: dict[str, Any]) -> None:
    try:
        jsonschema = import_module("jsonschema")
    except ModuleNotFoundError as exc:
        raise CapabilityError("jsonschema is required to validate the frozen OpenSpec capability manifest") from exc

    schema = _load_json(SOURCE_SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(source)
    except jsonschema.exceptions.SchemaError as exc:
        raise CapabilityError(f"invalid capability manifest schema: {exc.message}") from exc
    except jsonschema.ValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path) or "<root>"
        raise CapabilityError(f"capability manifest violates schema at {location}: {exc.message}") from exc


def _validate_adapted_schema_hashes(tools: list[dict[str, Any]]) -> None:
    for tool in tools:
        capability_id = tool.get("qualifiedCapabilityId", "<unknown>")
        hashes = tool.get("adaptedSchemaHashes")
        if not isinstance(hashes, dict) or set(hashes) != ADAPTED_SCHEMA_HASH_KEYS:
            raise CapabilityError(f"{capability_id} lacks the closed adapted schema hash contract")
        if hashes.get("status") != "frozen":
            raise CapabilityError(f"{capability_id} adapted schema hashes are not frozen")
        for field in ("inputSchemaSha256", "outputSchemaSha256"):
            value = hashes.get(field)
            if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
                raise CapabilityError(f"{capability_id} has an invalid adapted {field}")


def _derived_manifest(source: dict[str, Any]) -> dict[str, Any]:
    derived = copy.deepcopy(source)
    for tool in derived.get("tools", []):
        if not isinstance(tool, dict):
            raise CapabilityError("every tool row must be an object")
        server = tool.get("server")
        if server not in DEGRADED_BEHAVIOR:
            raise CapabilityError(f"unknown Things++ backend: {server!r}")
        tool["degradedBehavior"] = DEGRADED_BEHAVIOR[server]
    return derived


def _source_projection(derived: dict[str, Any]) -> dict[str, Any]:
    projected = copy.deepcopy(derived)
    tools = projected.get("tools", [])
    if not isinstance(tools, list):
        raise CapabilityError("tools must be an array")
    for tool in tools:
        if not isinstance(tool, dict):
            raise CapabilityError("every tool row must be an object")
        if not isinstance(tool.get("degradedBehavior"), str) or not tool["degradedBehavior"].strip():
            raise CapabilityError(f"{tool.get('qualifiedCapabilityId', '<unknown>')} lacks degraded behavior")
        tool.pop("degradedBehavior")
    return projected


def _unique(values: list[str], label: str) -> set[str]:
    unique = set(values)
    if len(unique) != len(values):
        raise CapabilityError(f"duplicate {label}")
    return unique


def _object_rows(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = payload.get(key)
    if not isinstance(rows, list):
        raise CapabilityError(f"{key} must be an array")
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise CapabilityError(f"{key}[{index}] must be an object")
        normalized.append(cast("dict[str, Any]", row))
    return normalized


def validate_capabilities(derived: dict[str, Any], source: dict[str, Any]) -> None:
    """Enforce source parity and the skill-owned semantic closure."""
    _validate_source_schema(source)
    if _source_projection(derived) != source:
        raise CapabilityError("references/capabilities.json does not exactly project the frozen OpenSpec manifest")

    counts = source.get("counts")
    if counts != {
        "tools": 70,
        "coreTools": 41,
        "shortcutTools": 21,
        "nativeTools": 8,
        "supaOutcomes": 37,
        "workflows": 17,
        "legacyEvalIds": 25,
        "newEvalIds": 16,
    }:
        raise CapabilityError("frozen cardinalities changed without an OpenSpec revision")

    tools = _object_rows(derived, "tools")
    outcomes = _object_rows(derived, "supaOutcomes")
    workflows = _object_rows(derived, "workflows")
    legacy_evals = _object_rows(derived, "legacyEvals")
    new_evals = _object_rows(derived, "newEvals")
    if (len(tools), len(outcomes), len(workflows), len(legacy_evals), len(new_evals)) != (70, 37, 17, 25, 16):
        raise CapabilityError("capability inventories do not match 70/37/17/25/16")

    _validate_adapted_schema_hashes(tools)
    qualified = _unique([row["qualifiedCapabilityId"] for row in tools], "qualified capability id")
    public = _unique([row["publicToolName"] for row in tools], "public tool name")
    if len(public) != 70:
        raise CapabilityError("public Things++ tool closure is not exactly 70")

    by_server = {
        server: sum(row["server"] == server for row in tools)
        for server in ("things-core", "things-shortcuts", "things-native")
    }
    if by_server != {"things-core": 41, "things-shortcuts": 21, "things-native": 8}:
        raise CapabilityError(f"backend partition changed: {by_server}")

    for row in tools:
        expected_public = f"{row['server'].replace('-', '_')}__{row['serverToolName']}"
        if row["publicToolName"] != expected_public or row["expectedMcphubQualifiedName"] != expected_public:
            raise CapabilityError(f"invalid public name for {row['qualifiedCapabilityId']}")
        if row["minimumIndependentScope"] not in {"things.read", "things.write", "things.admin"}:
            raise CapabilityError(f"invalid scope for {row['qualifiedCapabilityId']}")
        if not row["backendPrerequisites"] or not row["testIds"]:
            raise CapabilityError(f"missing prerequisite or test ids for {row['qualifiedCapabilityId']}")

    workflow_ids = _unique([row["workflowId"] for row in workflows], "workflow id")
    for row in outcomes:
        if row["status"] != "mapped" or not row["targetCapabilityIds"] or not row["testIds"]:
            raise CapabilityError(f"unmapped historical outcome: {row['supaToolName']}")
        if not set(row["targetCapabilityIds"]).issubset(qualified):
            raise CapabilityError(f"unknown target for historical outcome: {row['supaToolName']}")
        if not set(row["workflowIds"]).issubset(workflow_ids):
            raise CapabilityError(f"unknown workflow for historical outcome: {row['supaToolName']}")

    for row in workflows:
        if row["status"] != "mapped" or not set(row["targetCapabilityIds"]).issubset(qualified):
            raise CapabilityError(f"unmapped workflow: {row['workflowId']}")
        if not row["testIds"]:
            raise CapabilityError(f"workflow lacks tests: {row['workflowId']}")

    legacy_ids = _unique([row["legacyEvalId"] for row in legacy_evals], "legacy eval id")
    replacement_ids = _unique([row["replacementEvalId"] for row in legacy_evals], "replacement eval id")
    new_ids = _unique([row["evalId"] for row in new_evals], "additive eval id")
    if legacy_ids != replacement_ids or legacy_ids & new_ids:
        raise CapabilityError("eval IDs do not preserve the exact 25 plus 16 partition")
    if not source.get("netNewOutcomeIds"):
        raise CapabilityError("coverage expansion requires at least one net-new outcome")

    group = source.get("group", {})
    if group.get("name") != "things" or group.get("localPath") != group.get("remotePath"):
        raise CapabilityError("Things++ must use the sole local/remote things group")


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _list_cell(values: list[str]) -> str:
    return "<br>".join(f"`{_cell(value)}`" for value in values)


def render_markdown(data: dict[str, Any]) -> str:
    counts = data["counts"]
    group = data["group"]
    lines = [
        "# Things++ Capability Ledger",
        "",
        "<!-- Generated by scripts/render_capabilities.py; do not edit by hand. -->",
        "",
        "This ledger is the deterministic skill projection of the active OpenSpec capability manifest. It contains",
        f"exactly {counts['tools']} public tools ({counts['coreTools']} core + {counts['shortcutTools']} Shortcuts +",
        f"{counts['nativeTools']} native), {counts['supaOutcomes']} historical outcome mappings,",
        f"{counts['workflows']} workflows, {counts['legacyEvalIds']} rewritten legacy eval IDs, and",
        f"{counts['newEvalIds']} additive eval IDs.",
        "",
        "## Sole MCPHub Route",
        "",
        f"- Group: `{group['name']}` (`{group['deterministicId']}`)",
        f"- Local: `{group['localResource']}`",
        f"- Remote contract (implementation/apply authorized; activation evidence gated): `{group['remoteResource']}`",
        f"- Internal members: {_list_cell(group['servers'])}",
        "- Clients call only this group. Individual backend routes, alternate Things groups, and generic-group",
        "  membership are prohibited.",
        "- OAuth grants `things.read`, `things.write`, and `things.admin` independently; authentication never",
        "  replaces preview, receipt, confirmation, or per-call approval.",
        "",
        "## Routing Rules",
        "",
        "Use core first. Select a Shortcuts or native tool only when the workflow or capability row explicitly names",
        "that typed gap. Server-executed mutations use preview then execute with a fresh, single-use receipt while",
        "all backends share one serialization reservation. Quick Entry is a UI handoff and returns no changed item",
        "until the user saves. Recurrence-template editing, deterministic positional reorder, tag-parent detach, raw",
        "JSON/URL passthrough, generic Shortcut execution, and arbitrary AppleScript remain unsupported.",
        "",
        "## Public Tool Inventory",
        "",
        "| Public tool | Capability | Backend | Scope | Risk | Prerequisites | Degraded behavior | Tests |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for tool in data["tools"]:
        lines.append(
            "| "
            + " | ".join([
                f"`{_cell(tool['publicToolName'])}`",
                f"`{_cell(tool['qualifiedCapabilityId'])}`",
                f"`{_cell(tool['server'])}`",
                f"`{_cell(tool['minimumIndependentScope'])}`",
                f"`{_cell(tool['risk'])}`",
                _list_cell(tool["backendPrerequisites"]),
                _cell(tool["degradedBehavior"]),
                _list_cell(tool["testIds"]),
            ])
            + " |"
        )

    lines.extend([
        "",
        "## Historical Outcome Closure",
        "",
        "Historical names below are provenance-only. They are never active aliases or routable tool names.",
        "",
        "| Historical outcome | Mapping | Target capabilities | Semantic workflows | Status | Tests |",
        "|---|---|---|---|---|---|",
    ])
    for outcome in data["supaOutcomes"]:
        lines.append(
            "| "
            + " | ".join([
                f"`{_cell(outcome['supaToolName'])}`",
                f"`{_cell(outcome['mappingKind'])}`",
                _list_cell(outcome["targetCapabilityIds"]),
                _list_cell(outcome["workflowIds"]) if outcome["workflowIds"] else "-",
                f"`{_cell(outcome['status'])}`",
                _list_cell(outcome["testIds"]),
            ])
            + " |"
        )

    lines.extend([
        "",
        "## Workflow Routes",
        "",
        "| Workflow ID | Target capabilities | Status | Tests |",
        "|---|---|---|---|",
    ])
    for workflow in data["workflows"]:
        lines.append(
            f"| `{_cell(workflow['workflowId'])}` | {_list_cell(workflow['targetCapabilityIds'])} | "
            f"`{_cell(workflow['status'])}` | {_list_cell(workflow['testIds'])} |"
        )

    lines.extend(["", "## Eval Closure", "", "### Rewritten legacy IDs", ""])
    lines.extend(f"- `{row['replacementEvalId']}` — tests: {_list_cell(row['testIds'])}" for row in data["legacyEvals"])
    lines.extend(["", "### Additive Things++ IDs", ""])
    lines.extend(
        f"- `{row['evalId']}` — {_cell(row['purpose'])} Tests: {_list_cell(row['testIds'])}" for row in data["newEvals"]
    )
    lines.extend(["", "## Net-New Outcomes", ""])
    lines.extend(f"- `{outcome_id}`" for outcome_id in data["netNewOutcomeIds"])
    return "\n".join(lines) + "\n"


def sync_from_source() -> None:
    source = _load_json(SOURCE_PATH)
    derived = _derived_manifest(source)
    validate_capabilities(derived, source)
    CAPABILITIES_JSON.write_text(json.dumps(derived, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(derived)
    CAPABILITIES_MD.write_text(markdown, encoding="utf-8")
    CHATGPT_CAPABILITIES_MD.parent.mkdir(parents=True, exist_ok=True)
    CHATGPT_CAPABILITIES_MD.write_text(markdown, encoding="utf-8")


def check() -> None:
    source = _load_json(SOURCE_PATH)
    derived = _load_json(CAPABILITIES_JSON)
    validate_capabilities(derived, source)
    expected_markdown = render_markdown(derived)
    try:
        actual_markdown = CAPABILITIES_MD.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise CapabilityError(f"missing generated capability ledger: {CAPABILITIES_MD}") from exc
    if actual_markdown != expected_markdown:
        raise CapabilityError("references/capabilities.md is stale; run render_capabilities.py --sync-source")
    try:
        actual_chatgpt_markdown = CHATGPT_CAPABILITIES_MD.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise CapabilityError(f"missing generated ChatGPT capability ledger: {CHATGPT_CAPABILITIES_MD}") from exc
    if actual_chatgpt_markdown != expected_markdown:
        raise CapabilityError("ChatGPT CAPABILITY_MATRIX.md is stale; run render_capabilities.py --sync-source")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail if JSON source parity or generated Markdown drifts")
    mode.add_argument("--sync-source", action="store_true", help="Refresh JSON and Markdown from the frozen OpenSpec")
    args = parser.parse_args(argv)

    try:
        if args.sync_source:
            sync_from_source()
        elif args.check:
            check()
        else:
            derived = _load_json(CAPABILITIES_JSON)
            source = _load_json(SOURCE_PATH)
            validate_capabilities(derived, source)
            markdown = render_markdown(derived)
            CAPABILITIES_MD.write_text(markdown, encoding="utf-8")
            CHATGPT_CAPABILITIES_MD.parent.mkdir(parents=True, exist_ok=True)
            CHATGPT_CAPABILITIES_MD.write_text(markdown, encoding="utf-8")
    except CapabilityError as exc:
        print(f"things-manager capabilities: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
