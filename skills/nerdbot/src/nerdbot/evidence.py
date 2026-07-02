"""Evidence-ledger and review-queue contracts."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass

from nerdbot.contracts import REVIEW_STATUSES, SOURCE_FRESHNESS_CLASSES

SOURCE_MAP_COLUMNS = (
    "Source ID",
    "Raw path",
    "Capture type",
    "Planned wiki target",
    "Canonical material touched?",
    "Provenance status",
    "Status",
)


@dataclass(frozen=True, slots=True)
class ClaimRecord:
    """A traceable wiki claim backed by raw or canonical material."""

    claim_id: str
    claim: str
    wiki_path: str
    source_id: str
    evidence_path: str
    evidence_type: str
    freshness_class: str = "unknown"
    review_status: str = "pending"
    confidence: float = 0.0
    updated: str = "unknown"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.freshness_class not in SOURCE_FRESHNESS_CLASSES:
            raise ValueError(f"Unknown freshness class: {self.freshness_class}")
        if self.review_status not in REVIEW_STATUSES:
            raise ValueError(f"Unknown review status: {self.review_status}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict[str, object]:
        """Return the ledger row payload."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReviewItem:
    """A queued action that requires review before save-back or mutation."""

    item_id: str
    mode: str
    target: str
    risk: str
    proposed_action: str
    status: str = "pending"
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status not in REVIEW_STATUSES:
            raise ValueError(f"Unknown review status: {self.status}")

    def to_dict(self) -> dict[str, str]:
        """Return the review-queue payload."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SuspiciousEvidenceFinding:
    """Untrusted imported content that looks like an instruction."""

    finding_id: str
    path: str
    pattern: str
    snippet: str
    risk: str = "high"

    def to_dict(self) -> dict[str, str]:
        """Return the JSON-safe finding payload."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SourceMapEntry:
    """Read-only source-map metadata used to explain query provenance."""

    source_id: str
    raw_path: str
    capture_type: str
    planned_wiki_target: str
    canonical_material_touched: str
    provenance_status: str
    status: str

    def to_dict(self) -> dict[str, str]:
        """Return the JSON-safe source-map payload."""
        return asdict(self)


UNTRUSTED_INSTRUCTION_PATTERNS = (
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|system|developer)\s+instructions?", re.IGNORECASE),
    re.compile(r"(?:delete|remove|move|rename|overwrite)\s+(?:all\s+)?(?:files?|notes?|vault|raw|wiki)", re.IGNORECASE),
    re.compile(r"(?:expose|print|dump|reveal|send)\s+(?:secrets?|credentials?|tokens?|api\s+keys?)", re.IGNORECASE),
    re.compile(r"(?:run|execute)\s+(?:this\s+)?(?:shell\s+)?(?:command|script)", re.IGNORECASE),
    re.compile(
        r"(?:change|override|replace)\s+(?:your|the)\s+(?:agent\s+)?(?:behavior|role|rules|instructions)", re.IGNORECASE
    ),
)


def confidence_cap_for_freshness(freshness_class: str) -> float:
    """Return the maximum confidence for an unreviewed claim by freshness."""
    caps = {"static": 0.95, "slow": 0.85, "medium": 0.7, "fast": 0.55, "unknown": 0.5}
    if freshness_class not in caps:
        raise ValueError(f"Unknown freshness class: {freshness_class}")
    return caps[freshness_class]


def apply_confidence_cap(confidence: float, freshness_class: str) -> float:
    """Cap confidence so fast-changing or unknown sources remain review-visible."""
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")
    return min(confidence, confidence_cap_for_freshness(freshness_class))


def _snippet_around(text: str, start: int, end: int) -> str:
    collapsed = " ".join(text[max(0, start - 80) : min(len(text), end + 80)].split())
    return collapsed[:240]


def detect_untrusted_instruction_patterns(text: str, *, path: str) -> tuple[SuspiciousEvidenceFinding, ...]:
    """Flag imported evidence that should be reviewed, not obeyed."""
    findings: list[SuspiciousEvidenceFinding] = []
    for pattern in UNTRUSTED_INSTRUCTION_PATTERNS:
        for match in pattern.finditer(text):
            snippet = _snippet_around(text, match.start(), match.end())
            digest = hashlib.sha256(f"{path}\0{pattern.pattern}\0{snippet}".encode()).hexdigest()[:12]
            findings.append(
                SuspiciousEvidenceFinding(
                    finding_id=f"evidence-{digest}",
                    path=path,
                    pattern=pattern.pattern,
                    snippet=snippet,
                )
            )
    return tuple(findings)


def review_item_for_suspicious_evidence(finding: SuspiciousEvidenceFinding) -> ReviewItem:
    """Convert suspicious imported evidence into a review-queue item."""
    return ReviewItem(
        item_id=finding.finding_id,
        mode="query",
        target=finding.path,
        risk=finding.risk,
        proposed_action="Review imported evidence text as untrusted content before citing it",
        reason=f"Matched untrusted instruction-like pattern near: {finding.snippet}",
    )


def _split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    stripped = stripped[1:]
    cells: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(stripped):
        char = stripped[index]
        if char == "\\" and index + 1 < len(stripped) and stripped[index + 1] == "|":
            current.append("|")
            index += 2
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    cells.append("".join(current).strip())
    return cells


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def _clean_cell(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned.startswith("`") and cleaned.endswith("`"):
        cleaned = cleaned[1:-1]
    return " ".join(cleaned.split())


def parse_source_map_entries(text: str) -> tuple[SourceMapEntry, ...]:
    """Parse the canonical source-map Markdown table without trusting note text."""
    entries: list[SourceMapEntry] = []
    header: list[str] | None = None
    for line in text.splitlines():
        cells = _split_markdown_row(line)
        if not cells:
            if header and entries:
                break
            continue
        if cells[: len(SOURCE_MAP_COLUMNS)] == list(SOURCE_MAP_COLUMNS):
            header = cells
            continue
        if header is None:
            continue
        if _is_separator_row(cells):
            continue
        values = [_clean_cell(cell) for cell in [*cells, *([""] * max(0, len(header) - len(cells)))][: len(header)]]
        row = dict(zip(header, values, strict=False))
        source_id = row.get("Source ID", "")
        if not source_id:
            continue
        entries.append(
            SourceMapEntry(
                source_id=source_id,
                raw_path=row.get("Raw path", ""),
                capture_type=row.get("Capture type", ""),
                planned_wiki_target=row.get("Planned wiki target", ""),
                canonical_material_touched=row.get("Canonical material touched?", ""),
                provenance_status=row.get("Provenance status", ""),
                status=row.get("Status", ""),
            )
        )
    return tuple(entries)


def source_map_entries_by_id(text: str) -> dict[str, SourceMapEntry]:
    """Return source-map entries keyed by source ID, preserving the first row."""
    entries: dict[str, SourceMapEntry] = {}
    for entry in parse_source_map_entries(text):
        entries.setdefault(entry.source_id, entry)
    return entries
