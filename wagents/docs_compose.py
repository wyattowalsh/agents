"""Catalog page composition: coverage tracking and orchestrator wave prompts."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import yaml

from wagents import CONTENT_DIR, ROOT
from wagents.catalog import CatalogNode
from wagents.docs_lint import HAND_MAINTAINED_SENTINEL
from wagents.skill_docs import collect_all_doc_nodes

ComposeSurface = Literal["skills", "agents", "mcp", "hooks", "configs", "all"]

COMPOSE_MANIFEST = ROOT / "planning" / "manifests" / "docs-composed-coverage.json"
HOOK_REGISTRY = ROOT / "config" / "hook-registry.json"
HARNESS_CONFIG_SOURCES = (
    ROOT / "config" / "sync-manifest.json",
    ROOT / "config" / "mcp-registry.json",
    ROOT / "config" / "tooling-policy.json",
)

REFERENCE_SKILL_PAGE = "docs/src/content/docs/skills/catalog/custom/orchestrator.mdx"


@dataclass(frozen=True)
class ComposeTarget:
    surface: str
    asset_id: str
    page_path: Path
    source_path: str | None = None
    source_kind: str | None = None


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[3:end].strip()
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def is_composed_mdx(text: str) -> bool:
    if HAND_MAINTAINED_SENTINEL in text:
        return True
    fm = _parse_frontmatter(text)
    return fm.get("composed") is True


def _skill_page_path(node: CatalogNode) -> Path:
    from wagents.skill_docs import skill_catalog_group

    group = skill_catalog_group(node=node)
    return CONTENT_DIR / "skills" / "catalog" / group / f"{node.id}.mdx"


def _agent_page_path(node: CatalogNode) -> Path:
    return CONTENT_DIR / "agents" / f"{node.id}.mdx"


def _mcp_page_path(node: CatalogNode) -> Path:
    return CONTENT_DIR / "mcp" / f"{node.id}.mdx"


def collect_compose_targets(*, surface: ComposeSurface = "all") -> list[ComposeTarget]:
    targets: list[ComposeTarget] = []
    surfaces = {"skills", "agents", "mcp", "hooks", "configs"} if surface == "all" else {surface}

    if "skills" in surfaces or "agents" in surfaces or "mcp" in surfaces:
        nodes = collect_all_doc_nodes(include_installed=False, include_drafts=False)
        for node in nodes:
            if node.kind == "skill" and "skills" in surfaces:
                targets.append(
                    ComposeTarget(
                        surface="skills",
                        asset_id=node.id,
                        page_path=_skill_page_path(node),
                        source_path=node.source_path,
                        source_kind=node.source,
                    )
                )
            elif node.kind == "agent" and "agents" in surfaces:
                targets.append(
                    ComposeTarget(
                        surface="agents",
                        asset_id=node.id,
                        page_path=_agent_page_path(node),
                        source_path=node.source_path,
                        source_kind="repo",
                    )
                )
            elif node.kind == "mcp" and "mcp" in surfaces:
                targets.append(
                    ComposeTarget(
                        surface="mcp",
                        asset_id=node.id,
                        page_path=_mcp_page_path(node),
                        source_path=node.source_path,
                        source_kind="repo",
                    )
                )

    if "hooks" in surfaces and HOOK_REGISTRY.exists():
        data = json.loads(HOOK_REGISTRY.read_text(encoding="utf-8"))
        for hook in data.get("hooks") or []:
            hook_id = str(hook.get("id") or "").strip()
            if not hook_id:
                continue
            targets.append(
                ComposeTarget(
                    surface="hooks",
                    asset_id=hook_id,
                    page_path=CONTENT_DIR / "hooks" / f"{hook_id}.mdx",
                    source_path=str(HOOK_REGISTRY.relative_to(ROOT)),
                    source_kind="registry",
                )
            )

    if "configs" in surfaces:
        for cfg in HARNESS_CONFIG_SOURCES:
            if not cfg.exists():
                continue
            targets.append(
                ComposeTarget(
                    surface="configs",
                    asset_id=cfg.stem,
                    page_path=CONTENT_DIR / "harness-config" / f"{cfg.stem}.mdx",
                    source_path=str(cfg.relative_to(ROOT)),
                    source_kind="registry",
                )
            )

    return targets


def compose_coverage(*, surface: ComposeSurface = "all") -> dict:
    targets = collect_compose_targets(surface=surface)
    composed = 0
    scaffold = 0
    missing = 0
    by_surface: dict[str, dict[str, int]] = defaultdict(lambda: {"composed": 0, "scaffold": 0, "missing": 0})

    for target in targets:
        bucket = by_surface[target.surface]
        if not target.page_path.exists():
            missing += 1
            bucket["missing"] += 1
            continue
        text = target.page_path.read_text(encoding="utf-8")
        if is_composed_mdx(text):
            composed += 1
            bucket["composed"] += 1
        else:
            scaffold += 1
            bucket["scaffold"] += 1

    total = len(targets)
    pct = round((composed / total) * 100, 1) if total else 100.0
    return {
        "generated_at": date.today().isoformat(),
        "surface": surface,
        "total": total,
        "composed": composed,
        "scaffold": scaffold,
        "missing": missing,
        "composed_pct": pct,
        "by_surface": dict(by_surface),
    }


def write_compose_manifest(*, surface: ComposeSurface = "all") -> Path:
    COMPOSE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    payload = compose_coverage(surface=surface)
    COMPOSE_MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return COMPOSE_MANIFEST


def partition_compose_targets(
    targets: list[ComposeTarget],
    *,
    batch_size: int = 8,
) -> list[list[ComposeTarget]]:
    pending: list[ComposeTarget] = []
    for target in targets:
        if not target.page_path.exists():
            pending.append(target)
            continue
        if not is_composed_mdx(target.page_path.read_text(encoding="utf-8")):
            pending.append(target)
    pending.sort(key=lambda t: (t.surface, t.asset_id))
    batches: list[list[ComposeTarget]] = []
    for index in range(0, len(pending), batch_size):
        batches.append(pending[index : index + batch_size])
    return batches


def partition_skills_for_compose(
    *,
    batch_size: int = 8,
    include_installed: bool = False,
    custom_only: bool = True,
) -> list[list[ComposeTarget]]:
    nodes = collect_all_doc_nodes(include_installed=include_installed, include_drafts=False)
    skill_targets: list[ComposeTarget] = []
    for node in nodes:
        if node.kind != "skill":
            continue
        if custom_only and node.source != "custom":
            continue
        skill_targets.append(
            ComposeTarget(
                surface="skills",
                asset_id=node.id,
                page_path=_skill_page_path(node),
                source_path=node.source_path,
                source_kind=node.source,
            )
        )
    return partition_compose_targets(skill_targets, batch_size=batch_size)


def _compose_instructions() -> str:
    return f"""Compose harness catalog MDX pages (do NOT trim or summarize source).

