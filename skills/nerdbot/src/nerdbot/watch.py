"""Watch-mode event classification without filesystem mutation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import PurePosixPath

from nerdbot.evidence import ReviewItem
from nerdbot.safety import normalize_vault_relative_path

VOLATILE_OBSIDIAN_FILES = {"app.json", "graph.json", "workspace.json", "workspace-mobile.json", "workspace"}


@dataclass(frozen=True, slots=True)
class WatchEventDecision:
    """A non-mutating decision for a filesystem event."""

    path: str
    event_type: str
    risk: str
    stable: bool
    action: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-safe watch event decision."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class WatchCheckpoint:
    """Persistable summary of watch decisions."""

    created_at: str
    decisions: tuple[WatchEventDecision, ...]

    def to_json(self) -> str:
        """Serialize the checkpoint as deterministic JSON."""
        payload = {"created_at": self.created_at, "decisions": [decision.to_dict() for decision in self.decisions]}
        return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def classify_watch_event(path: str, event_type: str, *, stable: bool = True) -> WatchEventDecision:
    """Classify a watch event for review, quarantine, or ignore handling."""
    try:
        normalized_path = normalize_vault_relative_path(path)
    except ValueError as exc:
        return WatchEventDecision(path.replace("\\", "/"), event_type, "high", stable, "quarantine", str(exc))
    pure_path = PurePosixPath(normalized_path)
    parts = pure_path.parts
    if not stable:
        return WatchEventDecision(normalized_path, event_type, "low", False, "wait", "path is not stable yet")
    if len(parts) >= 2 and parts[0] == ".obsidian" and parts[1] in {"templates", "snippets"}:
        return WatchEventDecision(
            normalized_path,
            event_type,
            "medium",
            True,
            "queue-review",
            "Obsidian reusable content changed",
        )
    if len(parts) == 2 and parts[0] == ".obsidian" and pure_path.name in VOLATILE_OBSIDIAN_FILES:
        return WatchEventDecision(
            normalized_path,
            event_type,
            "low",
            True,
            "ignore",
            "volatile Obsidian workspace state",
        )
    if parts[:2] == ("indexes", "generated"):
        return WatchEventDecision(
            normalized_path,
            event_type,
            "low",
            True,
            "ignore",
            "rebuildable generated artifact",
        )
    if parts and parts[0] in {"raw", "wiki", "indexes", "schema", "config", "activity"}:
        return WatchEventDecision(
            normalized_path,
            event_type,
            "medium",
            True,
            "queue-review",
            "canonical KB surface changed",
        )
    return WatchEventDecision(normalized_path, event_type, "unknown", True, "classify", "outside default KB layers")


def classify_watch_events(events: Iterable[tuple[str, str]], *, stable_paths: set[str]) -> list[WatchEventDecision]:
    """Classify multiple watch events using a stable-path set."""
    return [
        classify_watch_event(path, event_type, stable=path.replace("\\", "/") in stable_paths)
        for path, event_type in events
    ]


def review_item_for_watch_event(decision: WatchEventDecision) -> ReviewItem:
    """Convert a queued/quarantined watch decision into a review item."""
    return ReviewItem(
        item_id=f"watch-{abs(hash((decision.path, decision.event_type, decision.action))) % 10_000_000}",
        mode="audit",
        target=decision.path,
        risk=decision.risk,
        proposed_action=f"{decision.action}: inspect watch event before applying automation",
        reason=decision.reason,
    )


def render_watch_checkpoint(decisions: Iterable[WatchEventDecision]) -> str:
    """Render watch decisions as a checkpoint JSON document."""
    checkpoint = WatchCheckpoint(
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        decisions=tuple(decisions),
    )
    return checkpoint.to_json()
