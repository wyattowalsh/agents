"""Read-only graph extraction from markdown and Obsidian links."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from itertools import groupby
from pathlib import Path, PurePosixPath

from nerdbot.contracts import GRAPH_EDGE_FIELDS

MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
OBSIDIAN_REFERENCE_PATTERN = re.compile(r"(?P<embed>!)?\[\[([^\[\]\n]+)\]\]")
FRONTMATTER_PATTERN = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
SOURCE_ID_PATTERN = re.compile(r"\b(?P<id>src-[A-Za-z0-9_-]+)\b")


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """Directed graph edge with source evidence."""

    source: str
    target: str
    edge_type: str
    evidence_path: str
    confidence: float = 1.0

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-safe graph edge."""
        payload = asdict(self)
        return {field: payload[field] for field in GRAPH_EDGE_FIELDS}


@dataclass(frozen=True, slots=True)
class ObsidianReference:
    """Parsed Obsidian link/embed target."""

    target: str
    heading: str | None = None
    block_ref: str | None = None
    alias: str | None = None
    embedded: bool = False


@dataclass(frozen=True, slots=True)
class GraphBuildResult:
    """Derived graph output and analytics."""

    edges: tuple[GraphEdge, ...]
    metrics: dict[str, object]
    broken_targets: tuple[str, ...]
    orphan_pages: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-safe graph build result."""
        return {
            "edges": [edge.to_dict() for edge in self.edges],
            "metrics": self.metrics,
            "broken_targets": list(self.broken_targets),
            "orphan_pages": list(self.orphan_pages),
        }


def split_obsidian_reference(value: str) -> str:
    """Remove alias, width, heading, and block-display suffixes from wikilinks."""
    target, *_rest = value.split("|", 1)
    target, *_rest = target.split("#", 1)
    target, *_rest = target.split("^", 1)
    return target.strip()


def markdown_code(value: object) -> str:
    """Render untrusted graph values as Markdown code spans."""
    text = value if isinstance(value, str) else repr(value)
    longest = max((len("".join(group)) for char, group in groupby(text) if char == "`"), default=0)
    fence = "`" * (longest + 1)
    return f"{fence}{text}{fence}"


def normalize_relative_target(source_path: str, target: str) -> str:
    """Normalize a relative markdown link target against the source document."""
    path_part, *suffix = target.split("#", 1)
    if not path_part or path_part.startswith("/"):
        return target
    parts: list[str] = []
    for part in (PurePosixPath(source_path).parent / path_part).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    normalized = PurePosixPath(*parts).as_posix() if parts else path_part
    return normalized + (f"#{suffix[0]}" if suffix else "")


def parse_obsidian_reference(value: str, *, embedded: bool = False) -> ObsidianReference:
    """Parse Obsidian link syntax while preserving alias, heading, and block refs."""
    if "|" in value:
        target_part, alias = value.split("|", 1)
    else:
        target_part = value
        alias = None
    block_ref = None
    if "^" in target_part:
        target_part, block_ref = target_part.split("^", 1)
    heading = None
    if "#" in target_part:
        target_part, heading = target_part.split("#", 1)
    return ObsidianReference(
        target=target_part.strip(),
        heading=heading.strip() if heading else None,
        block_ref=block_ref.strip() if block_ref else None,
        alias=alias.strip() if alias else None,
        embedded=embedded,
    )


def extract_edges(source_path: str, text: str) -> list[GraphEdge]:
    """Extract baseline graph edges from one markdown document.

    This keeps the original public helper stable. Rich graph builds use
    ``extract_detailed_edges`` to add alias, citation, heading, and block-ref edges.
    """
    edges: list[GraphEdge] = []
    for match in OBSIDIAN_REFERENCE_PATTERN.finditer(text):
        reference = parse_obsidian_reference(match.group(2), embedded=bool(match.group("embed")))
        if reference.target:
            edges.append(
                GraphEdge(
                    source=source_path,
                    target=reference.target,
                    edge_type="embeds" if reference.embedded else "links_to",
                    evidence_path=source_path,
                )
            )
    for target in MARKDOWN_LINK_PATTERN.findall(text):
        cleaned = target.strip()
        if cleaned and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", cleaned):
            edges.append(
                GraphEdge(
                    source=source_path,
                    target=normalize_relative_target(source_path, cleaned),
                    edge_type="links_to",
                    evidence_path=source_path,
                )
            )
    return edges


def extract_detailed_edges(source_path: str, text: str) -> list[GraphEdge]:
    """Extract baseline plus analytics-oriented graph edges."""
    edges = extract_edges(source_path, text)
    for match in OBSIDIAN_REFERENCE_PATTERN.finditer(text):
        reference = parse_obsidian_reference(match.group(2), embedded=bool(match.group("embed")))
        if reference.alias:
            edges.append(
                GraphEdge(
                    source=source_path,
                    target=reference.alias,
                    edge_type="aliases",
                    evidence_path=source_path,
                    confidence=0.8,
                )
            )
        if reference.heading or reference.block_ref:
            block_suffix = f"^{reference.block_ref}" if reference.block_ref else ""
            target = f"{reference.target}#{reference.heading or ''}{block_suffix}"
            edges.append(
                GraphEdge(
                    source=source_path,
                    target=target,
                    edge_type="mentions",
                    evidence_path=source_path,
                    confidence=0.75,
                )
            )
    edges.extend(extract_alias_edges(source_path, text))
    edges.extend(extract_citation_edges(source_path, text))
    return edges


def extract_alias_edges(source_path: str, text: str) -> list[GraphEdge]:
    """Extract simple frontmatter alias edges."""
    aliases = extract_frontmatter_aliases(text)
    if not aliases:
        return []
    return [
        GraphEdge(source=source_path, target=alias, edge_type="aliases", evidence_path=source_path, confidence=0.85)
        for alias in aliases
        if alias
    ]


def extract_frontmatter_aliases(text: str) -> list[str]:
    """Extract common Obsidian alias frontmatter forms."""
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return []
    aliases: list[str] = []
    in_alias_list = False
    for line in match.group("body").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("alias:"):
            value = stripped.split(":", 1)[1].strip().strip("\"'")
            if value:
                aliases.append(value)
            in_alias_list = False
            continue
        if stripped.startswith("aliases:"):
            value = stripped.split(":", 1)[1].strip()
            if value.startswith("[") and value.endswith("]"):
                aliases.extend(alias.strip().strip("\"'") for alias in value.strip("[]").split(",") if alias.strip())
            elif value:
                aliases.append(value.strip("\"'"))
            in_alias_list = not value
            continue
        if in_alias_list and stripped.startswith("-"):
            value = stripped.removeprefix("-").strip().strip("\"'")
            if value:
                aliases.append(value)
            continue
        in_alias_list = False
    return aliases


def extract_citation_edges(source_path: str, text: str) -> list[GraphEdge]:
    """Extract source/provenance citation edges from source IDs."""
    return [
        GraphEdge(
            source=source_path, target=match.group("id"), edge_type="cites", evidence_path=source_path, confidence=0.9
        )
        for match in SOURCE_ID_PATTERN.finditer(text)
    ]


def _iter_markdown_pages(root: Path, *, include_unlayered: bool) -> list[Path]:
    layer_roots = ("wiki", "indexes") if not include_unlayered else (".",)
    paths: list[Path] = []
    for rel_root in layer_roots:
        base = root / rel_root
        if not base.exists() or base.is_symlink():
            continue
        for path in sorted(base.rglob("*.md")):
            rel = path.relative_to(root).as_posix()
            if path.is_symlink() or rel.startswith("indexes/generated/"):
                continue
            paths.append(path)
    return paths


def _canonical_targets(paths: list[Path], root: Path) -> set[str]:
    targets: set[str] = set()
    for path in paths:
        rel = path.relative_to(root).as_posix()
        stem = PurePosixPath(rel).with_suffix("").as_posix()
        targets.update({rel, stem, PurePosixPath(stem).name})
    return targets


def build_graph(root: Path, *, include_unlayered: bool = False) -> GraphBuildResult:
    """Build derived graph edges and basic analytics from markdown pages."""
    paths = _iter_markdown_pages(root, include_unlayered=include_unlayered)
    edges: list[GraphEdge] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        edges.extend(extract_detailed_edges(path.relative_to(root).as_posix(), text))
    known_targets = _canonical_targets(paths, root)
    source_pages = {
        path.relative_to(root).as_posix() for path in paths if path.relative_to(root).as_posix().startswith("wiki/")
    }
    inbound: defaultdict[str, int] = defaultdict(int)
    outbound: Counter[str] = Counter()
    broken: set[str] = set()
    for edge in edges:
        outbound[edge.source] += 1
        inbound[edge.target] += 1
        if edge.edge_type in {"links_to", "embeds"} and edge.target not in known_targets:
            broken.add(edge.target)
    orphan_pages = tuple(
        sorted(
            page
            for page in source_pages
            if inbound.get(page, 0) == 0
            and inbound.get(PurePosixPath(page).with_suffix("").as_posix(), 0) == 0
            and inbound.get(PurePosixPath(page).stem, 0) == 0
        )
    )
    edge_counts = Counter(edge.edge_type for edge in edges)
    alias_counts = Counter(edge.target for edge in edges if edge.edge_type == "aliases")
    metrics: dict[str, object] = {
        "node_count": len({edge.source for edge in edges} | {edge.target for edge in edges}),
        "edge_count": len(edges),
        "edge_count_by_type": dict(sorted(edge_counts.items())),
        "orphan_page_count": len(orphan_pages),
        "broken_target_count": len(broken),
        "alias_collisions": sorted(alias for alias, count in alias_counts.items() if count > 1),
        "embed_count": edge_counts.get("embeds", 0),
        "heading_or_block_ref_count": edge_counts.get("mentions", 0),
        "top_in_degree": sorted(inbound.items(), key=lambda item: (-item[1], item[0]))[:10],
        "top_out_degree": sorted(outbound.items(), key=lambda item: (-item[1], item[0]))[:10],
        "source_citation_count": edge_counts.get("cites", 0),
    }
    return GraphBuildResult(
        edges=tuple(edges), metrics=metrics, broken_targets=tuple(sorted(broken)), orphan_pages=orphan_pages
    )


def render_graph_edges_jsonl(edges: list[GraphEdge] | tuple[GraphEdge, ...]) -> str:
    """Render graph edges as deterministic JSONL."""
    import json

    return "".join(json.dumps(edge.to_dict(), sort_keys=True, ensure_ascii=False) + "\n" for edge in edges)


def render_graph_report(result: GraphBuildResult) -> str:
    """Render a human-readable graph analytics report."""
    lines = ["# Nerdbot Graph Report", "", "## Metrics"]
    for key, value in result.metrics.items():
        lines.append(f"- {markdown_code(key)}: {markdown_code(value)}")
    lines.extend(["", "## Broken Targets"])
    if result.broken_targets:
        lines.extend(f"- {markdown_code(target)}" for target in result.broken_targets)
    else:
        lines.append("- none")
    lines.extend(["", "## Orphan Pages"])
    if result.orphan_pages:
        lines.extend(f"- {markdown_code(path)}" for path in result.orphan_pages)
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
