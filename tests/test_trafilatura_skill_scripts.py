"""Tests for skills/trafilatura script helpers."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "trafilatura"
SCRIPTS = SKILL_DIR / "scripts"


def _run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_doctor_json_shape() -> None:
    result = _run_script("doctor.py", "--format", "json")
    assert result.returncode in (0, 1)
    payload = json.loads(result.stdout)
    assert "ok" in payload
    assert "checks" in payload
    names = {check["name"] for check in payload["checks"]}
    assert "trafilatura-binary" in names
    assert "trafilatura-version" in names


def _import_script_module(name: str):
    import importlib.util

    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extract_url_builds_command() -> None:
    extract_url = _import_script_module("extract_url")

    command = extract_url._build_command(
        "https://example.org",
        output_format="json",
        with_metadata=True,
        precision=False,
        recall=True,
        archived=False,
        fast=False,
        no_comments=False,
        no_tables=True,
    )
    assert command[-2:] == ["--no-tables", "https://example.org"] or "--recall" in command
    assert "https://example.org" in command
    assert "--json" in command
    assert "--with-metadata" in command


def test_list_urls_parses_stdout() -> None:
    list_urls = _import_script_module("list_urls")

    stdout = "noise\nhttps://example.org/a\n  https://example.org/b  \nnot-a-url"
    urls = list_urls._parse_urls(stdout)
    assert urls == ["https://example.org/a", "https://example.org/b"]


def test_extract_url_envelope_ok() -> None:
    extract_url_mod = _import_script_module("extract_url")
    extract_url_mod._trafilatura_binary = lambda: "/usr/bin/trafilatura"  # type: ignore[method-assign]

    with patch.object(
        extract_url_mod.subprocess,
        "run",
        return_value=subprocess.CompletedProcess(
            args=["trafilatura"],
            returncode=0,
            stdout="# Title\n\nBody text",
            stderr="",
        ),
    ):
        report = extract_url_mod.extract_url("https://example.org", output_format="markdown")
    assert report["ok"] is True
    assert report["text_length"] > 0
    assert report["url"] == "https://example.org"