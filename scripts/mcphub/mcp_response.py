"""Parse and validate MCP Streamable HTTP responses for local smoke tests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

type JsonRpcId = str | int | None


class McpResponseError(ValueError):
    """Raised when an MCP response violates the smoke-test contract."""


def _decode_utf8(raw: bytes, *, source: str) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise McpResponseError(f"{source} is not valid UTF-8") from exc


def parse_final_headers(raw_headers: bytes) -> dict[str, str]:
    """Return the final HTTP header block, with case-insensitive field names."""
    lines = _decode_utf8(raw_headers, source="response headers").splitlines()
    final_headers: dict[str, str] | None = None
    current_headers: dict[str, str] | None = None

    for line in lines:
        if line.upper().startswith("HTTP/"):
            current_headers = {}
            final_headers = current_headers
            continue
        if current_headers is None or not line or line[:1].isspace():
            continue
        name, separator, value = line.partition(":")
        if not separator:
            continue
        current_headers[name.strip().lower()] = value.strip()

    if final_headers is None:
        raise McpResponseError("response headers do not contain an HTTP status line")
    return final_headers


def final_header(raw_headers: bytes, name: str) -> str:
    """Return a required, non-empty field from the final HTTP header block."""
    value = parse_final_headers(raw_headers).get(name.lower(), "")
    if not value:
        raise McpResponseError(f"final response headers do not contain {name}")
    return value


def _sse_data_payloads(body: str) -> list[str]:
    payloads: list[str] = []
    data_lines: list[str] = []

    def flush_event() -> None:
        if not data_lines:
            return
        payload = "\n".join(data_lines)
        data_lines.clear()
        if payload:
            payloads.append(payload)

    for line in body.splitlines():
        if not line:
            flush_event()
            continue
        if line.startswith(":"):
            continue
        field, separator, value = line.partition(":")
        if field != "data":
            continue
        if not separator:
            value = ""
        elif value.startswith(" "):
            value = value[1:]
        data_lines.append(value)
    flush_event()
    return payloads


def _load_json_object(payload: str, *, source: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise McpResponseError(f"{source} does not contain valid JSON") from exc
    if not isinstance(value, dict):
        raise McpResponseError(f"{source} must contain a JSON object")
    return value


def parse_response_messages(raw_headers: bytes, raw_body: bytes) -> list[dict[str, Any]]:
    """Decode JSON-RPC objects from an application/json or SSE response."""
    content_type = final_header(raw_headers, "Content-Type")
    media_type = content_type.partition(";")[0].strip().lower()
    body = _decode_utf8(raw_body, source="response body")

    if media_type == "application/json":
        return [_load_json_object(body, source="JSON response body")]
    if media_type == "text/event-stream":
        payloads = _sse_data_payloads(body)
        if not payloads:
            raise McpResponseError("SSE response does not contain a data event")
        return [_load_json_object(payload, source="SSE data event") for payload in payloads]
    raise McpResponseError(f"unsupported response Content-Type: {media_type or '<empty>'}")


def _ids_match(actual: object, expected: JsonRpcId) -> bool:
    if isinstance(actual, bool) or isinstance(expected, bool):
        return False
    return type(actual) is type(expected) and actual == expected


def select_response(messages: Iterable[dict[str, Any]], *, response_id: JsonRpcId) -> dict[str, Any]:
    """Select and validate exactly one JSON-RPC response with the requested id."""
    matches = [message for message in messages if "id" in message and _ids_match(message["id"], response_id)]
    if not matches:
        raise McpResponseError("response does not contain the requested JSON-RPC id")
    if len(matches) != 1:
        raise McpResponseError("response contains duplicate messages for the requested JSON-RPC id")

    response = matches[0]
    if response.get("jsonrpc") != "2.0":
        raise McpResponseError("response does not declare jsonrpc 2.0")
    if "error" in response:
        raise McpResponseError("JSON-RPC response contains an error")
    if "result" not in response:
        raise McpResponseError("JSON-RPC response does not contain a result")
    if not isinstance(response["result"], dict):
        raise McpResponseError("JSON-RPC result must be an object")
    return response


def parse_protocol_version(raw_headers: bytes, raw_body: bytes, *, response_id: JsonRpcId) -> str:
    """Return the non-empty protocolVersion negotiated by initialize."""
    response = select_response(parse_response_messages(raw_headers, raw_body), response_id=response_id)
    protocol_version = response["result"].get("protocolVersion")
    if not isinstance(protocol_version, str) or not protocol_version.strip():
        raise McpResponseError("initialize result does not contain a non-empty protocolVersion")
    return protocol_version


def parse_tool_names(raw_headers: bytes, raw_body: bytes, *, response_id: JsonRpcId) -> list[str]:
    """Return a complete, duplicate-free tools/list response."""
    response = select_response(parse_response_messages(raw_headers, raw_body), response_id=response_id)
    result = response["result"]
    tools = result.get("tools")
    if not isinstance(tools, list):
        raise McpResponseError("tools/list result does not contain a tools array")

    next_cursor = result.get("nextCursor")
    if next_cursor not in (None, ""):
        raise McpResponseError("tools/list response is paginated; smoke requires a complete first response")

    names: list[str] = []
    for tool in tools:
        if not isinstance(tool, dict):
            raise McpResponseError("tools/list contains a non-object tool entry")
        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            raise McpResponseError("tools/list contains a tool with a non-string or empty name")
        names.append(name)

    if len(names) != len(set(names)):
        raise McpResponseError("tools/list contains duplicate tool names")
    return names


def assert_expected_tools(actual: Sequence[str], expected: Sequence[str], *, mode: str) -> None:
    """Assert exact equality or expected-name containment without relying on order."""
    if len(expected) != len(set(expected)):
        raise McpResponseError("expected tool names contain duplicates")
    actual_set = set(actual)
    expected_set = set(expected)
    missing = expected_set - actual_set
    extra = actual_set - expected_set
    if missing or (mode == "exact" and extra):
        details = [f"missing={sorted(missing)}"]
        if mode == "exact":
            details.append(f"unexpected={sorted(extra)}")
        raise McpResponseError("tools/list does not satisfy the expected tool-name contract: " + ", ".join(details))


def _parse_response_id(value: str) -> JsonRpcId:
    try:
        response_id = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError("response id must be a JSON string, integer, or null") from exc
    if isinstance(response_id, bool) or not isinstance(response_id, str | int | type(None)):
        raise argparse.ArgumentTypeError("response id must be a JSON string, integer, or null")
    return response_id


def _add_response_files(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--headers", type=Path, required=True)
    parser.add_argument("--body", type=Path, required=True)
    parser.add_argument("--response-id", type=_parse_response_id, required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    session_parser = subparsers.add_parser("session-id", help="Print the final MCP-Session-Id response header")
    session_parser.add_argument("--headers", type=Path, required=True)

    protocol_parser = subparsers.add_parser("protocol-version", help="Print initialize result.protocolVersion")
    _add_response_files(protocol_parser)

    tools_parser = subparsers.add_parser("assert-tools", help="Validate a tools/list response")
    _add_response_files(tools_parser)
    tools_parser.add_argument("--mode", choices=("contains", "exact"), default="contains")
    tools_parser.add_argument("--expect", action="append", default=[])
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        raw_headers = args.headers.read_bytes()
        if args.command == "session-id":
            print(final_header(raw_headers, "MCP-Session-Id"))
            return 0

        raw_body = args.body.read_bytes()
        if args.command == "protocol-version":
            print(parse_protocol_version(raw_headers, raw_body, response_id=args.response_id))
            return 0

        names = parse_tool_names(raw_headers, raw_body, response_id=args.response_id)
        assert_expected_tools(names, args.expect, mode=args.mode)
    except (McpResponseError, OSError) as exc:
        print(f"MCP response validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
