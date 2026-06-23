"""Keep portable and wagents hook event sets aligned."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "skill-creator" / "scripts"))

from asset_toolkit.common import KNOWN_HOOK_EVENTS as TOOLKIT_EVENTS

from wagents.parsing import KNOWN_HOOK_EVENTS as PARSING_EVENTS


def test_known_hook_events_match_between_parsing_and_toolkit() -> None:
    assert PARSING_EVENTS == TOOLKIT_EVENTS
