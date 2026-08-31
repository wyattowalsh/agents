"""Fail-closed provenance checks for the audited upstream distribution."""

from __future__ import annotations

import base64
import csv
import hashlib
import importlib.metadata
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from things_common import RecordVerification, SecurityViolation, verify_artifact, verify_record_tree
from things_common.integrity import _safe_read_artifact

from .contracts import CoreContractError, validate_frozen_contract

EXPECTED_PACKAGE = "mcp-server-things"
EXPECTED_VERSION = "1.9.0"
EXPECTED_WHEEL_SHA256 = "720f27aaabe76c3daddd2d92d4fd15bed0111b9eb390dca4b56284f950b9ce2c"
EXPECTED_SDIST_SHA256 = "99a6f630a0b80fe12a95ccf36a727b1dbc667ce60a6cc30ad1d391f4071e9bd0"
EXPECTED_RECORD_SHA256 = "e44727b7595a2b618118a060e5871e02065999152404055c68301613e49a1be7"
EXPECTED_RECORD_ENTRIES = 48
_DIST_INFO = "mcp_server_things-1.9.0.dist-info"
_INSTALLER_OWNED_RECORD_ENTRIES = frozenset({
    "../../../bin/mcp-server-things",
    "../../../bin/things-mcp",
    f"{_DIST_INFO}/INSTALLER",
    f"{_DIST_INFO}/REQUESTED",
})


class ProvenanceError(RuntimeError):
    """The upstream package cannot be proven to be the audited artifact."""


@dataclass(frozen=True, slots=True)
class DistributionEvidence:
    """Content-free proof returned after all requested checks pass."""

    package: str
    version: str
    wheel_verified: bool
    sdist_verified: bool
    record_sha256: str
    record_entries_verified: int
    frozen_tools_verified: int


def _artifact_paths(
    wheel_path: Path | None,
    sdist_path: Path | None,
) -> tuple[Path | None, Path | None]:
    if wheel_path is None and (value := os.environ.get("THINGS_CORE_WHEEL_PATH")):
        wheel_path = Path(value)
    if sdist_path is None and (value := os.environ.get("THINGS_CORE_SDIST_PATH")):
        sdist_path = Path(value)
    return wheel_path, sdist_path


def _development_override_allowed() -> bool:
    return (
        os.environ.get("THINGS_CORE_ALLOW_UNVERIFIED_ARTIFACT_CACHE") == "1"
        and os.environ.get("MCPHUB_TUNNEL_ENABLED", "false").casefold() == "false"
    )


def verify_distribution_artifacts(
    wheel_path: Path | None = None,
    sdist_path: Path | None = None,
    *,
    allow_tunnel_disabled_development: bool = False,
) -> tuple[bool, bool]:
    """Verify the accepted wheel and sdist immediately before package use.

    The sole exception is an explicit development override while the public
    tunnel is disabled. A missing path is never silently treated as evidence.
    """
    wheel_path, sdist_path = _artifact_paths(wheel_path, sdist_path)
    if wheel_path is None or sdist_path is None:
        if allow_tunnel_disabled_development and _development_override_allowed():
            return False, False
        raise ProvenanceError("things_core_distribution_artifacts_missing")
    try:
        verify_artifact(wheel_path, EXPECTED_WHEEL_SHA256, max_bytes=20_000_000)
        verify_artifact(sdist_path, EXPECTED_SDIST_SHA256, max_bytes=20_000_000)
    except (OSError, SecurityViolation) as exc:
        raise ProvenanceError("things_core_distribution_artifact_mismatch") from exc
    return True, True


def _distribution() -> importlib.metadata.Distribution:
    try:
        distribution = importlib.metadata.distribution(EXPECTED_PACKAGE)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ProvenanceError("things_core_distribution_missing") from exc
    if distribution.version != EXPECTED_VERSION:
        raise ProvenanceError("things_core_distribution_version_mismatch")
    return distribution


def _record_rows(payload: bytes) -> list[tuple[str, str, str]]:
    try:
        rows = [tuple(row) for row in csv.reader(payload.decode("utf-8", errors="strict").splitlines())]
    except UnicodeError as exc:
        raise SecurityViolation("Installed RECORD is not strict UTF-8.") from exc
    if any(len(row) != 3 for row in rows):
        raise SecurityViolation("Installed RECORD contains a malformed row.")
    typed_rows = [(row[0], row[1], row[2]) for row in rows]
    if len({row[0] for row in typed_rows}) != len(typed_rows):
        raise SecurityViolation("Installed RECORD contains duplicate paths.")
    return typed_rows


def _digest_hex(encoded: str) -> str:
    algorithm, separator, value = encoded.partition("=")
    if separator != "=" or algorithm != "sha256" or not value:
        raise SecurityViolation("Installed RECORD contains an unsupported digest.")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except ValueError as exc:
        raise SecurityViolation("Installed RECORD contains a malformed digest.") from exc
    if len(decoded) != hashlib.sha256().digest_size:
        raise SecurityViolation("Installed RECORD contains a malformed digest.")
    return decoded.hex()


