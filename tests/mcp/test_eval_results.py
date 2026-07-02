"""Tests for mcp/eval-results/server.py.

`subprocess.run` is mocked; no real `wagents eval ...` subprocess is spawned.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("eval-results")


@dataclass
class _FakeCompletedProcess:
    stdout: str
    stderr: str = ""
    returncode: int = 0


def _patch_subprocess(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any], returncode: int = 0) -> list[list[str]]:
    calls: list[list[str]] = []

    def _fake_run(argv: list[str], **_kwargs: Any) -> _FakeCompletedProcess:
        calls.append(argv)
        return _FakeCompletedProcess(json.dumps(payload), returncode=returncode)

    monkeypatch.setattr(server.subprocess, "run", _fake_run)
    return calls


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {"eval_list", "eval_coverage", "eval_adequacy", "eval_validate"} <= names


def test_eval_list_parses_json_and_tags_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_subprocess(monkeypatch, {"count": 3, "eval_count": 10, "skills": []})

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("eval_list", {})
            return result.data

    data = run_async(_call())
    assert data["count"] == 3
    assert data["_exit_code"] == 0
    assert calls[0] == ["uv", "run", "wagents", "eval", "list", "--format", "json"]


def test_eval_coverage_invokes_expected_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_subprocess(monkeypatch, {"count": 1, "skills": []})

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("eval_coverage", {})
            return result.data

    run_async(_call())
    assert calls[0] == ["uv", "run", "wagents", "eval", "coverage", "--format", "json"]


def test_eval_adequacy_passes_skill_and_strict_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_subprocess(monkeypatch, {"skill": "review", "adequacy": "pass"})

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("eval_adequacy", {"skill": "review", "strict": True})
            return result.data

    run_async(_call())
    assert calls[0] == ["uv", "run", "wagents", "eval", "adequacy", "--skill", "review", "--strict", "--format", "json"]


def test_eval_adequacy_omits_flags_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_subprocess(monkeypatch, {"count": 1})

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("eval_adequacy", {})
            return result.data

    run_async(_call())
    assert calls[0] == ["uv", "run", "wagents", "eval", "adequacy", "--format", "json"]


def test_eval_validate_reports_nonzero_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_subprocess(monkeypatch, {"ok": False, "error_count": 2, "errors": ["a", "b"]}, returncode=1)

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("eval_validate", {})
            return result.data

    data = run_async(_call())
    assert data["ok"] is False
    assert data["_exit_code"] == 1


def test_invalid_json_output_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_run(argv: list[str], **_kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess("not json", stderr="boom", returncode=1)

    monkeypatch.setattr(server.subprocess, "run", _fake_run)

    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("eval_list", {})

    with pytest.raises(ToolError):
        run_async(_call())


def test_subprocess_failure_to_launch_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_run(argv: list[str], **_kwargs: Any) -> _FakeCompletedProcess:
        raise subprocess.SubprocessError("could not start")

    monkeypatch.setattr(server.subprocess, "run", _fake_run)

    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("eval_list", {})

    with pytest.raises(ToolError):
        run_async(_call())
