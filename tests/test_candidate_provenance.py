from __future__ import annotations

import base64
import hashlib
import json
from typing import TYPE_CHECKING

import pytest

from wagents.candidate_provenance import package_manager_provenance

if TYPE_CHECKING:
    from pathlib import Path


def test_npm_provenance_binds_lock_integrity_and_origin(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    lock = runtime / "npm/package-lock.json"
    lock.parent.mkdir(parents=True)
    package = {
        "version": "1.2.3",
        "resolved": "https://registry.npmjs.org/example/-/example-1.2.3.tgz",
        "integrity": "sha512-c2FmZQ==",
    }
    lock.write_text(
        json.dumps({"lockfileVersion": 3, "packages": {"node_modules/example": package}}),
        encoding="utf-8",
    )

    result = package_manager_provenance(
        {"package_manager": "npm", "package_name": "example", "version": "1.2.3"},
        runtime_state=runtime,
        uv_tools=tmp_path / "uv-tools",
    )

    assert result["kind"] == "npm-package-lock"
    assert result["integrity"] == package["integrity"]
    assert result["resolved"] == package["resolved"]
    assert len(result["origin_digest"]) == 64


def test_uv_tool_provenance_validates_distribution_record(tmp_path: Path) -> None:
    uv_tools = tmp_path / "uv-tools"
    tool = uv_tools / "example"
    site_packages = tool / "lib/python3.13/site-packages"
    package_file = site_packages / "example/__init__.py"
    package_file.parent.mkdir(parents=True)
    package_file.write_text("VALUE = 1\n", encoding="utf-8")
    dist_info = site_packages / "example-1.2.3.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text("Name: example\nVersion: 1.2.3\n", encoding="utf-8")
    (dist_info / "INSTALLER").write_text("uv\n", encoding="utf-8")
    digest = base64.urlsafe_b64encode(hashlib.sha256(package_file.read_bytes()).digest()).decode().rstrip("=")
    (dist_info / "RECORD").write_text(
        f"example/__init__.py,sha256={digest},{package_file.stat().st_size}\n"
        "example-1.2.3.dist-info/RECORD,,\n",
        encoding="utf-8",
    )
    (tool / "uv-receipt.toml").write_text(
        '[tool]\nrequirements = [{ name = "example", specifier = "==1.2.3" }]\n',
        encoding="utf-8",
    )

    result = package_manager_provenance(
        {"package_manager": "uv-tool", "package_name": "example", "version": "1.2.3"},
        runtime_state=tmp_path / "runtime",
        uv_tools=uv_tools,
    )

    assert result["kind"] == "uv-tool-receipt-and-record"
    assert result["integrity"].startswith("python-record-sha256:")
    assert result["validated_record_entry_count"] == 1


def test_uv_tool_provenance_rejects_modified_installed_file(tmp_path: Path) -> None:
    uv_tools = tmp_path / "uv-tools"
    tool = uv_tools / "example"
    site_packages = tool / "lib/python3.13/site-packages"
    package_file = site_packages / "example/__init__.py"
    package_file.parent.mkdir(parents=True)
    package_file.write_text("modified\n", encoding="utf-8")
    dist_info = site_packages / "example-1.2.3.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text("Name: example\nVersion: 1.2.3\n", encoding="utf-8")
    (dist_info / "INSTALLER").write_text("uv\n", encoding="utf-8")
    (dist_info / "RECORD").write_text(
        "example/__init__.py,sha256=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,9\n",
        encoding="utf-8",
    )
    (tool / "uv-receipt.toml").write_text(
        '[tool]\nrequirements = [{ name = "example", specifier = "==1.2.3" }]\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="RECORD digest mismatch"):
        package_manager_provenance(
            {"package_manager": "uv-tool", "package_name": "example", "version": "1.2.3"},
            runtime_state=tmp_path / "runtime",
            uv_tools=uv_tools,
        )
