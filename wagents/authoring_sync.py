"""Sync repo-owned skills (skills/*/SKILL.md) into authoring mdx sources.

Produces docs/src/authoring/skills/{id}.mdx with:
- source_kind: custom
- projected frontmatter from SKILL.md
- body containing a generated marker comment pointing back to the source SKILL.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from wagents.skill_docs import collect_repo_skill_nodes
from wagents.skill_index import AUTHORING_SKILLS_DIR, CatalogAuthoringEntry, load_authoring_entries

if TYPE_CHECKING:
    from pathlib import Path

GENERATED_MARKER = (
    "{{/* GENERATED-AUTHORING: source=skills/{name}/SKILL.md; edit SKILL.md then re-run authoring sync */}}"
)


def _authoring_path_for(name: str, base: Path | None = None) -> Path:
    b = base or AUTHORING_SKILLS_DIR
    return b / f"{name}.mdx"


def _render_frontmatter(fm: dict) -> str:
    # Minimal, deterministic YAML frontmatter for mdx
    # We intentionally project a small set; keep order stable.
    lines: list[str] = ["---"]
    # name first
    name = fm.get("name")
    if name:
        lines.append(f'name: "{name}"')
    desc = fm.get("description")
    if desc is not None:
        # Escape simple quotes for YAML single-line safety; keep readable
        d = str(desc).replace('"', '\\"')
        lines.append(f'description: "{d}"')
    # Optional common fields if present in SKILL.md frontmatter
    for key in ("license", "model", "version", "author"):
        if key in fm and fm[key] not in (None, ""):
            val = str(fm[key]).replace('"', '\\"')
            lines.append(f'{key}: "{val}"')
    # Explicit authoring marker
    lines.append('source_kind: "custom"')
    lines.append("---")
    return "\n".join(lines)


def _render_body_with_marker(name: str, body: str) -> str:
    marker = GENERATED_MARKER.format(name=name)
    # Ensure a blank line after marker, then original body (trimmed)
    b = (body or "").strip()
    if b:
        return f"{marker}\n\n{b}\n"
    return f"{marker}\n"


def _is_generated_custom_authoring(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "GENERATED-AUTHORING: source=skills/" in text


def sync_custom_authoring_from_skills(
    *,
    authoring_dir: Path | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """For each skills/*/SKILL.md, write/update the corresponding authoring mdx.

    Returns list of written (or would-be-written) authoring mdx paths.
    """
    base = authoring_dir or AUTHORING_SKILLS_DIR
    base.mkdir(parents=True, exist_ok=True)

    nodes = list(collect_repo_skill_nodes())
    live_names = {node.id for node in nodes}
    written: list[Path] = []

    for stale in sorted(base.glob("*.mdx")):
        if stale.stem in live_names:
            continue
        if not _is_generated_custom_authoring(stale):
            continue
        if dry_run:
            written.append(stale)
            continue
        stale.unlink()
        written.append(stale)

    for node in nodes:
        name = node.id
        # Parse original frontmatter to project fields accurately
        # node.metadata is the frontmatter dict from SKILL.md
        fm = dict(node.metadata) if isinstance(node.metadata, dict) else {}
        fm.setdefault("name", name)
        if node.description:
            fm.setdefault("description", node.description)

        front = _render_frontmatter(fm)
        body = _render_body_with_marker(name, node.body or "")

        content = f"{front}\n\n{body}"

        target = _authoring_path_for(name, base=base)
        if dry_run:
            written.append(target)
            continue

        # Preserve marker on update by simply overwriting with canonical form
        # (marker text is stable; any prior hand edits to body are replaced per sync contract)
        target.write_text(content, encoding="utf-8")
        written.append(target)

    return written


def load_synced_authoring_entries(authoring_dir: Path | None = None) -> list[CatalogAuthoringEntry]:
    """Convenience: load current authoring entries after a sync (or independently)."""
    base = authoring_dir or AUTHORING_SKILLS_DIR
    return load_authoring_entries(base)
