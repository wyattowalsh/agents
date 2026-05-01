"""Evidence-ledger and review-queue contracts."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass

from nerdbot.contracts import REVIEW_STATUSES, SOURCE_FRESHNESS_CLASSES


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
