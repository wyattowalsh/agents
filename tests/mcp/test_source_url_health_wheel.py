"""Distribution contract for the source-url-health MCP wheel."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT = REPO_ROOT / "mcp" / "source-url-health"
_IMPORT_SCRIPT = """
import sys
import types

class _FastMCP:
    def __init__(self, *_args, **_kwargs):
        pass

    def tool(self, **_kwargs):
        return lambda function: function

fastmcp = types.ModuleType("fastmcp")
fastmcp.FastMCP = _FastMCP
sys.modules["fastmcp"] = fastmcp
sys.modules["httpx"] = types.ModuleType("httpx")

sentinel = types.ModuleType("ssrf")
sentinel.origin = "sentinel"
sys.modules["ssrf"] = sentinel

from mcp_source_url_health import server, ssrf

assert server.validate_url_for_probe is ssrf.validate_url_for_probe
assert sys.modules["ssrf"] is sentinel
assert sys.modules["ssrf"].origin == "sentinel"
"""


def test_source_url_health_wheel_is_self_contained(tmp_path: Path) -> None:
    subprocess.run(
        [
            "uv",
            "build",
            "--offline",
            "--project",
            str(PROJECT),
            "--wheel",
            "--out-dir",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    (wheel,) = tmp_path.glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())
        metadata_name = next(name for name in members if name.endswith(".dist-info/METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")

    assert "mcp_source_url_health/__init__.py" in members
    assert "mcp_source_url_health/server.py" in members
    assert "mcp_source_url_health/ssrf.py" in members
    assert "server.py" not in members
    assert "ssrf.py" not in members
    assert "Requires-Dist: wagents" not in metadata
    assert "Requires-Dist: fastmcp>=2" in metadata
    assert "Requires-Dist: httpx>=0.28.1" in metadata
    assert "Requires-Dist: idna>=3.11" in metadata

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (f"import sys; sys.path.insert(0, {str(wheel)!r}); exec({_IMPORT_SCRIPT!r})"),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
