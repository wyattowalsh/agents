"""Presence and coverage APIs for fleet skill projection assurance.

Wave 1a INV: distinguish Skills CLI universal store presence from per-harness
projection presence. Cursor global projection is ``~/.cursor/skills`` only —
repo ``.cursor/skills/**`` never counts as global coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from wagents.installed_inventory import (
    LOCAL_SKILL_ROOT_FALLBACKS,
    UNIVERSAL_SKILL_STORE_REL,
    is_cursor_home_projection_path,
    is_repo_cursor_skills_path,
    skill_dir_has_body,
    supported_agent_ids,
)
from wagents.platforms.base import HOME

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

PRESENCE_TIER_ABSENT = "absent"
PRESENCE_TIER_STORE_ONLY = "store_only"
PRESENCE_TIER_PROJECTION_ONLY = "projection_only"
PRESENCE_TIER_COVERED = "covered"

PRESENCE_TIERS = frozenset({
    PRESENCE_TIER_ABSENT,
    PRESENCE_TIER_STORE_ONLY,
    PRESENCE_TIER_PROJECTION_ONLY,
    PRESENCE_TIER_COVERED,
})

# Home-relative global projection roots. Cursor intentionally excludes the
# universal store — store presence is tracked separately via store_present.
HARNESS_GLOBAL_PROJECTION_RELS: dict[str, tuple[Path, ...]] = {
    "antigravity": (UNIVERSAL_SKILL_STORE_REL,),
    "claude-code": (Path(".claude") / "skills",),
    "codex": (Path(".codex") / "skills",),
    "crush": (Path(".config") / "crush" / "skills", UNIVERSAL_SKILL_STORE_REL),
    "cursor": (Path(".cursor") / "skills",),
    "gemini-cli": (Path(".gemini") / "skills",),
    "github-copilot": (Path(".copilot") / "skills",),
    "grok": (Path(".grok") / "skills",),
    "opencode": (Path(".config") / "opencode" / "skills",),
}


@dataclass(frozen=True)
class SkillPresence:
    """Store vs projection presence for one skill on one harness."""

    name: str
    agent_id: str
    store_present: bool
    projection_present: bool
    presence_tier: str
    store_path: str
    projection_path: str

    def public_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "agent_id": self.agent_id,
            "store_present": self.store_present,
            "projection_present": self.projection_present,
            "presence_tier": self.presence_tier,
            "store_path": self.store_path,
            "projection_path": self.projection_path,
        }


def presence_tier(*, store_present: bool, projection_present: bool) -> str:
    """Map boolean store/projection flags to a stable presence tier."""
    if store_present and projection_present:
        return PRESENCE_TIER_COVERED
    if store_present:
        return PRESENCE_TIER_STORE_ONLY
    if projection_present:
        return PRESENCE_TIER_PROJECTION_ONLY
    return PRESENCE_TIER_ABSENT


def default_store_root(*, home: Path | None = None) -> Path:
    """Return the Skills CLI universal skill store root."""
    return (home or HOME) / UNIVERSAL_SKILL_STORE_REL


def harness_projection_roots(agent_id: str, *, home: Path | None = None) -> tuple[Path, ...]:
    """Return home-absolute global projection roots for ``agent_id``."""
    home_dir = home or HOME
    rels = HARNESS_GLOBAL_PROJECTION_RELS.get(agent_id)
    if rels is None:
        fallback = LOCAL_SKILL_ROOT_FALLBACKS.get(agent_id, ())
        return tuple((home_dir / relative).expanduser() for relative, _label in fallback)
    return tuple((home_dir / relative).expanduser() for relative in rels)


def store_present(
    name: str,
    *,
    home: Path | None = None,
    store_root: Path | None = None,
) -> bool:
    """True when ``~/.agents/skills/<name>/SKILL.md`` (or override) is readable."""
    root = Path(store_root) if store_root is not None else default_store_root(home=home)
    return skill_dir_has_body(root / name)


def projection_present(
    name: str,
    agent_id: str,
    *,
    home: Path | None = None,
    repo_root: Path | None = None,
    projection_roots: Sequence[Path] | None = None,
) -> bool:
    """True when the skill is present under a harness global projection root.

    For Cursor, only ``~/.cursor/skills/<name>`` counts. Paths under a repo's
    ``.cursor/skills/**`` never count as global projection presence.
    """
    home_dir = home or HOME
    roots = (
        tuple(projection_roots) if projection_roots is not None else harness_projection_roots(agent_id, home=home_dir)
    )
    for root in roots:
        skill_dir = root / name
        if repo_root is not None and is_repo_cursor_skills_path(skill_dir, repo_root):
            continue
        if agent_id == "cursor" and not is_cursor_home_projection_path(skill_dir, home_dir):
            continue
        if skill_dir_has_body(skill_dir):
            return True
    return False


def evaluate_skill_presence(
    name: str,
    agent_id: str,
    *,
    home: Path | None = None,
    store_root: Path | None = None,
    repo_root: Path | None = None,
    projection_roots: Sequence[Path] | None = None,
) -> SkillPresence:
    """Evaluate store/projection presence and tier for one skill on one harness."""
    home_dir = home or HOME
    resolved_store_root = Path(store_root) if store_root is not None else default_store_root(home=home_dir)
    store_path = resolved_store_root / name
    roots = (
        tuple(projection_roots) if projection_roots is not None else harness_projection_roots(agent_id, home=home_dir)
    )
    projection_path = roots[0] / name if roots else home_dir / name
    for root in roots:
        candidate = root / name
        if repo_root is not None and is_repo_cursor_skills_path(candidate, repo_root):
            continue
        if agent_id == "cursor" and not is_cursor_home_projection_path(candidate, home_dir):
            continue
        if skill_dir_has_body(candidate):
            projection_path = candidate
            break

    store_flag = skill_dir_has_body(store_path)
    projection_flag = projection_present(
        name,
        agent_id,
        home=home_dir,
        repo_root=repo_root,
        projection_roots=roots,
    )
    return SkillPresence(
        name=name,
        agent_id=agent_id,
        store_present=store_flag,
        projection_present=projection_flag,
        presence_tier=presence_tier(store_present=store_flag, projection_present=projection_flag),
        store_path=str(store_path),
        projection_path=str(projection_path),
    )


def evaluate_skill_coverage(
    names: Iterable[str],
    *,
    agent_ids: Sequence[str] | None = None,
    home: Path | None = None,
    store_root: Path | None = None,
    repo_root: Path | None = None,
) -> tuple[SkillPresence, ...]:
    """Evaluate presence for each (name, agent) pair in stable name-then-agent order."""
    agents = tuple(agent_ids) if agent_ids is not None else supported_agent_ids()
    results: list[SkillPresence] = []
    for name in names:
        for agent_id in agents:
            results.append(
                evaluate_skill_presence(
                    name,
                    agent_id,
                    home=home,
                    store_root=store_root,
                    repo_root=repo_root,
                )
            )
    return tuple(results)


def missing_projections(
    names: Iterable[str],
    agent_id: str,
    *,
    home: Path | None = None,
    store_root: Path | None = None,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    """Return skill names that have store bodies but lack harness projections."""
    missing: list[str] = []
    for name in names:
        presence = evaluate_skill_presence(
            name,
            agent_id,
            home=home,
            store_root=store_root,
            repo_root=repo_root,
        )
        if presence.store_present and not presence.projection_present:
            missing.append(name)
    return tuple(missing)
