"""Hermetic response-contract tests for the MCPHub HTTP smoke helper."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from scripts.mcphub.mcp_response import (
    McpResponseError,
    assert_expected_tools,
    final_header,
    main,
    parse_final_headers,
    parse_protocol_version,
    parse_response_messages,
    parse_tool_names,
    select_response,
)

if TYPE_CHECKING:
    from pathlib import Path


def response_headers(content_type: str = "application/json; charset=utf-8", *, separator: str = "\r\n") -> bytes:
    return (
        f"HTTP/1.1 200 OK{separator}"
        f"Content-Type: {content_type}{separator}"
        f"MCP-Session-Id: session-123{separator}{separator}"
    ).encode()


def response_body(result: object, *, response_id: int = 2) -> bytes:
    return json.dumps({"jsonrpc": "2.0", "id": response_id, "result": result}).encode()


def tool(name: object) -> dict[str, object]:
    return {"name": name, "description": "fixture"}


def test_final_header_uses_final_response_block_and_last_repeated_value() -> None:
    raw = (
        b"\xef\xbb\xbfHTTP/1.1 100 Continue\r\nContent-Type: text/plain\r\n\r\n"
        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
        b"content-type: Application/JSON; charset=utf-8\r\nMcp-Session-Id: final-session\r\n\r\n"
    )

    assert parse_final_headers(raw) == {
        "content-type": "Application/JSON; charset=utf-8",
        "mcp-session-id": "final-session",
    }
    assert final_header(raw, "MCP-SESSION-ID") == "final-session"


def test_final_header_rejects_missing_status_or_field() -> None:
    with pytest.raises(McpResponseError, match="HTTP status"):
        parse_final_headers(b"Content-Type: application/json\n")
    with pytest.raises(McpResponseError, match="MCP-Session-Id"):
        final_header(response_headers(), "MCP-Session-Id-Other")


def test_json_response_accepts_bom_and_matches_numeric_id_strictly() -> None:
    body = b"\xef\xbb\xbf" + response_body({"protocolVersion": "2025-06-18"}, response_id=1)

    assert parse_protocol_version(response_headers(), body, response_id=1) == "2025-06-18"
    with pytest.raises(McpResponseError, match="requested JSON-RPC id"):
        parse_protocol_version(response_headers(), body, response_id="1")


@pytest.mark.parametrize("separator", ["\r\n", "\r"])
def test_sse_handles_line_endings_comments_empty_events_multiline_data_and_final_event(separator: str) -> None:
    lines = [
        ": keepalive",
        "",
        "event: message",
        'data: {"jsonrpc":"2.0","method":"notifications/progress"}',
        "",
        "data: {",
        'data: "jsonrpc": "2.0",',
        'data: "id": 2,',
        'data: "result": {"tools": [{"name": "ddgs-search_text"}]}',
        "data: }",
    ]
    body = ("\ufeff" + separator.join(lines)).encode()

    assert parse_tool_names(response_headers("text/event-stream", separator=separator), body, response_id=2) == [
        "ddgs-search_text"
    ]


def test_sse_rejects_empty_or_invalid_data_events() -> None:
    with pytest.raises(McpResponseError, match="does not contain a data event"):
        parse_response_messages(response_headers("text/event-stream"), b": comment\n\n\n")
    with pytest.raises(McpResponseError, match="does not contain a data event"):
        parse_response_messages(response_headers("text/event-stream"), b"data:\n\n")


def test_response_rejects_unsupported_content_type_and_invalid_utf8() -> None:
    with pytest.raises(McpResponseError, match="unsupported response Content-Type"):
        parse_response_messages(response_headers("text/plain"), b"{}")
    with pytest.raises(McpResponseError, match="not valid UTF-8"):
        parse_response_messages(response_headers(), b"\xff")


def test_select_response_rejects_missing_duplicate_invalid_and_error_messages() -> None:
    valid = {"jsonrpc": "2.0", "id": 2, "result": {}}
    with pytest.raises(McpResponseError, match="requested JSON-RPC id"):
        select_response([valid], response_id=3)
    with pytest.raises(McpResponseError, match="duplicate messages"):
        select_response([valid, valid], response_id=2)
    with pytest.raises(McpResponseError, match=r"jsonrpc 2\.0"):
        select_response([{"jsonrpc": "1.0", "id": 2, "result": {}}], response_id=2)
    with pytest.raises(McpResponseError, match="contains an error"):
        select_response([{"jsonrpc": "2.0", "id": 2, "error": {"message": "TOP_SECRET"}}], response_id=2)
    with pytest.raises(McpResponseError, match="does not contain a result"):
        select_response([{"jsonrpc": "2.0", "id": 2}], response_id=2)
    with pytest.raises(McpResponseError, match="result must be an object"):
        select_response([{"jsonrpc": "2.0", "id": 2, "result": []}], response_id=2)


def test_protocol_version_must_be_a_nonempty_string() -> None:
    with pytest.raises(McpResponseError, match="non-empty protocolVersion"):
        parse_protocol_version(response_headers(), response_body({"protocolVersion": ""}, response_id=1), response_id=1)
    with pytest.raises(McpResponseError, match="non-empty protocolVersion"):
        parse_protocol_version(response_headers(), response_body({"protocolVersion": 1}, response_id=1), response_id=1)


@pytest.mark.parametrize(
    ("result", "message"),
    [
        ({}, "tools array"),
        ({"tools": {}}, "tools array"),
        ({"tools": ["bad"]}, "non-object tool entry"),
        ({"tools": [tool(7)]}, "non-string or empty name"),
        ({"tools": [tool("")]}, "non-string or empty name"),
        ({"tools": [tool("same"), tool("same")]}, "duplicate tool names"),
        ({"tools": [], "nextCursor": "page-2"}, "response is paginated"),
        ({"tools": [], "nextCursor": 0}, "response is paginated"),
    ],
)
def test_tool_names_reject_malformed_or_incomplete_results(result: object, message: str) -> None:
    with pytest.raises(McpResponseError, match=message):
        parse_tool_names(response_headers(), response_body(result), response_id=2)


@pytest.mark.parametrize("next_cursor", [None, ""])
def test_tool_names_accepts_absent_or_empty_pagination_cursor(next_cursor: object) -> None:
    result = {"tools": [tool("one")], "nextCursor": next_cursor}
    assert parse_tool_names(response_headers(), response_body(result), response_id=2) == ["one"]


def test_expected_tool_modes_are_order_independent() -> None:
    actual = ["ddgs-search_text", "ddgs-search_news", "other-tool"]
    assert_expected_tools(actual, ["ddgs-search_news", "ddgs-search_text"], mode="contains")
    assert_expected_tools(actual, ["other-tool", "ddgs-search_news", "ddgs-search_text"], mode="exact")

    with pytest.raises(McpResponseError, match=r"missing=\['missing'\]"):
        assert_expected_tools(actual, ["missing"], mode="contains")
    with pytest.raises(McpResponseError, match=r"unexpected=\['other-tool'\]"):
        assert_expected_tools(actual, ["ddgs-search_news", "ddgs-search_text"], mode="exact")
    with pytest.raises(McpResponseError, match="expected tool names contain duplicates"):
        assert_expected_tools(actual, ["same", "same"], mode="contains")


def test_cli_extracts_session_and_protocol_and_asserts_tools(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    headers_path = tmp_path / "headers.txt"
    body_path = tmp_path / "body.json"
    headers_path.write_bytes(response_headers())
    body_path.write_bytes(response_body({"protocolVersion": "2025-06-18"}, response_id=1))

    assert main(["session-id", "--headers", str(headers_path)]) == 0
    assert capsys.readouterr().out == "session-123\n"
    assert (
        main([
            "protocol-version",
            "--headers",
            str(headers_path),
            "--body",
            str(body_path),
            "--response-id",
            "1",
        ])
        == 0
    )
    assert capsys.readouterr().out == "2025-06-18\n"

    body_path.write_bytes(response_body({"tools": [tool("one"), tool("two")]}))
    assert (
        main([
            "assert-tools",
            "--headers",
            str(headers_path),
            "--body",
            str(body_path),
            "--response-id",
            "2",
            "--mode",
            "exact",
            "--expect",
            "two",
            "--expect",
            "one",
        ])
        == 0
    )
    assert capsys.readouterr() == ("", "")


def test_cli_error_does_not_echo_response_body(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    headers_path = tmp_path / "headers.txt"
    body_path = tmp_path / "body.json"
    headers_path.write_bytes(response_headers())
    body_path.write_text(
        json.dumps({"jsonrpc": "2.0", "id": 2, "error": {"message": "TOP_SECRET"}}),
        encoding="utf-8",
    )

    assert (
        main([
            "assert-tools",
            "--headers",
            str(headers_path),
            "--body",
            str(body_path),
            "--response-id",
            "2",
        ])
        == 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "TOP_SECRET" not in captured.err
    assert "JSON-RPC response contains an error" in captured.err
