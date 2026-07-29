"""Verify local candidate package provenance from package-manager receipts."""

from __future__ import annotations

import base64
import csv
import hashlib
import json
import re
import tomllib
from email.parser import Parser
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _normalized_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _npm_provenance(seed: dict[str, Any], runtime_state: Path) -> dict[str, Any]:
    package_name = str(seed.get("package_name") or "")
    version = str(seed.get("version") or "")
    receipt_path = runtime_state / "npm/package-lock.json"
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    package_record = payload.get("packages", {}).get(f"node_modules/{package_name}")
    if not isinstance(package_record, dict):
        raise ValueError(f"npm lock receipt omitted {package_name}")
    if str(package_record.get("version") or "") != version:
        raise ValueError(f"npm lock receipt version drifted for {package_name}")
    integrity = str(package_record.get("integrity") or "")
    resolved = str(package_record.get("resolved") or "")
    if not integrity.startswith("sha512-"):
        raise ValueError(f"npm lock receipt omitted sha512 integrity for {package_name}")
    if not resolved.startswith("https://registry.npmjs.org/"):
        raise ValueError(f"npm lock receipt has an untrusted package origin for {package_name}")
    record = {
        "kind": "npm-package-lock",
        "package_name": package_name,
        "version": version,
        "integrity": integrity,
        "resolved": resolved,
        "lockfile_version": payload.get("lockfileVersion"),
        "receipt_path": str(receipt_path.resolve()),
        "package_record_sha256": _canonical_digest(package_record),
    }
    record["origin_digest"] = _canonical_digest(record)
    return record


def _distribution_record(tool_root: Path, package_name: str, version: str) -> tuple[Path, Path, Path]:
    candidates: list[tuple[Path, Path, Path]] = []
    for metadata_path in tool_root.glob("lib/python*/site-packages/*.dist-info/METADATA"):
        metadata = Parser().parsestr(metadata_path.read_text(encoding="utf-8"))
        if (
            _normalized_distribution_name(str(metadata.get("Name") or ""))
            != _normalized_distribution_name(package_name)
            or str(metadata.get("Version") or "") != version
        ):
            continue
        dist_info = metadata_path.parent
        candidates.append((dist_info / "RECORD", dist_info / "INSTALLER", dist_info))
    if len(candidates) != 1:
        raise ValueError(
            f"expected one installed distribution record for {package_name}=={version}, found {len(candidates)}"
        )
    record_path, installer_path, dist_info = candidates[0]
    if not record_path.is_file() or not installer_path.is_file():
        raise ValueError(f"installed distribution metadata is incomplete for {package_name}")
    return record_path, installer_path, dist_info


def _validate_python_record(tool_root: Path, record_path: Path) -> int:
    site_packages = record_path.parent.parent
    validated = 0
    with record_path.open(newline="", encoding="utf-8") as handle:
        for relative, encoded_hash, _size in csv.reader(handle):
            if not encoded_hash:
                continue
            algorithm, separator, expected = encoded_hash.partition("=")
            if separator != "=" or algorithm != "sha256":
                raise ValueError(f"unsupported Python RECORD digest: {encoded_hash!r}")
            target = (site_packages / relative).resolve(strict=True)
            if not target.is_relative_to(tool_root.resolve()):
                raise ValueError(f"Python RECORD path escapes the managed tool root: {relative}")
            actual = base64.urlsafe_b64encode(hashlib.sha256(target.read_bytes()).digest()).decode().rstrip("=")
            if actual != expected:
                raise ValueError(f"Python RECORD digest mismatch: {relative}")
            validated += 1
    if validated == 0:
        raise ValueError("Python RECORD did not contain any verifiable sha256 entries")
    return validated


def _uv_tool_provenance(seed: dict[str, Any], uv_tools: Path) -> dict[str, Any]:
    package_name = str(seed.get("package_name") or "").split("[", 1)[0]
    version = str(seed.get("version") or "")
    tool_root = (uv_tools / package_name).resolve(strict=True)
    receipt_path = tool_root / "uv-receipt.toml"
    receipt = tomllib.loads(receipt_path.read_text(encoding="utf-8"))
    requirements = receipt.get("tool", {}).get("requirements", [])
    matching = [
        item
        for item in requirements
        if isinstance(item, dict)
        and _normalized_distribution_name(str(item.get("name") or ""))
        == _normalized_distribution_name(package_name)
        and str(item.get("specifier") or "") == f"=={version}"
    ]
    if len(matching) != 1:
        raise ValueError(f"uv tool receipt did not pin {package_name}=={version}")
    record_path, installer_path, dist_info = _distribution_record(tool_root, package_name, version)
    installer = installer_path.read_text(encoding="utf-8").strip()
    if installer != "uv":
        raise ValueError(f"unexpected Python package installer for {package_name}: {installer!r}")
    validated_entries = _validate_python_record(tool_root, record_path)
    record = {
        "kind": "uv-tool-receipt-and-record",
        "package_name": package_name,
        "version": version,
        "integrity": f"python-record-sha256:{_sha256(record_path)}",
        "receipt_path": str(receipt_path),
        "receipt_sha256": _sha256(receipt_path),
        "distribution_record_path": str(record_path),
        "distribution_record_sha256": _sha256(record_path),
        "distribution_metadata_path": str(dist_info),
        "installer": installer,
        "validated_record_entry_count": validated_entries,
    }
    record["origin_digest"] = _canonical_digest(record)
    return record


def package_manager_provenance(
    seed: dict[str, Any],
    *,
    runtime_state: Path,
    uv_tools: Path,
) -> dict[str, Any]:
    """Return independently recomputable provenance for a managed package install."""
    manager = str(seed.get("package_manager") or "")
    if manager == "npm":
        return _npm_provenance(seed, runtime_state)
    if manager in {"uv-tool", "uvx"}:
        return _uv_tool_provenance(seed, uv_tools)
    raise ValueError(f"package-manager provenance is unsupported for {manager!r}")
