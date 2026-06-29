"""Lightweight docs page quality scoring against the docs-steward checklist."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from wagents import CONTENT_DIR, ROOT

STARLIGHT_COMPONENTS = (
    "Aside", "Steps", "Tabs", "TabItem", "CardGrid", "Card", "LinkCard", "Badge", "FileTree",
)


@dataclass
class PageScore:
    path: str
    dimensions: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def average(self) -> float:
        if not self.dimensions:
            return 0.0
        return sum(self.dimensions.values()) / len(self.dimensions)

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "average": round(self.average, 2),
            "dimensions": self.dimensions,
            "notes": self.notes,
        }


def _score_description(body: str, frontmatter_desc: str) -> int:
    desc = (frontmatter_desc or "").strip()
    if not desc or "TODO" in desc:
        return 1
    if len(desc) < 40:
        return 2
    if len(desc) < 120:
        return 3
    if "## What It Does" in body or len(desc) >= 120:
        return 4
    return 5


def _score_usage(body: str) -> int:
    score = 3 if ("/review" in body or "Use when" in body[:500]) else 2
    if "```" in body and ("/" in body or "wagents " in body or "npx " in body):
        score = max(score, 4)
    if body.count("```") >= 3:
        score = 5
    return score


def _score_visual(body: str) -> int:
    imports = sum(1 for comp in STARLIGHT_COMPONENTS if comp in body)
    if imports == 0:
        return 1 if "<" not in body else 2
    if imports <= 2:
        return 3
    if imports <= 5:
        return 4
    return 5


def _score_cross_refs(body: str) -> int:
    links = len(re.findall(r"\]\(/", body))
    if links == 0:
        return 1
    if links < 3:
        return 3
    if links < 8:
        return 4
    return 5


def _score_structure(body: str) -> int:
    h2 = len(re.findall(r"^## ", body, re.MULTILINE))
    if h2 == 0:
        return 2
    if h2 < 3:
        return 3
    if h2 < 6:
        return 4
    return 5


def _score_interactivity(body: str) -> int:
    if "CatalogBrowser" in body or "InstallCommand" in body:
        return 4
    if "<details" in body or "client:" in body:
        return 5
    return 2


def _score_external_links(body: str) -> int:
    ext = len(re.findall(r"https?://", body))
    if ext == 0:
        return 2
    if ext < 3:
        return 3
    return 4


def _score_agent_compat(body: str) -> int:
    if "targetAgents" in body or "harness" in body.lower() or "Supported" in body:
        return 4
    if "npx skills add" in body or "--agent" in body:
        return 5
    return 2


def _score_source_disclosure(body: str) -> int:
    if "HAND-MAINTAINED" in body or "Source" in body or "provenance" in body.lower():
        return 4
    if "wagents docs generate" in body or "authoring/skills" in body:
        return 5
    return 2


def score_mdx_page(path: Path) -> PageScore:
    text = path.read_text(encoding="utf-8")
    rel = str(path.relative_to(ROOT))
    fm_desc = ""
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            body = parts[2]
            match = re.search(r'^description:\s*"?([^"\n]+)"?', fm, re.MULTILINE)
            if match:
                fm_desc = match.group(1).strip()

    score = PageScore(path=rel)
    score.dimensions = {
        "description": _score_description(body, fm_desc),
        "usage_examples": _score_usage(body),
        "visual_elements": _score_visual(body),
        "cross_references": _score_cross_refs(body),
        "structure": _score_structure(body),
        "interactivity": _score_interactivity(body),
        "external_links": _score_external_links(body),
        "agent_compatibility": _score_agent_compat(body),
        "source_disclosure": _score_source_disclosure(body),
    }
    if score.average < 3:
        score.notes.append("below acceptable threshold (3.0)")
    return score


def collect_score_paths(*, surface: str = "all", limit: int | None = None) -> list[Path]:
    roots: list[Path] = []
    if surface in {"all", "skills-custom"}:
        roots.append(CONTENT_DIR / "skills" / "catalog" / "custom")
    if surface in {"all", "skills-external"}:
        roots.append(CONTENT_DIR / "skills" / "catalog" / "external")
    if surface in {"all", "agents"}:
        roots.append(CONTENT_DIR / "agents")
    if surface in {"all", "mcp"}:
        roots.append(CONTENT_DIR / "mcp")
    if surface in {"all", "hooks"}:
        roots.append(CONTENT_DIR / "hooks")

    paths: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.mdx")):
            if path.name == "index.mdx":
                continue
            paths.append(path)
    if limit is not None:
        return paths[:limit]
    return paths


def score_docs_surface(*, surface: str = "all", limit: int | None = None) -> list[PageScore]:
    return [score_mdx_page(path) for path in collect_score_paths(surface=surface, limit=limit)]


def write_score_manifest(scores: list[PageScore], *, manifest_path: Path | None = None) -> Path:
    manifest_path = manifest_path or ROOT / "planning" / "manifests" / "docs-quality-baseline.json"
    averages = [s.average for s in scores if s.average > 0]
    payload = {
        "generated_at": __import__("datetime").date.today().isoformat(),
        "page_count": len(scores),
        "median_average": round(sorted(averages)[len(averages) // 2], 2) if averages else 0,
        "mean_average": round(sum(averages) / len(averages), 2) if averages else 0,
        "pages": [s.as_dict() for s in scores],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return manifest_path
