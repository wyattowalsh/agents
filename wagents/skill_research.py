"""Cached per-skill research artifacts for generated docs pages."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from wagents import DOCS_DIR, ROOT
from wagents.catalog_rows import curated_entry_by_name
from wagents.external_skills import ExternalSkillEntry, read_external_skill_entries
from wagents.skill_docs import SkillDocNode, collect_skill_doc_nodes

RESEARCH_DIR = DOCS_DIR / "src" / "skill-research"
MANIFEST_PATH = DOCS_DIR / "src" / "generated-skill-research-index.mjs"
QUERIES_PATH = Path(__file__).resolve().parent / "data" / "skill-research-queries.yaml"

_LOCAL_PATH_PATTERN = re.compile(r"(/Users/|/home/|/private/)")
_STALE_DAYS = {"custom": 90, "installed": 30, "curated-external": 30}


CURATED_RESEARCH_SECTIONS: tuple[str, ...] = (
    "Purpose",
    "Harness Coverage",
    "Trust And Risks",
    "Install Prerequisites",
    "Upstream Maintainer",
    "Comparable Alternatives",
)


@dataclass(frozen=True)
class SkillResearchArtifact:
    skill: str
    source_type: str
    researched_at: str
    research_tier: str
    mean_confidence: float
    body: str


def research_queries() -> dict[str, Any]:
    """Load per-source research query templates."""
    if not QUERIES_PATH.exists():
        return {}
    return yaml.safe_load(QUERIES_PATH.read_text(encoding="utf-8")) or {}


def research_artifact_path(skill_id: str) -> Path:
    return RESEARCH_DIR / f"{skill_id}.md"


def load_skill_research(skill_id: str) -> str | None:
    """Return markdown body (after frontmatter) for a cached research artifact."""
    path = research_artifact_path(skill_id)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text.strip() or None
    meta, body = _parse_frontmatter(text)
    if not meta and len(text.split("---", 2)) < 3:
        return None
    return body.strip() or None


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    return dict(meta), parts[2].strip()


def validate_artifact(path: Path) -> list[str]:
    """Validate a research artifact file."""
    errors: list[str] = []
    if not path.exists():
        return ["missing file"]
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    for key in ("skill", "source_type", "researched_at", "research_tier", "mean_confidence"):
        if key not in meta:
            errors.append(f"missing frontmatter field: {key}")
    if _LOCAL_PATH_PATTERN.search(text):
        errors.append("contains local filesystem path")
    if not body.strip():
        errors.append("empty research body")
    source_type = str(meta.get("source_type") or "")
    if source_type == "curated-external":
        for section in CURATED_RESEARCH_SECTIONS:
            if f"## {section}" not in body:
                errors.append(f"missing curated-external header: ## {section}")
    return errors


def is_stale(path: Path, *, source_type: str) -> bool:
    """Return whether a research artifact is older than the staleness window."""
    if not path.exists():
        return True
    meta, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
    researched_at = str(meta.get("researched_at") or "")
    if not researched_at:
        return True
    try:
        researched = datetime.fromisoformat(researched_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    age_days = (datetime.now(tz=UTC) - researched.astimezone(UTC)).days
    return age_days > _STALE_DAYS.get(source_type, 30)


def write_skill_research_artifact(
    skill_id: str,
    *,
    source_type: str,
    research_tier: str,
    mean_confidence: float,
    body: str,
) -> Path:
    """Write a research artifact markdown file."""
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    researched_at = datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    frontmatter = {
        "skill": skill_id,
        "source_type": source_type,
        "researched_at": researched_at,
        "research_tier": research_tier,
        "mean_confidence": round(mean_confidence, 2),
    }
    content = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n\n" + body.strip() + "\n"
    path = research_artifact_path(skill_id)
    path.write_text(content, encoding="utf-8")
    return path


def partition_skills_for_research(
    doc_nodes: list[SkillDocNode] | None = None,
    *,
    batch_size: int = 25,
    include_installed: bool = True,
    source_types: set[str] | None = None,
) -> list[list[SkillDocNode]]:
    """Partition skill doc nodes into fixed-size research batches."""
    nodes = doc_nodes or collect_skill_doc_nodes(include_installed=include_installed, include_curated=True)
    if source_types is not None:
        nodes = [node for node in nodes if node.source_type in source_types]
    batches: list[list[SkillDocNode]] = []
    for index in range(0, len(nodes), batch_size):
        batches.append(nodes[index : index + batch_size])
    return batches


def partition_skills_by_source(
    batch_max: int = 10,
    curated_status: str | None = None,
    include_installed: bool = False,
) -> list[list[SkillDocNode]]:
    """Partition skill doc nodes into batches (max size batch_max), grouped by _skills_install_source then chunked.
    Optional curated_status filter (for curated-external). Groups ensure related-source skills stay together for
    batched research prompts when using GROUP BY install_source in enrichment waves.
    """
    nodes = collect_skill_doc_nodes(include_installed=include_installed, include_curated=True)
    if curated_status is not None:
        nodes = [node for node in nodes if node.curated_status == curated_status]
    groups: dict[str, list[SkillDocNode]] = defaultdict(list)
    for node in nodes:
        meta = node.node.metadata or {}
        src = str(meta.get("_skills_install_source") or "").strip() or "unknown"
        groups[src].append(node)
    # stable order: sort group keys, sort nodes by id within group
    batches: list[list[SkillDocNode]] = []
    for src in sorted(groups.keys()):
        gnodes = sorted(groups[src], key=lambda n: n.id)
        for index in range(0, len(gnodes), batch_max):
            batches.append(gnodes[index : index + batch_max])
    return batches


def build_batch_prompt(batch: list[SkillDocNode]) -> str:
    """Build a subagent prompt for researching one batch of skills."""
    templates = research_queries()
    lines = ["Research the following skills and write docs/src/skill-research/<name>.md for each."]
    for doc in batch:
        node = doc.node
        template_key = doc.curated_status if doc.curated_status in templates else doc.source_type
        template = templates.get(template_key) or templates.get(doc.source_type, {})
        prompt = str(template.get("prompt", "Summarize skill {name}."))
        formatted = prompt.format(
            name=node.id,
            install_source=node.metadata.get("_skills_install_source", ""),
            source_url=node.metadata.get("_skills_source", ""),
            curated_status=doc.curated_status,
            trust_tier=node.metadata.get("_skills_trust_tier", ""),
        )
        lines.append(f"- {node.id} ({doc.source_type}): {formatted.strip()}")
    lines.append("Use Quick Answer or Research Brief format. Max 400 words per skill. Redact local paths.")
    return "\n".join(lines)


def render_research_manifest() -> str:
    """Return generated-skill-research-index.mjs content from cached artifacts."""
    entries: list[dict[str, Any]] = []
    if RESEARCH_DIR.exists():
        for path in sorted(RESEARCH_DIR.glob("*.md")):
            meta, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
            entries.append({
                "name": meta.get("skill", path.stem),
                "source_type": meta.get("source_type", ""),
                "researched_at": meta.get("researched_at", ""),
                "research_tier": meta.get("research_tier", ""),
                "mean_confidence": meta.get("mean_confidence", 0.0),
                "stale": is_stale(path, source_type=str(meta.get("source_type") or "custom")),
            })
    encoded = json.dumps(entries, indent=2, sort_keys=True)
    return f"// Auto-generated by wagents docs generate — do not edit\nexport const skillResearchIndex = {encoded};\n"


def update_research_manifest() -> None:
    """Write generated-skill-research-index.mjs from cached artifacts."""
    MANIFEST_PATH.write_text(
        render_research_manifest(),
        encoding="utf-8",
    )


def research_coverage(
    doc_nodes: list[SkillDocNode] | None = None,
    *,
    source_type: str = "custom",
    curated_status: str | None = None,
) -> tuple[int, int]:
    """Return (present, total) research cache coverage for a source type (optionally filtered by curated_status)."""
    nodes = doc_nodes or collect_skill_doc_nodes(include_installed=False, include_curated=True)
    filtered = [node for node in nodes if node.source_type == source_type]
    if curated_status is not None:
        filtered = [node for node in filtered if node.curated_status == curated_status]
    present = sum(1 for node in filtered if research_artifact_path(node.id).exists())
    return present, len(filtered)


_NOT_FOR_PATTERN = re.compile(r"NOT for ([^(]+)\(([^)]+)\)", re.IGNORECASE)


def _extract_comparable_alternative(description: str) -> str:
    match = _NOT_FOR_PATTERN.search(description)
    if match:
        scope, skill = match.group(1).strip(), match.group(2).strip()
        return f"`{skill}` for {scope.lower()}"
    return "A general-purpose agent instruction without a scoped skill contract"


def _first_body_paragraph(body: str, *, max_chars: int = 320) -> str:
    found_heading = False
    paragraph: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not found_heading:
            if stripped.startswith("#"):
                found_heading = True
            continue
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith("|") or stripped.startswith("```"):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    text = " ".join(paragraph).strip()
    if len(text) > max_chars:
        return text[: max_chars - 3].rstrip() + "..."
    return text


def _stack_assumptions(node: SkillDocNode) -> str:
    compatibility = str(node.node.metadata.get("compatibility") or "").strip()
    if compatibility:
        return compatibility
    skill_dir = (ROOT / node.node.source_path).parent
    hints: list[str] = []
    if (skill_dir / "scripts").is_dir():
        hints.append("portable skill scripts under `scripts/`")
    if (skill_dir / "references").is_dir():
        hints.append("on-demand references")
    if (skill_dir / "evals").is_dir():
        hints.append("eval fixtures")
    if hints:
        return "; ".join(hints)
    return "Repository skill format (`skills/<name>/SKILL.md`) with progressive disclosure"


def build_repo_grounded_research_body(doc: SkillDocNode) -> str:
    """Build a Phase A quick research brief grounded in repository SKILL.md."""
    description = doc.description.strip() or doc.node.description.strip()
    summary = _first_body_paragraph(doc.node.body)
    alternative = _extract_comparable_alternative(description)
    stack = _stack_assumptions(doc)
    lines = [
        "## Quick Answer",
        "",
        f"**Problem:** {description}",
        "",
        f"**Stack / assumptions:** {stack}",
        "",
        f"**Comparable alternative:** {alternative}",
        "",
    ]
    if summary:
        lines.extend(["**Repo summary:**", "", summary, ""])
    lines.append(f"> Grounded in repository `skills/{doc.id}/SKILL.md`; treat as evidence, not authority.")
    return "\n".join(lines)


def build_curated_config_research_body(entry: ExternalSkillEntry) -> str:
    """Build structured research body from ExternalSkillEntry (config/external-skills.md fields)."""
    purpose = (entry.notes or entry.risk_notes or f"Curated external skill: {entry.name}.").strip()
    harness_list = ", ".join(entry.target_agents) if entry.target_agents else "(see install command -a targets)"
    trust_parts: list[str] = [
        f"trust_tier={entry.trust_tier or 'unspecified'}",
        f"status={entry.status}",
        f"provenance={entry.provenance_status}",
    ]
    if entry.risk_notes:
        trust_parts.append(f"risks={entry.risk_notes}")
    if entry.promotion_policy:
        trust_parts.append(f"policy={entry.promotion_policy}")
    if entry.provenance_evidence:
        trust_parts.append(f"evidence={entry.provenance_evidence}")
    trust_and_risks = "; ".join(trust_parts)

    prereqs: list[str] = []
    if entry.install_command:
        prereqs.append(f"Install: `{entry.install_command}`")
    prereqs.append(f"status={entry.status}; selector={entry.selector_mode}")
    if entry.unresolved_reason:
        prereqs.append(f"unresolved: {entry.unresolved_reason}")
    install_prereqs = " ".join(prereqs)

    if entry.source_url:
        upstream = f"[{entry.source}]({entry.source_url})"
    else:
        upstream = entry.source or entry.install_source or "config/external-skills.md"

    comparable = _extract_comparable_alternative(purpose)

    lines = [
        "## Purpose",
        "",
        purpose,
        "",
        "## Harness Coverage",
        "",
        f"Target agents: {harness_list}.",
        "",
        "## Trust And Risks",
        "",
        trust_and_risks,
        "",
        "## Install Prerequisites",
        "",
        install_prereqs,
        "",
        "## Upstream Maintainer",
        "",
        upstream,
        "",
        "## Comparable Alternatives",
        "",
        comparable,
        "",
        "> Sourced from curated config/external-skills.md; use /review source for live evidence.",
    ]
    return "\n".join(lines)


def seed_phase_a_research(
    doc_nodes: list[SkillDocNode] | None = None,
    *,
    overwrite: bool = False,
) -> list[Path]:
    """Write Phase A research artifacts for repo-owned custom skills."""
    nodes = doc_nodes or collect_skill_doc_nodes(include_installed=False, include_curated=False)
    written: list[Path] = []
    for doc in nodes:
        if doc.source_type != "custom":
            continue
        path = research_artifact_path(doc.id)
        if path.exists() and not overwrite:
            continue
        body = build_repo_grounded_research_body(doc)
        written.append(
            write_skill_research_artifact(
                doc.id,
                source_type="custom",
                research_tier="quick",
                mean_confidence=0.78,
                body=body,
            )
        )
    if written:
        update_research_manifest()
    return written


def _curated_entry_for_doc(doc: SkillDocNode, entries: list[ExternalSkillEntry]) -> ExternalSkillEntry | None:
    """Resolve the config row that matches a curated catalog doc node (install_source first, else first-by-name)."""
    install_source = str((doc.node.metadata or {}).get("_skills_install_source") or "")
    matches = [entry for entry in entries if entry.name == doc.id]
    if not matches:
        return None
    for entry in matches:
        if entry.install_source == install_source:
            return entry
    return curated_entry_by_name(entries, doc.id)


def seed_curated_config_research(
    curated_status: str | None = None,
    overwrite: bool = False,
) -> list[Path]:
    """Write research artifacts for curated-external skills, using config fields via build_curated_config_research_body.
    Optional curated_status filter (e.g. 'install-now-after-trust-gate'); overwrite to force rewrite.
    """
    entries = read_external_skill_entries()
    doc_nodes = collect_skill_doc_nodes(include_installed=False, include_curated=True)
    curated_docs = [doc for doc in doc_nodes if doc.source_type == "curated-external"]
    if curated_status is not None:
        curated_docs = [doc for doc in curated_docs if doc.curated_status == curated_status]
    written: list[Path] = []
    for doc in curated_docs:
        entry = _curated_entry_for_doc(doc, entries)
        if entry is None:
            continue
        path = research_artifact_path(doc.id)
        if path.exists() and not overwrite:
            continue
        body = build_curated_config_research_body(entry)
        written.append(
            write_skill_research_artifact(
                doc.id,
                source_type="curated-external",
                research_tier="standard",
                mean_confidence=0.65,
                body=body,
            )
        )
    if written:
        update_research_manifest()
    return written
