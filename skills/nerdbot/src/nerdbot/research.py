"""Autoresearcher policy helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from nerdbot.contracts import AUTORESEARCH_POLICIES


@dataclass(frozen=True, slots=True)
class ResearchJournalEntry:
    """A research finding that may later become a source or review item."""

    policy: str
    question: str
    candidate_sources: tuple[str, ...]
    decision: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.policy not in AUTORESEARCH_POLICIES:
            raise ValueError(f"Unknown autoresearch policy: {self.policy}")

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-safe journal entry."""
        return asdict(self)


def should_ingest_from_research(policy: str, *, approved: bool) -> bool:
    """Return True only when policy and approval permit source ingestion."""
    if policy not in AUTORESEARCH_POLICIES:
        raise ValueError(f"Unknown autoresearch policy: {policy}")
    return policy == "approved-ingest" and approved
