"""Docs verbosity lint for generated and hand-maintained MDX pages."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from wagents import CONTENT_DIR

HAND_MAINTAINED_SENTINEL = "{/* HAND-MAINTAINED */}"

LINE_CAP_GENERATED_SKILL = 600
LINE_CAP_HAND_SKILL = 650
LINE_CAP_COMPOSED_HAND = 1200
LINE_CAP_CLI = 900
LINE_CAP_AGENT = 120

FORBIDDEN_BOILERPLATE = (
    "## Related Pages",
    "## Built With",
    '<Aside type="note" title="Source">',
)

DUPLICATE_SECTION_HEADINGS = (
    "## Dispatch",
    "## What It Does",
    "## Tier Selection",
    "## Orchestration Patterns",
)


@dataclass
class LintFinding:
    path: str
    rule: str
    message: str
    severity: str = "warn"

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class LintReport:
    findings: list[LintFinding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def warn_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warn")

    def add(self, *, path: Path, rule: str, message: str, severity: str = "warn") -> None:
        try:
            rel = path.relative_to(CONTENT_DIR.parent.parent)
        except ValueError:
            rel = path
        self.findings.append(
            LintFinding(path=str(rel), rule=rule, message=message, severity=severity)
        )


def _is_hand_maintained(text: str) -> bool:
    return HAND_MAINTAINED_SENTINEL in text


def _split_details_blocks(text: str) -> tuple[str, list[str]]:
    outside: list[str] = []
    inside: list[str] = []
    in_details = False
    depth = 0
    current_inside: list[str] = []
    for line in text.splitlines():
        if re.match(r"<details\b", line, re.I):
            in_details = True
            depth += 1
            if depth == 1:
                current_inside = []
            continue
        if in_details and re.match(r"</details>", line, re.I):
            depth -= 1
            if depth == 0:
                inside.append("\n".join(current_inside))
                in_details = False
            continue
        if in_details and depth >= 1:
            current_inside.append(line)
        else:
            outside.append(line)
    return "\n".join(outside), inside


def _count_duplicate_headings(outside: str, inside_blocks: list[str]) -> list[str]:
    hits: list[str] = []
    inside_joined = "\n".join(inside_blocks)
    for heading in DUPLICATE_SECTION_HEADINGS:
        if heading in outside and heading in inside_joined:
            hits.append(heading)
    return hits


def _resolve_line_cap(rel: str, *, hand: bool) -> int | None:
    if rel == "cli.mdx":
        return LINE_CAP_CLI
    if rel.startswith("agents/") and rel.endswith(".mdx") and rel != "agents/index.mdx":
        return LINE_CAP_AGENT
    if rel.startswith("skills/catalog/custom/") and rel.endswith(".mdx") and not rel.endswith("/index.mdx"):
        return LINE_CAP_HAND_SKILL if hand else LINE_CAP_GENERATED_SKILL
    return None


def lint_docs_content(*, strict: bool = False) -> LintReport:
    report = LintReport()
    if not CONTENT_DIR.exists():
        report.add(path=CONTENT_DIR, rule="missing-content", message="docs content dir missing", severity="error")
        return report

    for path in sorted(CONTENT_DIR.rglob("*.mdx")):
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(CONTENT_DIR))
        hand = _is_hand_maintained(text)
        line_count = len(text.splitlines())

        for needle in FORBIDDEN_BOILERPLATE:
            if needle in text:
                report.add(
                    path=path,
                    rule="forbidden-boilerplate",
                    message=f"contains removed boilerplate: {needle!r}",
                    severity="error" if strict else "warn",
                )

        if hand and "View Full SKILL.md" in text and 'class="source-disclosure"' not in text:
            report.add(
                path=path,
                rule="hand-details-class",
                message='hand-maintained SKILL disclosure should use class="source-disclosure"',
            )

        outside, inside_blocks = _split_details_blocks(text)
        composed = hand or _is_composed_frontmatter(text)
        for heading in _count_duplicate_headings(outside, inside_blocks):
            report.add(
                path=path,
                rule="duplicate-section",
                message=f"{heading} appears both above and inside collapsed SKILL disclosure",
                severity="error" if composed else "warn",
            )

        cap = _resolve_line_cap(rel, hand=hand)
        if composed and hand:
            cap = LINE_CAP_COMPOSED_HAND
        elif composed:
            cap = None
        if cap is not None and line_count > cap:
            report.add(
                path=path,
                rule="line-cap",
                message=f"{line_count} lines exceeds soft cap {cap}",
            )

    return report


def load_verbosity_baseline(manifest_path: Path) -> dict[str, int]:
    if not manifest_path.exists():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages = data.get("pages") or {}
    return {str(k): int(v) for k, v in pages.items()}


def compare_to_baseline(report: LintReport, *, manifest_path: Path, regression_pct: float = 0.15) -> None:
    baseline = load_verbosity_baseline(manifest_path)
    if not baseline:
        return
    for path in sorted(CONTENT_DIR.rglob("*.mdx")):
        rel = str(path.relative_to(CONTENT_DIR))
        if rel not in baseline:
            continue
        current = len(path.read_text(encoding="utf-8").splitlines())
        base = baseline[rel]
        if base <= 0:
            continue
        growth = (current - base) / base
        if growth > regression_pct:
            report.add(
                path=path,
                rule="baseline-regression",
                message=f"grew {current - base:+d} lines ({growth:.0%}) vs baseline {base}",
            )


def _is_composed_frontmatter(text: str) -> bool:
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end < 0:
        return False
    block = text[3:end]
    return "composed: true" in block


def compose_coverage_report() -> dict:
    """Report composed vs scaffold catalog pages under docs content."""
    from wagents.docs_compose import compose_coverage

    return compose_coverage(surface="all")