Quality bar: `{REFERENCE_SKILL_PAGE}`

For each target page:
1. Read source asset (SKILL.md / agents/*.md / mcp/*/server.py / hook-registry row).
2. Read optional inputs: docs/src/authoring/skills/<id>.mdx, docs/src/skill-research/<id>.md, site index metadata.
3. Write curated prose sections (Quick Start, What It Does, Modes/Dispatch when useful, Related Skills).
4. Put full source in collapsed <details class="source-disclosure"> (never delete SKILL body).
5. YAML frontmatter MUST include the standardized catalog contract
   (composed: true, docs_density: standard, page_kind, source_kind, asset_id).
6. Insert HAND-MAINTAINED sentinel immediately after frontmatter.
7. Do not duplicate section headings above and inside source disclosure.

Validate touched paths: uv run wagents docs build (or spot-check links)."""


def build_compose_batch_prompt(batch: list[ComposeTarget], *, wave_id: str = "wave-1") -> str:
    lines = [
        _compose_instructions(),
        "",
        f"Wave: {wave_id}",
        f"Targets ({len(batch)}):",
    ]
    for target in batch:
        research = ROOT / "docs" / "src" / "skill-research" / f"{target.asset_id}.md"
        authoring = ROOT / "docs" / "authoring" / "skills" / f"{target.asset_id}.mdx"
        extras = []
        if target.source_path:
            extras.append(f"source={target.source_path}")
        if research.exists():
            extras.append(f"research={research.relative_to(ROOT)}")
        if authoring.exists():
            extras.append(f"authoring={authoring.relative_to(ROOT)}")
        extra = f" ({', '.join(extras)})" if extras else ""
        try:
            rel_page = target.page_path.relative_to(ROOT)
        except ValueError:
            rel_page = target.page_path
        lines.append(f"- [{target.surface}] {target.asset_id} -> {rel_page}{extra}")
    lines.append("")
    lines.append("Use subagent model grok-composer-2.5-fast when delegating within this wave.")
    return "\n".join(lines)


def check_composed_threshold(*, surface: ComposeSurface = "all", min_pct: float = 100.0) -> tuple[bool, dict]:
    report = compose_coverage(surface=surface)
    ok = report["composed_pct"] >= min_pct
    return ok, report
