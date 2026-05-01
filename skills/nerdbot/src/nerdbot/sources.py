"""Source-record helpers for Nerdbot acquisition lanes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from nerdbot.contracts import SOURCE_RECORD_FIELDS
from nerdbot.safety import normalize_vault_relative_path

SECRET_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "secrets.toml",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}
SECRET_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """Stable metadata for a captured source or pointer stub."""

    source_id: str
    original_location: str
    raw_path: str
    capture_method: str
    captured_at: str
    size_bytes: int | None = None
    checksum: str | None = None
    license_or_access_notes: str = "unknown"
    intended_wiki_coverage: str = "pending review"

    def to_dict(self) -> dict[str, object]:
        """Return the public source-record payload in contract order."""
        payload = asdict(self)
        return {field: payload[field] for field in SOURCE_RECORD_FIELDS}


@dataclass(frozen=True, slots=True)
class SourceIngestPlan:
    """Side-effect-free plan for a source capture or pointer stub."""

    record: SourceRecord
    raw_content: bytes | None
    pointer_reason: str | None = None

    @property
    def writes_pointer_stub(self) -> bool:
        """Return whether the plan writes a pointer stub instead of source bytes."""
        return self.raw_content is None

    def raw_text(self) -> str:
        """Return the text that should be written to raw/ for this plan."""
        return self.raw_bytes().decode("utf-8", errors="replace")

    def raw_bytes(self) -> bytes:
        """Return byte-preserving raw content or an encoded pointer stub."""
        if self.raw_content is not None:
            return self.raw_content
        return pointer_stub_text(self.record, self.pointer_reason or "source was not copied").encode("utf-8")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe ingest plan summary without embedding raw content."""
        return {
            "record": self.record.to_dict(),
            "raw_path": self.record.raw_path,
            "writes_pointer_stub": self.writes_pointer_stub,
            "pointer_reason": self.pointer_reason,
            "size_bytes": self.record.size_bytes,
            "checksum": self.record.checksum,
        }


