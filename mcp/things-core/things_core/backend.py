"""Lazy, provenance-gated delegation to the upstream FastMCP server."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from fastmcp import Client

from things_common import SecurityViolation, canonical_schema_sha256, canonical_sha256, secure_read_bytes

from .contracts import load_contracts
from .provenance import ProvenanceError, verify_installed_distribution

_AUTH_FILE_NAME = ".things-auth"
_SAFE_UPSTREAM_ENV = {
    "THINGS_MCP_APPLESCRIPT_RETRY_COUNT": "0",
    "THINGS_MCP_APPLESCRIPT_TIMEOUT": "60",
    "THINGS_MCP_BATCH_OPERATION_MAX_SIZE": "25",
    "THINGS_MCP_LOG_LEVEL": "ERROR",
    "THINGS_MCP_MAX_CHECKLIST_ITEMS": "25",
    "THINGS_MCP_MAX_CONCURRENT_OPERATIONS": "1",
    "THINGS_MCP_SEARCH_RESULTS_LIMIT": "25",
    "THINGS_MCP_TAG_CREATION_POLICY": "fail_on_unknown",
}
_CHECKLIST_TOOLS = frozenset({"add_checklist_items", "prepend_checklist_items", "replace_checklist_items"})
_CREATE_TOOLS = frozenset({"add_area", "add_project", "add_todo", "create_tag"})
_TARGET_FIELDS = frozenset({"id", "project_id", "project_uuid", "record_ids", "todo_id", "todo_ids"})
_CONTROL_FIELDS = frozenset({"max_concurrent"})


class UpstreamContractError(ProvenanceError):
    """The imported upstream FastMCP inventory differs from audited bytes."""


def _disable_upstream_logging() -> None:
    """Prevent upstream exception strings from reaching inherited handlers."""
    for name, candidate in logging.Logger.manager.loggerDict.items():
        if (name == "things_mcp" or name.startswith("things_mcp.")) and isinstance(candidate, logging.Logger):
            candidate.disabled = True


def read_safe_auth_token(home: Path | None = None) -> tuple[str | None, list[dict[str, str]]]:
    """Read only ``~/.things-auth`` through the shared secure-file gate."""
    auth_file = (Path.home() if home is None else Path(home)) / _AUTH_FILE_NAME
    try:
        payload = secure_read_bytes(auth_file, max_bytes=4_096)
    except FileNotFoundError:
        return None, [{"path": "~/.things-auth", "status": "missing"}]
    except SecurityViolation:
        raise
    try:
        raw = payload.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise SecurityViolation("Things auth file is not strict UTF-8.") from exc
    if "\x00" in raw or "\n" in raw or "\r" in raw:
        raise SecurityViolation("Things auth file must contain one bounded token value.")
    if "=" in raw:
        key, raw = raw.split("=", 1)
        if key.strip() != "THINGS_AUTH_TOKEN":
            raise SecurityViolation("Things auth file uses an unsupported key.")
        raw = raw.strip()
    if not raw:
        return None, [{"path": "~/.things-auth", "status": "empty"}]
    if len(raw) > 2_048:
        raise SecurityViolation("Things auth token exceeds its maximum length.")
    return raw, [{"path": "~/.things-auth", "status": "matched"}]


@contextlib.contextmanager
def _sanitized_upstream_environment() -> Any:
    """Suppress dotenv/config-file discovery and unsafe upstream overrides."""
    saved = {key: value for key, value in os.environ.items() if key.startswith("THINGS_MCP_")}
    saved_dotenv = os.environ.get("PYTHON_DOTENV_DISABLED")
    for key in list(os.environ):
        if key.startswith("THINGS_MCP_"):
            del os.environ[key]
    os.environ.update(_SAFE_UPSTREAM_ENV)
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    try:
        yield
    finally:
        for key in list(os.environ):
            if key.startswith("THINGS_MCP_"):
                del os.environ[key]
        os.environ.update(saved)
        if saved_dotenv is None:
            os.environ.pop("PYTHON_DOTENV_DISABLED", None)
        else:
            os.environ["PYTHON_DOTENV_DISABLED"] = saved_dotenv


async def verify_live_tool_contract(upstream_mcp: Any) -> None:
    """Verify imported FastMCP names and schemas before allowing a call."""
    expected = load_contracts()
    async with Client(upstream_mcp) as client:
        tools = list(await client.list_tools())
    if [tool.name for tool in tools] != [contract.name for contract in expected]:
        raise UpstreamContractError("things_core_upstream_tool_names_mismatch")
    for tool, contract in zip(tools, expected, strict=True):
        if canonical_schema_sha256(tool.inputSchema) != contract.audited_input_sha256:
            raise UpstreamContractError("things_core_upstream_input_schema_mismatch")
        if canonical_schema_sha256(tool.outputSchema or {}) != contract.audited_output_sha256:
            raise UpstreamContractError("things_core_upstream_output_schema_mismatch")


def _result_data(result: Any) -> Any:
    if getattr(result, "is_error", False):
        raise RuntimeError("things_core_upstream_call_failed")
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        if set(structured) == {"result"}:
            return structured["result"]
        return structured
    data = getattr(result, "data", None)
    if data is not None:
        if hasattr(data, "model_dump"):
            return data.model_dump(mode="json")
        return data
    content = getattr(result, "content", [])
    values = [getattr(item, "text", None) for item in content if getattr(item, "text", None) is not None]
    return {"messages": values[:25]}


def _target_values(arguments: dict[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for field in ("id", "todo_id", "todo_ids", "project_id", "project_uuid", "record_ids"):
        value = arguments.get(field)
        if isinstance(value, str):
            values.extend(item.strip() for item in value.split(",") if item.strip())
        elif isinstance(value, list):
            values.extend(str(item) for item in value)
    return tuple(dict.fromkeys(values))[:25]


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _created_ids(result: Any) -> tuple[str, ...]:
    values: list[str] = []
    for node in _walk(result):
        if not isinstance(node, dict):
            continue
        for key in ("id", "todo_id", "uuid", "project_id"):
            value = node.get(key)
            if isinstance(value, str) and value and not value.startswith(("things://", "file://")):
                values.append(value)
    return tuple(dict.fromkeys(values))[:25]


def _explicit_failure_count(result: Any) -> int:
    count = 0
    for node in _walk(result):
        if not isinstance(node, dict):
            continue
        status = str(node.get("status", "")).casefold()
        success = node.get("success")
        if success is False or status in {"error", "failed", "failure"}:
            count += 1
    return min(count, 25)


def _normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _record_view(value: Any) -> dict[str, Any] | None:
    """Unwrap one known response envelope without searching unrelated children."""
    if not isinstance(value, dict):
        return None
    current = value
    for _ in range(4):
        child = next(
            (
                current[key]
                for key in ("item", "todo", "project", "area", "tag", "record", "result")
                if isinstance(current.get(key), dict)
            ),
            None,
        )
        if child is None:
            break
        current = child
    return current


def _direct_value(value: Any, *aliases: str) -> tuple[bool, Any]:
    record = _record_view(value)
    if record is None:
        return False, None
    indexed = {_normalized_key(str(key)): item for key, item in record.items()}
    for alias in aliases:
        normalized = _normalized_key(alias)
        if normalized in indexed:
            return True, indexed[normalized]
    return False, None


def _record_identifier(value: Any) -> str | None:
    found, identifier = _direct_value(value, "id", "uuid", "todo_id", "project_id", "area_id", "tag_id")
    return identifier if found and isinstance(identifier, str) and identifier else None


def _find_record(value: Any, identifier: str) -> Any | None:
    for node in _walk(value):
        if isinstance(node, dict) and _record_identifier(node) == identifier:
            return node
    return None


def _target_rows(value: Any, target_ids: tuple[str, ...]) -> list[Any | None]:
    if isinstance(value, list) and len(value) == len(target_ids):
        return list(value)
    return [_find_record(value, target_id) for target_id in target_ids]


def _as_tags(value: Any) -> set[str] | None:
    if isinstance(value, str):
        return {item.strip() for item in value.split(",") if item.strip()}
    if not isinstance(value, list):
        return None
    result: set[str] = set()
    for item in value:
        if isinstance(item, str):
            result.add(item)
        elif isinstance(item, dict):
            found, title = _direct_value(item, "title", "name", "tag_name")
            if not found or not isinstance(title, str):
                return None
            result.add(title)
        else:
            return None
    return result


def _as_titles(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    titles: list[str] = []
    for item in value:
        if isinstance(item, str):
            titles.append(item)
        elif isinstance(item, dict):
            found, title = _direct_value(item, "title", "name")
            if not found or not isinstance(title, str):
                return None
            titles.append(title)
        else:
            return None
    return titles


def _field_match(tool: str, record: Any, field: str, expected: Any) -> bool | None:
    aliases: dict[str, tuple[str, ...]] = {
        "area_id": ("area_id", "areaId", "area"),
        "area_title": ("area_title", "areaTitle"),
        "deadline": ("deadline", "due_date", "dueDate"),
        "heading": ("heading", "heading_title", "headingTitle"),
        "list_id": ("list_id", "listId", "project_id", "projectId", "project", "area_id", "areaId", "area"),
        "list_title": ("list_title", "listTitle", "project_title", "projectTitle", "area_title", "areaTitle"),
        "notes": ("notes", "note"),
        "tag_name": ("tag_name", "tagName", "name", "title"),
        "title": ("title", "name"),
        "when": ("when", "start", "start_date", "startDate"),
    }
    if field == "tags":
        found, actual = _direct_value(record, "tags", "tag_names", "tagNames")
        if not found:
            return None
        actual_tags = _as_tags(actual)
        expected_tags = _as_tags(expected)
        if actual_tags is None or expected_tags is None:
            return None
        if tool == "add_tags":
            return expected_tags <= actual_tags
        if tool == "remove_tags":
            return actual_tags.isdisjoint(expected_tags)
        return actual_tags == expected_tags
    if field in {"checklist_items", "items"}:
        actual = _checklist_titles(record)
        expected_titles = _as_titles(expected)
        return None if actual is None or expected_titles is None else actual == expected_titles
    if field == "todos":
        found, actual = _direct_value(record, "todos", "items")
        if not found or not isinstance(expected, str):
            return None
        expected_titles = [
            line.strip() for line in expected.splitlines() if line.strip() and not line.lstrip().startswith("##")
        ]
        actual_titles = _as_titles(actual)
        return None if actual_titles is None else actual_titles == expected_titles
    if field in {"completed", "canceled"}:
        found_flag, actual_flag = _direct_value(record, field)
        if found_flag and isinstance(actual_flag, bool):
            return actual_flag is expected
        found_status, actual_status = _direct_value(record, "status")
        if not found_status or not isinstance(actual_status, str) or not isinstance(expected, bool):
            return None
        desired = field
        if expected:
            return actual_status.casefold() == desired
        return actual_status.casefold() == "incomplete"
    if field in {"destination", "destination_list"}:
        if not isinstance(expected, str):
            return None
        prefix, separator, identifier = expected.partition(":")
        if separator and prefix.casefold() in {"project", "area"}:
            found, actual = _direct_value(record, f"{prefix}_id", f"{prefix}Id", prefix)
            return None if not found else str(actual) == identifier
        found, actual = _direct_value(record, "destination", "destination_list", "destinationList", "start", "list")
        return None if not found or not isinstance(actual, str) else actual.casefold() == expected.casefold()
    field_aliases = aliases.get(field)
    if field_aliases is None:
        return None
    found, actual = _direct_value(record, *field_aliases)
    if not found:
        return None
    if field in {"deadline", "notes"} and expected == "":
        return actual in {None, ""}
    if isinstance(expected, str) and isinstance(actual, str):
        return actual.casefold() == expected.casefold() if field == "when" else actual == expected
    return actual == expected


def _requested_fields(arguments: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    return tuple(
        (field, value)
        for field, value in arguments.items()
        if field not in _TARGET_FIELDS and field not in _CONTROL_FIELDS
    )


def _record_matches(tool: str, record: Any, fields: tuple[tuple[str, Any], ...]) -> bool | None:
    matches = [_field_match(tool, record, field, expected) for field, expected in fields]
    if not matches:
        return None
    if any(match is False for match in matches):
        return False
    if any(match is None for match in matches):
        return None
    return True


def _explicit_failure_ids(result: Any) -> set[str]:
    failures: set[str] = set()
    for node in _walk(result):
        if not isinstance(node, dict):
            continue
        for key in ("failed_ids", "not_found", "not_found_ids"):
            values = node.get(key)
            if isinstance(values, list):
                failures.update(str(value) for value in values if isinstance(value, str) and value)
        status = str(node.get("status", "")).casefold()
        if node.get("success") is False or status in {"error", "failed", "failure"}:
            identifier = _record_identifier(node)
            if identifier is not None:
                failures.add(identifier)
    return failures


def _single_explicit_failure(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    status = str(result.get("status", "")).casefold()
    return result.get("success") is False or status in {"error", "failed", "failure"}


def _absent(value: Any) -> bool:
    found, status = _direct_value(value, "status")
    if found and isinstance(status, str) and status.casefold() in {"absent", "deleted", "trashed"}:
        return True
    found, trashed = _direct_value(value, "trashed")
    return found and trashed is True


def _checklist_titles(value: Any) -> list[str] | None:
    for node in _walk(value):
        if not isinstance(node, dict):
            continue
        for key in ("checklist", "checklist_items", "items"):
            items = node.get(key)
            if not isinstance(items, list):
                continue
            titles: list[str] = []
            for item in items:
                if isinstance(item, str):
                    titles.append(item)
                elif isinstance(item, dict) and isinstance(item.get("title"), str):
                    titles.append(item["title"])
                else:
                    break
            else:
                return titles
    return None


class UpstreamThingsBackend:
    """Generic backend that delegates every domain operation to upstream MCP."""

    def __init__(self) -> None:
        self._server: Any = None
        self._initialize_lock = asyncio.Lock()

    async def _ensure_server(self) -> Any:
        if self._server is not None:
            return self._server
        async with self._initialize_lock:
            if self._server is not None:
                return self._server
            verify_installed_distribution(allow_tunnel_disabled_development=True)
            read_safe_auth_token()
            previous_cwd = Path.cwd()
            with tempfile.TemporaryDirectory(prefix="things-core-") as private_directory:
                os.chmod(private_directory, 0o700)
                with _sanitized_upstream_environment():
                    try:
                        os.chdir(private_directory)
                        from things_mcp.services.applescript_manager import AppleScriptManager

                        def load_only_safe_home(_manager: Any) -> tuple[str | None, list[dict[str, str]]]:
                            return read_safe_auth_token()

                        # Upstream exposes no constructor seam for its auth loader. Install the
                        # audited fixed implementation explicitly without assigning through the
                        # third-party method's narrower static type.
                        setattr(AppleScriptManager, "_load_auth_token", load_only_safe_home)  # noqa: B010
                        from things_mcp.server import ThingsMCPServer

                        candidate = ThingsMCPServer(env_file=None)
                        _disable_upstream_logging()
                    finally:
                        os.chdir(previous_cwd)
            await verify_live_tool_contract(candidate.mcp)
            self._server = candidate
            return candidate

    async def call(self, tool: str, arguments: dict[str, Any]) -> Any:
        """Call one exact audited upstream MCP tool."""
        server = await self._ensure_server()
        async with Client(server.mcp) as client:
            result = await client.call_tool(tool, arguments, raise_on_error=False)
        return _result_data(result)

    async def read_state(self, tool: str, arguments: dict[str, Any]) -> Any:
        """Read a bounded target snapshot without invoking a mutation."""
        target_ids = _target_values(arguments)
        collection_reader = {
            "update_project": "get_projects",
            "update_area": "get_areas",
        }.get(tool)
        if collection_reader is not None and target_ids:
            try:
                snapshot = await self.call(
                    collection_reader,
                    {"include_items": False, "mode": "minimal"},
                )
            except RuntimeError:
                return [{"status": "absent"} for _ in target_ids]
            return [_find_record(snapshot, target_id) or {"status": "absent"} for target_id in target_ids]
        if target_ids:
            rows: list[Any] = []
            for target_id in target_ids:
                try:
                    rows.append(await self.call("get_todo_by_id", {"todo_id": target_id}))
                except RuntimeError:
                    rows.append({"status": "absent"})
            return rows
        state_tool, state_arguments = {
            "add_area": ("get_areas", {"include_items": False, "mode": "minimal"}),
            "add_project": ("get_projects", {"include_items": False, "mode": "minimal"}),
            "add_todo": ("get_todos", {"include_items": False, "limit": 25, "mode": "minimal"}),
            "create_tag": ("get_tags", {"include_items": False}),
        }.get(tool, ("get_todos", {"include_items": False, "limit": 25, "mode": "minimal"}))
        return await self.call(state_tool, state_arguments)

    async def verify(
        self,
        tool: str,
        arguments: dict[str, Any],
        before: Any,
        result: Any,
    ) -> dict[str, Any]:
        """Classify each target only from explicit result and field readback evidence."""
        target_ids = _target_values(arguments)
        target_count = max(1, len(target_ids))
        fields = _requested_fields(arguments)
        created_ids = _created_ids(result)
        after = await self.read_state(tool, arguments)
        counts = {"changed": 0, "skipped": 0, "failed": 0, "ambiguous": 0}

        if tool in _CREATE_TOOLS:
            if _single_explicit_failure(result):
                counts["failed"] = 1
            elif not created_ids:
                counts["ambiguous"] = 1
            else:
                created_id = created_ids[0]
                created = _find_record(after, created_id)
                existed_before = _find_record(before, created_id)
                match = _record_matches(tool, created, fields)
                if created is None or match is not True or existed_before is not None:
                    counts["ambiguous"] = 1
                else:
                    counts["changed"] = 1
        else:
            before_rows = _target_rows(before, target_ids)
            after_rows = _target_rows(after, target_ids)
            failed_ids = _explicit_failure_ids(result)
            for index, target_id in enumerate(target_ids):
                previous = before_rows[index]
                current = after_rows[index]
                if target_id in failed_ids or (target_count == 1 and _single_explicit_failure(result)):
                    counts["failed"] += 1
                    continue
                if tool == "delete_todo":
                    if _absent(current) and not _absent(previous):
                        counts["changed"] += 1
                    elif _absent(current) and _absent(previous):
                        counts["skipped"] += 1
                    else:
                        counts["ambiguous"] += 1
                    continue
                if tool in _CHECKLIST_TOOLS:
                    expected = arguments.get("items")
                    previous_titles = _checklist_titles(previous)
                    current_titles = _checklist_titles(current)
                    expected_titles = _as_titles(expected)
                    if previous_titles is None or current_titles is None or expected_titles is None:
                        counts["ambiguous"] += 1
                        continue
                    if tool == "add_checklist_items":
                        exact = current_titles == previous_titles + expected_titles
                    elif tool == "prepend_checklist_items":
                        exact = current_titles == expected_titles + previous_titles
                    else:
                        exact = current_titles == expected_titles
                    if not exact:
                        counts["ambiguous"] += 1
                    elif current_titles == previous_titles:
                        counts["skipped"] += 1
                    else:
                        counts["changed"] += 1
                    continue
                current_match = _record_matches(tool, current, fields)
                if current_match is not True:
                    counts["ambiguous"] += 1
                    continue
                previous_match = _record_matches(tool, previous, fields)
                if previous_match is True:
                    counts["skipped"] += 1
                else:
                    counts["changed"] += 1

        if sum(counts.values()) != target_count:
            raise RuntimeError("things_core_verification_count_mismatch")
        return {
            **counts,
            "readbackVerified": counts["ambiguous"] == 0,
            "beforeDigest": canonical_sha256(before),
            "afterDigest": canonical_sha256(after),
        }


def auth_doctor() -> dict[str, Any]:
    """Return only the auth prerequisite state, never a token or local path."""
    try:
        token, trace = read_safe_auth_token()
    except SecurityViolation:
        return {"status": "blocked", "code": "things_core_auth_file_unsafe"}
    return {
        "status": "ready" if token else "optional",
        "code": "things_core_auth_present" if token else "things_core_auth_absent",
        "checked": len(trace),
    }