def _verify_installer_projection(root: Path, record_relative: str) -> RecordVerification:
    """Verify uv/pip's RECORD projection against the exact wheel RECORD.

    Installers may reorder rows and add their two generated launchers plus
    INSTALLER/REQUESTED metadata. Every audited wheel row and installed byte
    must still match the exact canonical RECORD embedded from the accepted
    wheel; no other addition or substitution is accepted.
    """
    canonical_path = Path(__file__).with_name("upstream_record.csv")
    canonical_bytes, _ = _safe_read_artifact(canonical_path, max_bytes=2_000_000)
    canonical_digest = hashlib.sha256(canonical_bytes).hexdigest()
    if canonical_digest != EXPECTED_RECORD_SHA256:
        raise SecurityViolation("Frozen upstream RECORD digest mismatch.")
    canonical_rows = _record_rows(canonical_bytes)
    if len(canonical_rows) != EXPECTED_RECORD_ENTRIES + 1:
        raise SecurityViolation("Frozen upstream RECORD entry count mismatch.")

    installed_path = root.joinpath(*PurePosixPath(record_relative).parts)
    installed_bytes, _ = _safe_read_artifact(installed_path, max_bytes=2_000_000)
    installed_rows = _record_rows(installed_bytes)
    canonical_by_path = {row[0]: row[1:] for row in canonical_rows}
    installed_by_path = {row[0]: row[1:] for row in installed_rows}
    if set(canonical_by_path) - set(installed_by_path):
        raise SecurityViolation("Installed RECORD omits audited wheel entries.")
    extras = set(installed_by_path) - set(canonical_by_path)
    if not extras <= _INSTALLER_OWNED_RECORD_ENTRIES:
        raise SecurityViolation("Installed RECORD contains an unapproved projection entry.")
    for relative, expected_row in canonical_by_path.items():
        if installed_by_path[relative] != expected_row:
            raise SecurityViolation("Installed RECORD changed an audited wheel entry.")
        encoded_digest, encoded_size = expected_row
        if not encoded_digest:
            if relative != record_relative or encoded_size:
                raise SecurityViolation("Only RECORD itself may omit a digest and size.")
            continue
        parts = PurePosixPath(relative)
        if parts.is_absolute() or ".." in parts.parts:
            raise SecurityViolation("Frozen upstream RECORD entry escapes the distribution root.")
        artifact = verify_artifact(root.joinpath(*parts.parts), _digest_hex(encoded_digest))
        if artifact.size != int(encoded_size):
            raise SecurityViolation("Installed artifact size differs from the audited wheel.")
    return RecordVerification(canonical_digest, EXPECTED_RECORD_ENTRIES, len(canonical_rows))


def verify_installed_distribution(
    *,
    wheel_path: Path | None = None,
    sdist_path: Path | None = None,
    allow_tunnel_disabled_development: bool = False,
) -> DistributionEvidence:
    """Verify artifacts, every installed RECORD entry, and the frozen contract.

    This uses importlib metadata only; it does not import or execute
    ``things_mcp``.
    """
    try:
        contracts = validate_frozen_contract()
    except CoreContractError as exc:
        raise ProvenanceError("things_core_frozen_contract_mismatch") from exc
    wheel_verified, sdist_verified = verify_distribution_artifacts(
        wheel_path,
        sdist_path,
        allow_tunnel_disabled_development=allow_tunnel_disabled_development,
    )
    distribution = _distribution()
    root = Path(str(distribution.locate_file("")))
    record_relative = f"{_DIST_INFO}/RECORD"
    try:
        try:
            record = verify_record_tree(
                root,
                record_relative,
                EXPECTED_RECORD_SHA256,
                expected_entries=EXPECTED_RECORD_ENTRIES,
            )
        except SecurityViolation:
            record = _verify_installer_projection(root, record_relative)
    except (OSError, SecurityViolation, UnicodeError, ValueError) as exc:
        raise ProvenanceError("things_core_installed_record_mismatch") from exc
    return DistributionEvidence(
        package=EXPECTED_PACKAGE,
        version=EXPECTED_VERSION,
        wheel_verified=wheel_verified,
        sdist_verified=sdist_verified,
        record_sha256=record.record_sha256,
        record_entries_verified=record.entries_verified,
        frozen_tools_verified=len(contracts),
    )


def provenance_doctor() -> dict[str, Any]:
    """Return a redacted diagnostic with no path, token, or environment value."""
    try:
        evidence = verify_installed_distribution(allow_tunnel_disabled_development=True)
    except ProvenanceError as exc:
        return {"status": "blocked", "code": str(exc), "package": EXPECTED_PACKAGE, "version": EXPECTED_VERSION}
    return {
        "status": "ready",
        "code": "things_core_provenance_verified",
        "package": evidence.package,
        "version": evidence.version,
        "wheelVerified": evidence.wheel_verified,
        "sdistVerified": evidence.sdist_verified,
        "recordVerified": evidence.record_entries_verified == EXPECTED_RECORD_ENTRIES,
        "toolsVerified": evidence.frozen_tools_verified,
    }