def stable_source_id(original_location: str, *, prefix: str = "src") -> str:
    """Create a deterministic source ID from the original location."""
    digest = hashlib.sha256(original_location.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def checksum_bytes(content: bytes) -> str:
    """Return a SHA-256 checksum for captured content."""
    return hashlib.sha256(content).hexdigest()


def checksum_file(path: Path) -> str:
    """Return a SHA-256 checksum without loading the whole file into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def raw_source_path(source_id: str, original_location: str) -> str:
    """Choose a safe raw/sources path for a local capture or pointer stub."""
    suffix = PurePosixPath(original_location.split("?", 1)[0]).suffix.lower() or ".md"
    if suffix in {"/", "."}:
        suffix = ".md"
    return normalize_vault_relative_path(f"raw/sources/{source_id}{suffix}", allowed_roots={"raw"})


def build_source_record(
    original_location: str,
    *,
    capture_method: str,
    content: bytes | None = None,
    size_bytes: int | None = None,
    checksum: str | None = None,
    raw_path: str | None = None,
    captured_at: str | None = None,
    license_or_access_notes: str = "unknown",
    intended_wiki_coverage: str = "pending review",
) -> SourceRecord:
    """Build a source record without writing files."""
    source_id = stable_source_id(original_location)
    return SourceRecord(
        source_id=source_id,
        original_location=original_location,
        raw_path=normalize_vault_relative_path(raw_path, allowed_roots={"raw"})
        if raw_path
        else raw_source_path(source_id, original_location),
        capture_method=capture_method,
        captured_at=captured_at or datetime.now(UTC).replace(microsecond=0).isoformat(),
        size_bytes=len(content) if content is not None else size_bytes,
        checksum=checksum_bytes(content) if content is not None else checksum,
        license_or_access_notes=license_or_access_notes,
        intended_wiki_coverage=intended_wiki_coverage,
    )


def pointer_stub_text(record: SourceRecord, reason: str) -> str:
    """Render a pointer stub for sources that cannot be copied into raw/."""
    original_location = record.original_location.replace("\n", " ")
    capture_method = record.capture_method.replace("\n", " ")
    access_notes = record.license_or_access_notes.replace("\n", " ")
    pointer_reason = reason.replace("\n", " ")
    coverage = record.intended_wiki_coverage.replace("\n", " ")
    return (
        "---\n"
        f"source_id: {json.dumps(record.source_id, ensure_ascii=False)}\n"
        "kind: source-pointer\n"
        f"captured_at: {json.dumps(record.captured_at, ensure_ascii=False)}\n"
        "---\n\n"
        f"# Source pointer: {record.source_id}\n\n"
        f"- Original location: {original_location}\n"
        f"- Capture method: {capture_method}\n"
        f"- Size bytes: {record.size_bytes if record.size_bytes is not None else ''}\n"
        f"- Checksum: {record.checksum or ''}\n"
        f"- Access notes: {access_notes}\n"
        f"- Pointer reason: {pointer_reason}\n"
        f"- Intended wiki coverage: {coverage}\n"
    )


def plan_text_source(original_location: str, content: str | bytes, *, capture_method: str) -> SourceIngestPlan:
    """Plan ingestion for provided text/bytes without writing files."""
    raw_content = content.encode("utf-8") if isinstance(content, str) else content
    record = build_source_record(original_location, capture_method=capture_method, content=raw_content)
    return SourceIngestPlan(record=record, raw_content=raw_content)


def plan_local_file_source(
    original_path: Path,
    *,
    vault_root: Path,
    max_copy_bytes: int = 50_000_000,
    copy_outside_root: bool = False,
) -> SourceIngestPlan:
    """Plan local-file ingestion, using pointer stubs for oversized or unreadable files."""
    expanded = original_path.expanduser()
    resolved = expanded.resolve(strict=False)
    location = resolved.as_posix()
    vault_root_resolved = vault_root.resolve(strict=False)
    try:
        size_bytes = resolved.stat().st_size
    except OSError:
        record = build_source_record(location, capture_method="pointer-stub")
        return SourceIngestPlan(record=record, raw_content=None, pointer_reason="source is not readable")
    if expanded.is_symlink():
        record = build_source_record(location, capture_method="pointer-stub", size_bytes=size_bytes)
        return SourceIngestPlan(record=record, raw_content=None, pointer_reason="source is a symlink")
    if resolved.is_dir():
        entries = []
        for child in sorted(resolved.rglob("*"))[:200]:
            if child.is_file() and not child.is_symlink():
                entries.append(child.relative_to(resolved).as_posix())
        manifest = "# Directory source manifest\n\n" + "\n".join(f"- {entry}" for entry in entries) + "\n"
        record = build_source_record(
            location,
            capture_method="directory-manifest",
            content=manifest.encode("utf-8"),
            raw_path=f"raw/sources/{stable_source_id(location)}.md",
        )
        return SourceIngestPlan(record=record, raw_content=manifest.encode("utf-8"))
    checksum = checksum_file(resolved)
    name = resolved.name.lower()
    if name in SECRET_FILENAMES or resolved.suffix.lower() in SECRET_SUFFIXES:
        record = build_source_record(
            location,
            capture_method="pointer-stub",
            size_bytes=size_bytes,
            checksum=checksum,
            raw_path=f"raw/sources/{stable_source_id(location)}.md",
        )
        return SourceIngestPlan(record=record, raw_content=None, pointer_reason="source path looks secret-bearing")
    try:
        resolved.relative_to(vault_root_resolved)
        outside_vault_root = False
    except ValueError:
        outside_vault_root = True
    if outside_vault_root and not copy_outside_root:
        record = build_source_record(
            location,
            capture_method="pointer-stub",
            size_bytes=size_bytes,
            checksum=checksum,
            raw_path=f"raw/sources/{stable_source_id(location)}.md",
        )
        return SourceIngestPlan(
            record=record,
            raw_content=None,
            pointer_reason="source is outside vault root; pass --copy-outside-root to copy intentionally",
        )
    if size_bytes > max_copy_bytes:
        record = build_source_record(
            location,
            capture_method="pointer-stub",
            size_bytes=size_bytes,
            checksum=checksum,
            raw_path=f"raw/sources/{stable_source_id(location)}.md",
        )
        return SourceIngestPlan(record=record, raw_content=None, pointer_reason="source exceeds max_copy_bytes")
    try:
        content = resolved.read_bytes()
    except OSError:
        record = build_source_record(location, capture_method="pointer-stub")
        return SourceIngestPlan(record=record, raw_content=None, pointer_reason="source could not be read")
    rel_location = location if outside_vault_root else resolved.relative_to(vault_root_resolved).as_posix()
    record = build_source_record(rel_location, capture_method="local-file", content=content)
    return SourceIngestPlan(record=record, raw_content=content)


def render_source_map_row(
    record: SourceRecord,
    *,
    planned_wiki_target: str = "",
    canonical_material_touched: str = "no",
    provenance_status: str = "pending",
    status: str = "captured",
) -> str:
    """Render a source-map Markdown row matching the public architecture contract."""
    fields = [
        record.source_id,
        record.raw_path,
        record.capture_method,
        planned_wiki_target,
        canonical_material_touched,
        provenance_status,
        status,
    ]
    return "| " + " | ".join(field.replace("\n", " ").replace("|", "\\|") for field in fields) + " |"


def render_source_record_block(record: SourceRecord) -> str:
    """Render a Markdown details block for a source record."""
    lines = [f"### {record.source_id}", ""]
    for field, value in record.to_dict().items():
        lines.append(f"- {field}: {value if value is not None else ''}")
    return "\n".join(lines) + "\n"
