"""Shared Starlight frontmatter contract for harness catalog pages."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING, Any

from wagents.docs_lint import HAND_MAINTAINED_SENTINEL
from wagents.parsing import truncate_sentence
from wagents.site_model import resolve_trust_tier_for_node

if TYPE_CHECKING:
    from wagents.catalog import CatalogNode

PAGE_KIND_BY_NODE = {
    "skill": "skill",
    "agent": "agent",
    "mcp": "mcp",
}


def catalog_page_kind(node: CatalogNode) -> str:
    return PAGE_KIND_BY_NODE.get(node.kind, "asset")


def catalog_source_kind(node: CatalogNode) -> str:
    if node.kind == "skill":
        return node.source or "custom"
    if node.kind in ("agent", "mcp"):
        return "repo"
    return "registry"


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def _append_optional(lines: list[str], key: str, value: Any) -> None:
    if value is None or value == "" or value == []:
        return
    if isinstance(value, list):
        items = ", ".join(_yaml_scalar(item) for item in value)
        lines.append(f"{key}: [{items}]")
        return
    lines.append(f"{key}: {_yaml_scalar(value)}")


def render_catalog_frontmatter_lines(
    node: CatalogNode,
    *,
    description: str | None = None,
    composed: bool = False,
) -> list[str]:
    """Emit standardized catalog frontmatter lines (without --- delimiters)."""
    fm = node.metadata or {}
    desc = description or node.description or f"{catalog_page_kind(node)}: {node.id}"
    lines = [
        f"title: {_yaml_scalar(node.id)}",
        f"description: {_yaml_scalar(truncate_sentence(desc, 200))}",
        f"page_kind: {_yaml_scalar(catalog_page_kind(node))}",
        f"source_kind: {_yaml_scalar(catalog_source_kind(node))}",
        f"asset_id: {_yaml_scalar(node.id)}",
        f"composed: {_yaml_scalar(composed)}",
        "docs_density: standard",
    ]

    if node.kind == "skill":
        meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
        _append_optional(lines, "license", fm.get("license"))
        _append_optional(lines, "trust_tier", resolve_trust_tier_for_node(node))
        _append_optional(lines, "curated_status", fm.get("_curated_status"))
        _append_optional(lines, "install_command", fm.get("_skills_install_command") or fm.get("install_command"))
        if isinstance(meta, dict):
            _append_optional(lines, "metadata.author", meta.get("author"))
            _append_optional(lines, "metadata.version", meta.get("version"))
        targets = fm.get("target_agents") or fm.get("_skills_target_agents")
        if isinstance(targets, list) and targets:
            _append_optional(lines, "target_agents", targets)
        lines.append(f"research_slug: {_yaml_scalar(node.id)}")

    elif node.kind == "agent":
        _append_optional(lines, "tools", fm.get("tools"))
        _append_optional(lines, "permissionMode", fm.get("permissionMode"))
        if isinstance(fm.get("skills"), list):
            _append_optional(lines, "skills", fm.get("skills"))
        if isinstance(fm.get("mcpServers"), list):
            _append_optional(lines, "mcpServers", fm.get("mcpServers"))
        _append_optional(lines, "memory", fm.get("memory"))
        _append_optional(lines, "model", fm.get("model"))

    elif node.kind == "mcp":
        project_meta = fm.get("project")
        proj = project_meta if isinstance(project_meta, dict) else {}
        _append_optional(lines, "package", proj.get("name"))
        _append_optional(lines, "fastmcp", "true")

    return lines


def render_catalog_frontmatter(
    node: CatalogNode,
    *,
    description: str | None = None,
    composed: bool = False,
) -> str:
    """Render full YAML frontmatter block including --- delimiters."""
    inner = render_catalog_frontmatter_lines(node, description=description, composed=composed)
    return "---\n" + "\n".join(inner) + "\n---"


def render_composed_frontmatter_block(node: CatalogNode, *, wave_id: str) -> str:
    """Full frontmatter block with composed metadata and HAND-MAINTAINED sentinel."""
    lines = render_catalog_frontmatter_lines(node, composed=True)
    lines.append(f'composed_by: "{wave_id}"')
    lines.append(f'composed_at: "{date.today().isoformat()}"')
    return "---\n" + "\n".join(lines) + "\n---\n\n" + HAND_MAINTAINED_SENTINEL + "\n"


def enrich_rich_hand_frontmatter(
    page_text: str, node: CatalogNode, *, wave_id: str = "compose-rich-hand-wave-1"
) -> str:
    """Add composed frontmatter contract to rich hand-maintained pages without rewriting body."""
    if "composed: true" in page_text[:400]:
        return page_text
    block = render_composed_frontmatter_block(node, wave_id=wave_id)
    if page_text.startswith("---"):
        return re.sub(r"^---\n.*?\n---\n", block, page_text, count=1, flags=re.DOTALL)
    return block + page_text
