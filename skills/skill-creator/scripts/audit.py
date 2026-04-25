#!/usr/bin/env python3
"""Deterministic quality scoring for AI agent skills.

Reads skills/<name>/SKILL.md, evaluates frontmatter, body structure,
pattern coverage, references, scripts, and conciseness, then outputs
a structured JSON report to stdout. Warnings go to stderr.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _shared import parse_frontmatter

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table as RichTable
    from rich.text import Text
    _RICH = True
except ImportError:
    _RICH = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KEBAB_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RESERVED_WORDS = {"anthropic", "claude"}
ACTION_VERBS = {
    "create", "detect", "analyze", "generate", "scan", "build", "run",
    "check", "validate", "review", "host", "simulate", "audit", "deploy",
    "transform", "convert", "extract", "parse", "install", "configure",
    "monitor", "test", "optimize", "refactor", "scaffold", "migrate",
    "evaluate", "research", "diagnose", "surface", "explore",
}
GRADE_THRESHOLDS = [(90, "A"), (75, "B"), (60, "C"), (40, "D"), (0, "F")]
PATTERN_NAMES = [
    "dispatch-table", "reference-file-index", "critical-rules",
    "canonical-vocabulary", "scope-boundaries", "classification-gating",
    "scaling-strategy", "state-management", "scripts", "templates",
    "hooks", "progressive-disclosure", "body-substitutions", "stop-hooks",
]
RESOURCE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])((?:skills/[a-z0-9-]+/)?"
    r"(?:references|scripts|templates|assets|reports)/"
    r"[A-Za-z0-9_./-]*[A-Za-z0-9_-]\.[A-Za-z0-9_-]+)"
)

GRADE_STATUS = {
    "A": "Production-Ready",
    "B": "Solid",
    "C": "Needs Work",
    "D": "Draft Quality",
    "F": "Draft Quality",
}

GRADE_COLORS = {
    "A": "green",
    "B": "cyan",
    "C": "yellow",
    "D": "bright_red",
    "F": "red",
}


def _warn(msg: str) -> None:
    print(f"[audit] {msg}", file=sys.stderr)


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _grade(score: float) -> str:
    for threshold, letter in GRADE_THRESHOLDS:
        if score >= threshold:
            return letter
    return "F"


def _extract_heading_section(body: str, heading_re: str) -> str:
    """Return the section content after a matching heading, if present."""
    match = re.search(heading_re, body, re.I | re.M)
    if not match:
        return ""
    next_heading = re.search(r"^#{1,6}\s+", body[match.end():], re.M)
    if not next_heading:
        return body[match.end():]
    return body[match.end():match.end() + next_heading.start()]


def _dispatch_table_rows(body: str) -> list[str]:
    """Return data rows from the first $ARGUMENTS dispatch table."""
    rows: list[str] = []
    in_table = False
    for line in body.splitlines():
        if "$ARGUMENTS" in line and "|" in line:
            in_table = True
            continue
        if not in_table:
            continue
        if "|" not in line:
            break
        stripped = line.strip().strip("|").strip()
        if not stripped:
            break
        if re.match(r"^[-:\s|]+$", stripped):
            continue
        rows.append(line)
    return rows


def _has_reference_index(body: str) -> bool:
    """Return True when the body contains a references index table."""
    return any("references/" in ln.lower() and "|" in ln for ln in body.splitlines())


def _has_canonical_vocabulary_section(body: str) -> bool:
    """Return True for a dedicated canonical terms/vocabulary section."""
    section_patterns = [
        r"^#+\s*(canonical\s+(terms?|vocab(ulary)?)|vocabulary)\b",
        r"^\*\*(canonical\s+(terms?|vocab(ulary)?)|vocabulary)\*\*",
    ]
    return any(re.search(pattern, body, re.I | re.M) for pattern in section_patterns)


def _canonical_vocabulary_section(body: str) -> str:
    """Return the canonical vocabulary section content, if present."""
    heading_re = r"^#+\s*(canonical\s+(terms?|vocab(ulary)?)|vocabulary)\b.*$"
    section = _extract_heading_section(body, heading_re)
    if section:
        return section

    lines = body.splitlines()
    for idx, line in enumerate(lines):
        if re.search(r"^\*\*(canonical\s+(terms?|vocab(ulary)?)|vocabulary)\*\*", line, re.I):
            collected = [line]
            for next_line in lines[idx + 1:]:
                if re.match(r"^#{1,6}\s+", next_line):
                    break
                collected.append(next_line)
            return "\n".join(collected)
    return ""


def _mentioned_resource_paths(skill_dir: Path, body: str) -> set[str]:
    """Return packaged resource paths mentioned in SKILL.md body."""
    mentioned: set[str] = set()
    skill_prefix = f"skills/{skill_dir.name}/"
    for match in RESOURCE_PATH_RE.finditer(body):
        raw_path = match.group(1).rstrip("`.,:;)]}")
        if raw_path.startswith(skill_prefix):
            raw_path = raw_path[len(skill_prefix):]
        mentioned.add(raw_path)
    return mentioned


def _dispatch_action_labels(body: str) -> set[str]:
    """Return normalized action labels from the dispatch table."""
    labels: set[str] = set()
    ignored = {"action", "example"}
    for row in _dispatch_table_rows(body):
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        label = re.sub(r"`|\*", "", cells[1]).strip()
        label = re.sub(r"^(auto:\s*)", "", label, flags=re.I)
        label = re.sub(r"\s+", " ", label)
        normalized = label.lower()
        if not normalized or normalized in ignored:
            continue
        labels.add(normalized)
    return labels


def _has_classification_structure(body: str) -> bool:
    """Return True when the skill contains explicit routing or tiering logic."""
    heading_re = (
        r"^#+\s*(auto[- ]detection\s+heuristic|classification(?:/gating)?\s+logic|"
        r"classifier|gating(?:\s+logic)?|complexity\s+tier(?:s)?|tiering)\b"
    )
    section = _extract_heading_section(body, heading_re)
    if section:
        numbered = re.findall(r"^\s*\d+[.)]\s+.+", section, re.M)
        if len(numbered) >= 3:
            return True

    score_table = re.search(
        r"^\|\s*[^|\n]*score[^|\n]*\|\s*[^|\n]*(tier|mode|action)[^|\n]*\|",
        body,
        re.I | re.M,
    )
    range_rows = re.findall(r"^\|\s*(?:\d+\s*-\s*\d+|\d+\+)\s*\|", body, re.M)
    return bool(score_table and len(range_rows) >= 2)


def _classification_applicable(body: str) -> bool:
    """Return True when explicit routing heuristics would fit the skill."""
    if _has_classification_structure(body):
        return True
    dispatch_rows = _dispatch_table_rows(body)
    heuristic_markers = [
        "auto-detect", "heuristic", "ambiguous", "complexity", "tier", "classif",
    ]
    return len(dispatch_rows) >= 4 and any(marker in body.lower() for marker in heuristic_markers)


def _has_scaling_structure(body: str) -> bool:
    """Return True when the skill maps scope/size to execution strategy."""
    table_header = re.search(
        r"^\|\s*(scope|size|input size|files?|complexity)\s*\|\s*(strategy|action|execution)\s*\|",
        body,
        re.I | re.M,
    )
    table_rows = re.findall(
        r"^\|\s*(?:[^|\n]*\d[^|\n]*files?[^|\n]*|\d+\s*-\s*\d+(?:\s+\w+)?|\d+\+(?:\s+\w+)?|small|medium|large|trivial)\s*\|",
        body,
        re.I | re.M,
    )
    if table_header and len(table_rows) >= 2:
        return True

    heading_re = r"^#+\s*(scaling\s+strategy|execution\s+strategy|scale\s+by\s+input\s+size)\b"
    section = _extract_heading_section(body, heading_re)
    if not section:
        return False
    threshold_lines = re.findall(
        r"^\s*[-*]\s*(?:\d+\s*-\s*\d+|\d+\+|small|medium|large|trivial)\b.+",
        section,
        re.I | re.M,
    )
    strategy_markers = ["subagent", "parallel", "batch", "team", "delegate"]
    return len(threshold_lines) >= 2 and any(marker in section.lower() for marker in strategy_markers)


def _scaling_applicable(body: str) -> bool:
    """Return True when the skill acknowledges variable-size workloads."""
    if _has_scaling_structure(body):
        return True
    markers = ["subagent", "parallel", "batch", "large input", "multiple files", "many files"]
    return any(marker in body.lower() for marker in markers)


def _has_state_management_structure(body: str) -> bool:
    """Return True when the skill defines a real persistence contract."""
    heading_re = r"^#+\s*(state\s+management|progress|journal|resume)\b"
    section = _extract_heading_section(body, heading_re)
    scope = section or body
    has_state_path = bool(re.search(r"~\/\.\{[^}]+\}\/[a-z0-9._-]+\/", scope))
    has_state_contract = any(
        marker in scope.lower()
        for marker in ["state-dir", "resume", "list", "read/write", "persist", "progress.py", "filename:"]
    )
    return has_state_path and has_state_contract


def _state_management_applicable(body: str, dir_path: Path) -> bool:
    """Return True when the skill exposes resumable or persisted state."""
    if _has_state_management_structure(body):
        return True
    markers = ["dashboard", "resume", "session state", "state-dir", "state file"]
    if any(marker in body.lower() for marker in markers):
        return True
    return (dir_path / "scripts" / "progress.py").is_file()


def _body_substitutions_present(body: str) -> bool:
    """Return True when SKILL.md uses supported body substitutions."""
    return bool(re.search(r"\$(?:ARGUMENTS(?:\[\d+\])?|N|\d+)", body))


def _has_stop_hooks(fm: dict, body: str) -> bool:
    """Return True when Stop hook guidance or config is present."""
    hooks = fm.get("hooks")
    if isinstance(hooks, dict) and any(key in hooks for key in ("Stop", "SubagentStop")):
        return True
    if re.search(r"^#+\s*Stop\s+Hooks?\b", body, re.I | re.M):
        return True
    return "stop_hook_active" in body


def _has_progressive_disclosure_guidance(body: str) -> bool:
    """Return True when the body explicitly describes layered, selective loading."""
    guidance_patterns = [
        r"^#+\s*progressive\s+disclosure\b",
        r"do not load all at once",
        r"load(?:ed)? on demand",
        r"read (?:reference )?files? as indicated",
        r"frontmatter for discovery",
        r"scripts/templates? for execution",
    ]
    return any(re.search(pattern, body, re.I | re.M) for pattern in guidance_patterns)


def _progressive_disclosure_applicable(references_exist: bool, scripts_exist: bool,
                                       templates_exist: bool) -> bool:
    """Return True when the skill has at least one real progressive-disclosure surface."""
    return references_exist or scripts_exist or templates_exist


def _has_progressive_disclosure_structure(body: str, references_exist: bool,
                                          scripts_exist: bool, templates_exist: bool) -> bool:
    """Return True when explicit progressive-disclosure guidance matches real surfaces."""
    if not _progressive_disclosure_applicable(references_exist, scripts_exist, templates_exist):
        return False
    return _has_progressive_disclosure_guidance(body)


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def score_frontmatter(fm: dict, dir_name: str) -> dict:
    """Frontmatter completeness and correctness (0-9, weight 1.0)."""
    s, f = 0, []
    name = fm.get("name", "")
    if name:
        s += 1
        f.append("name field present")
        if KEBAB_RE.match(name):
            s += 1
            f.append("name is valid kebab-case")
        else:
            f.append("name is not valid kebab-case")
        if len(name) <= 64:
            s += 1
        else:
            f.append(f"name exceeds 64 chars ({len(name)})")
        if name == dir_name:
            s += 1
            f.append("name matches directory name")
        else:
            f.append(f"name '{name}' does not match directory '{dir_name}'")
        if "--" in name:
            f.append("name contains consecutive hyphens")
            s = max(s - 1, 0)
        if name.startswith("-") or name.endswith("-"):
            f.append("name has leading/trailing hyphens")
            s = max(s - 1, 0)
        for w in RESERVED_WORDS:
            if w in name.lower():
                f.append(f"name contains reserved word '{w}'")
                s = max(s - 1, 0)
    else:
        f.append("MISSING required field: name")
    desc = fm.get("description", "")
    if desc and str(desc).strip():
        s += 2
        f.append("description field present")
        if re.search(r"<[a-zA-Z][^>]*>", str(desc)):
            f.append("description contains XML/HTML tags")
            s = max(s - 1, 0)
    else:
        f.append("MISSING required field: description")
    if fm.get("license"):
        s += 1
        f.append("license field present")
    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        if meta.get("author"):
            s += 1
            f.append("metadata.author present")
        if meta.get("version"):
            s += 1
            f.append("metadata.version present")
    return {
        "name": "Frontmatter Completeness", "id": "frontmatter",
        "score": min(s, 9), "max": 9, "weight": 1.0, "findings": f,
    }


def score_description(fm: dict) -> dict:
    """Description quality (0-20, weight 2.0)."""
    s, f = 0, []
    desc = str(fm.get("description", "")).strip()
    if not desc:
        f.append("No description to evaluate")
        return {
            "name": "Description Quality", "id": "description",
            "score": 0, "max": 20, "weight": 2.0, "findings": f,
        }
    ln = len(desc)
    if 50 <= ln <= 200:
        s += 6
        f.append(f"Description length optimal ({ln} chars)")
    elif 30 <= ln < 50:
        s += 3
        f.append(f"Description slightly short ({ln} chars)")
    elif 200 < ln <= 300:
        s += 4
        f.append(f"Description slightly long ({ln} chars)")
    elif ln > 300:
        s += 2
        f.append(f"Description too long ({ln} chars, >300)")
    else:
        s += 1
        f.append(f"Description too short ({ln} chars, <30)")
    words = set(re.findall(r"\b[a-z]+\b", desc.lower()))
    verbs = set()
    for w in words:
        if w in ACTION_VERBS:
            verbs.add(w)
        elif w.endswith("s") and w[:-1] in ACTION_VERBS:
            verbs.add(w[:-1])
        elif w.endswith("ing") and w[:-3] in ACTION_VERBS:
            verbs.add(w[:-3])
        elif w.endswith("ed") and w[:-2] in ACTION_VERBS:
            verbs.add(w[:-2])
    if verbs:
        s += 4
        f.append(f"Action verbs found: {', '.join(sorted(verbs)[:5])}")
    else:
        f.append("No action verbs detected")
    dl = desc.lower()
    if "use when" in dl or "use for" in dl:
        s += 3
        f.append("Contains 'Use when/for' trigger clause")
    else:
        f.append("Missing 'Use when/for' trigger clause")
    if "not for" in dl or "not when" in dl:
        s += 3
        f.append("Contains exclusion clause (NOT for)")
    else:
        f.append("Missing exclusion clause (NOT for)")
    first = desc.split()[0].lower() if desc.split() else ""
    if first in ("i", "you", "my", "your", "we"):
        f.append(f"Description starts with '{first}' — prefer third-person voice")
    else:
        s += 4
        f.append("Third-person voice check passed")
    return {
        "name": "Description Quality", "id": "description",
        "score": min(s, 20), "max": 20, "weight": 2.0, "findings": f,
    }


def score_dispatch_table(body: str) -> dict:
    """Dispatch table presence and quality (0-10, weight 1.0)."""
    s, f = 0, []
    table_rows = _dispatch_table_rows(body)
    if not table_rows:
        f.append("No dispatch table with $ARGUMENTS found")
        return {
            "name": "Dispatch Table", "id": "dispatch-table",
            "score": 0, "max": 10, "weight": 1.0, "findings": f,
        }
    s += 4
    f.append("Dispatch table with $ARGUMENTS found")
    rows = len(table_rows)
    if rows >= 3:
        s += 3
        f.append(f"Dispatch table has {rows} rows (>= 3)")
    else:
        s += 1
        f.append(f"Dispatch table has only {rows} rows (< 3)")
    empty_synonyms = {"empty", "no arg", "no args", "none", "blank", "default"}
    if any(any(syn in ln.lower() for syn in empty_synonyms) for ln in table_rows):
        s += 3
        f.append("Empty-args handler row found")
    else:
        f.append("No empty-args handler row in dispatch table")
    return {
        "name": "Dispatch Table", "id": "dispatch-table",
        "score": min(s, 10), "max": 10, "weight": 1.0, "findings": f,
    }


def score_body_structure(body: str) -> dict:
    """Body structure quality (0-15, weight 1.5)."""
    s, f, lines = 0, [], body.splitlines()
    lc = len(lines)
    if lc <= 500:
        s += 4
        f.append(f"Body length acceptable ({lc} lines)")
    else:
        s += 1
        f.append(f"Body too long ({lc} lines, >500)")
    headings = [(len(m.group(1)), m.group(0).strip())
                for line in lines if (m := re.match(r"^(#{1,6})\s+", line))]
    h2 = sum(1 for lv, _ in headings if lv == 2)
    h3 = sum(1 for lv, _ in headings if lv == 3)
    first_h3 = next((i for i, (lv, _) in enumerate(headings) if lv == 3), None)
    first_h4 = next((i for i, (lv, _) in enumerate(headings) if lv == 4), None)
    first_h2 = next((i for i, (lv, _) in enumerate(headings) if lv == 2), None)
    if first_h3 is not None and (first_h2 is None or first_h3 < first_h2):
        f.append("Invalid heading hierarchy: ### appears before any ##")
    elif first_h4 is not None and (first_h2 is None or first_h4 < first_h2):
        f.append("Invalid heading hierarchy: #### appears before any ##")
    elif headings:
        s += 3
        f.append("Heading hierarchy valid")
    else:
        f.append("No headings found in body")
    if h2 >= 3:
        s += 5
        f.append(f"Good section coverage ({h2} ## sections)")
    elif h2 >= 1:
        s += 2
        f.append(f"Limited section coverage ({h2} ## sections, need >= 3)")
    else:
        f.append("No ## sections found")
    if h2 >= 3 and h3 >= 2:
        s += 3
        f.append(f"Good sub-section depth ({h3} ### sub-sections)")
    elif h2 >= 3:
        f.append(f"Limited sub-section depth ({h3} ### sub-sections, need >= 2 for +3 points)")
    return {
        "name": "Body Structure", "id": "body-structure",
        "score": min(s, 15), "max": 15, "weight": 1.5, "findings": f,
    }


def score_pattern_coverage(body: str, dir_path: Path, fm: dict) -> dict:
    """Coverage of applicable skill patterns (0-15, weight 1.5)."""
    f = []
    description = str(fm.get("description", "")).lower()
    dispatch_rows = _dispatch_table_rows(body)
    refs_dir = dir_path / "references"
    scripts_dir = dir_path / "scripts"
    templates_dir = dir_path / "templates"
    hooks_config = fm.get("hooks")
    references_exist = refs_dir.is_dir() and any(p.is_file() for p in refs_dir.iterdir())
    scripts_exist = scripts_dir.is_dir() and bool(list(scripts_dir.glob("*.py")) or list(scripts_dir.glob("*.sh")))
    templates_exist = templates_dir.is_dir() and bool(list(templates_dir.glob("*.html")))
    user_invocable = fm.get("user-invocable", True) is not False

    pattern_status: dict[str, str] = {}

    def set_status(name: str, applicable: bool, found: bool) -> None:
        if found:
            pattern_status[name] = "found"
        elif applicable:
            pattern_status[name] = "suggested"
        else:
            pattern_status[name] = "not-applicable"

    set_status("dispatch-table", user_invocable, bool(dispatch_rows))
    set_status("reference-file-index", references_exist, _has_reference_index(body))
    set_status(
        "critical-rules",
        True,
        bool(re.search(r"^#+\s*critical\s+rules", body, re.I | re.M) and re.findall(r"^\s*\d+[.)]\s+", body, re.M)),
    )
    canonical_applicable = len(dispatch_rows) >= 4 or "mode" in body.lower() or "tier" in body.lower()
    set_status("canonical-vocabulary", canonical_applicable, _has_canonical_vocabulary_section(body))
    set_status("scope-boundaries", True, "not for" in body.lower() or "not for" in description or "not when" in body.lower())
    set_status("classification-gating", _classification_applicable(body), _has_classification_structure(body))
    set_status("scaling-strategy", _scaling_applicable(body), _has_scaling_structure(body))
    set_status("state-management", _state_management_applicable(body, dir_path), _has_state_management_structure(body))
    set_status("scripts", scripts_exist or "scripts/" in body.lower(), scripts_exist)
    set_status("templates", templates_exist or "templates/" in body.lower(), templates_exist)
    hooks_applicable = bool(hooks_config) or "hooks:" in body or re.search(r"^#+\s*hooks\b", body, re.I | re.M)
    set_status("hooks", hooks_applicable, bool("hooks:" in body or hooks_config))
    progressive_applicable = _progressive_disclosure_applicable(
        references_exist, scripts_exist, templates_exist
    )
    progressive_found = _has_progressive_disclosure_structure(
        body, references_exist, scripts_exist, templates_exist
    )
    set_status("progressive-disclosure", progressive_applicable, progressive_found)
    set_status("body-substitutions", user_invocable, _body_substitutions_present(body))
    stop_hooks_applicable = bool(hooks_config) or "stop hook" in body.lower() or "stop_hook_active" in body
    set_status("stop-hooks", stop_hooks_applicable, _has_stop_hooks(fm, body))

    found = [name for name in PATTERN_NAMES if pattern_status[name] == "found"]
    suggested = [name for name in PATTERN_NAMES if pattern_status[name] == "suggested"]
    not_applicable = [name for name in PATTERN_NAMES if pattern_status[name] == "not-applicable"]
    applicable_count = len(found) + len(suggested)
    score = round((len(found) / applicable_count) * 15) if applicable_count else 0

    f.append(f"Patterns found: {len(found)}/{len(PATTERN_NAMES)}")
    f.append(f"Applicable patterns: {applicable_count}/{len(PATTERN_NAMES)}")
    for name in found:
        f.append(f"  [+] {name}")
    if suggested:
        f.append(f"Suggested additions: {', '.join(suggested[:5])}")
    if not_applicable:
        f.append(f"Not applicable: {', '.join(not_applicable[:5])}")
    return {
        "name": "Pattern Coverage",
        "id": "pattern-coverage",
        "score": min(score, 15),
        "max": 15,
        "weight": 1.5,
        "findings": f,
        "_found": found,
        "_suggested": suggested,
        "_not_applicable": not_applicable,
    }


def score_references(dir_path: Path, body: str) -> dict:
    """Reference file management (0-10, weight 1.0)."""
    s, f = 0, []
    rd = dir_path / "references"
    if not rd.is_dir():
        f.append("No references/ directory found")
        return {
            "name": "References", "id": "references",
            "score": 0, "max": 10, "weight": 1.0, "findings": f,
        }
    if any("references/" in ln.lower() and "|" in ln for ln in body.splitlines()):
        s += 3
        f.append("Reference index table found in body")
    else:
        f.append("No reference index table in body")
    on_disk = sorted(p.name for p in rd.iterdir() if p.is_file() and not p.name.startswith("."))
    mentioned = set(re.findall(r"references/([a-zA-Z0-9_.-]+\.md)", body))
    orphans = [n for n in on_disk if n not in mentioned]
    if orphans:
        f.append(f"Orphan reference files: {', '.join(orphans)}")
    else:
        s += 2
        f.append("No orphan reference files")
    missing = [m for m in sorted(mentioned) if m not in on_disk]
    if missing:
        f.append(f"Missing reference files: {', '.join(missing)}")
    else:
        s += 2
        f.append("No missing reference files")
    good = 0
    for name in on_disk:
        txt = _read(rd / name)
        if txt is None:
            continue
        lc = len(txt.splitlines())
        if lc < 50:
            f.append(f"Size warning: {name}: {lc} lines (<50)")
        elif lc > 500:
            f.append(f"Size warning: {name}: {lc} lines (>500)")
        else:
            good += 1
    if good:
        s += min(good, 3)
        f.append(f"{good} reference files with appropriate size")
    return {
        "name": "References", "id": "references",
        "score": min(s, 10), "max": 10, "weight": 1.0, "findings": f,
    }


def score_critical_rules(body: str) -> dict:
    """Critical rules section (0-10, weight 1.0)."""
    s, f = 0, []
    m = re.search(r"^#+\s*Critical\s+Rules", body, re.I | re.M)
    if not m:
        f.append("No 'Critical Rules' section found")
        return {
            "name": "Critical Rules", "id": "critical-rules",
            "score": 0, "max": 10, "weight": 1.0, "findings": f,
        }
    s += 3
    f.append("Critical Rules section found")
    nxt = re.search(r"^#{1,3}\s+", body[m.end():], re.M)
    section = body[m.end():m.end() + nxt.start()] if nxt else body[m.end():]
    items = re.findall(r"^\s*\d+[.)]\s+.+", section, re.M)
    ic = len(items)
    if ic >= 5:
        s += 4
        f.append(f"Has {ic} numbered rules (>= 5)")
    elif ic >= 3:
        s += 2
        f.append(f"Has {ic} numbered rules (3-4, prefer >= 5)")
    elif ic >= 1:
        s += 1
        f.append(f"Has only {ic} numbered rules")
    else:
        f.append("No numbered rules found")
    imperative = ("never", "always", "must", "do not", "ensure", "require",
                  "check", "save", "force", "label", "allow", "flag", "name",
                  "read", "run", "skip", "acknowledge", "apply")
    ac = sum(1 for item in items if any(v in item.lower() for v in imperative))
    if ac >= 3:
        s += 3
        f.append(f"{ac} rules appear actionable")
    elif ac >= 1:
        s += 1
        f.append(f"Only {ac} rules appear actionable")
    else:
        f.append("Rules lack imperative verbs")
    return {
        "name": "Critical Rules", "id": "critical-rules",
        "score": min(s, 10), "max": 10, "weight": 1.0, "findings": f,
    }


def score_scripts(dir_path: Path) -> dict:
    """Scripts directory quality (0-5, weight 0.5)."""
    s, f = 0, []
    sd = dir_path / "scripts"
    if not sd.is_dir():
        f.append("No scripts/ directory (optional)")
        return {
            "name": "Scripts", "id": "scripts",
            "score": 0, "max": 5, "weight": 0.5, "findings": f,
        }
    py = list(sd.glob("*.py"))
    sh = list(sd.glob("*.sh"))
    scripts = py + sh
    if not scripts:
        f.append("scripts/ exists but no .py or .sh files")
        return {
            "name": "Scripts", "id": "scripts",
            "score": 0, "max": 5, "weight": 0.5, "findings": f,
        }
    s += 1
    parts = []
    if py:
        parts.append(f"{len(py)} Python")
    if sh:
        parts.append(f"{len(sh)} Shell")
    f.append(f"Found {' + '.join(parts)} script(s)")
    ap, jo, ds = False, False, False
    for p in py:
        c = _read(p)
        if c is None:
            continue
        if "argparse" in c:
            ap = True
        if "json.dump" in c:
            jo = True
        if '"""' in c[:500] or "'''" in c[:500]:
            ds = True
    # Shell-specific checks: shebang and executable bit
    sh_shebang, sh_exec = False, False
    for p in sh:
        c = _read(p)
        if c is None:
            continue
        if c.startswith("#!"):
            sh_shebang = True
        if p.stat().st_mode & 0o111:
            sh_exec = True
    if sh and sh_shebang:
        f.append("Shell script(s) have shebang line")
    elif sh and not sh_shebang:
        f.append("Shell script(s) missing shebang line")
    if sh and sh_exec:
        f.append("Shell script(s) are executable")
    elif sh and not sh_exec:
        f.append("Shell script(s) missing executable bit")
    if ap:
        s += 1
        f.append("Script(s) use argparse")
    if jo:
        s += 1
        f.append("Script(s) produce JSON output")
    if ds:
        s += 1
        f.append("Script(s) have docstrings")
    if len(scripts) >= 2:
        s += 1
        f.append(f"Multiple scripts ({len(scripts)})")
    return {
        "name": "Scripts", "id": "scripts",
        "score": min(s, 5), "max": 5, "weight": 0.5, "findings": f,
    }


def score_portability(fm: dict, body: str, dir_path: Path) -> dict:
    """Portability for cross-platform distribution (0-5, weight 0.5)."""
    s, f = 0, []
    # +1: license populated
    if fm.get("license"):
        s += 1
        f.append("license field present")
    else:
        f.append("Missing license field")
    # +1: metadata.author populated
    meta = fm.get("metadata", {})
    if isinstance(meta, dict) and meta.get("author"):
        s += 1
        f.append("metadata.author present")
    else:
        f.append("Missing metadata.author")
    # +1: metadata.version populated
    if isinstance(meta, dict) and meta.get("version"):
        s += 1
        f.append("metadata.version present")
    else:
        f.append("Missing metadata.version")
    # +1: no absolute paths in body
    abs_paths = [
        ln for ln in body.splitlines()
        if re.search(r'(?<![a-zA-Z])\/(?:tmp|home|Users|etc|var|opt)\/', ln)
    ]
    if not abs_paths:
        s += 1
        f.append("No absolute paths in body")
    else:
        f.append(f"Absolute paths found in {len(abs_paths)} lines")
    # +1: no repo-specific assumptions (@ imports, hardcoded repo paths)
    # Skip lines inside fenced code blocks (decorators like @mcp.tool are legit)
    in_code = False
    repo_refs = []
    for ln in body.splitlines():
        stripped = ln.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if not in_code and re.match(r'\s*@', ln):
            repo_refs.append(ln)
    if not repo_refs:
        s += 1
        f.append("No repo-specific path assumptions")
    else:
        f.append(f"Repo-specific references found in {len(repo_refs)} lines")
    mentioned = _mentioned_resource_paths(dir_path, body)
    missing_resources = sorted(rel_path for rel_path in mentioned if not (dir_path / rel_path).is_file())
    if missing_resources:
        s = max(s - 1, 0)
        f.append(f"Missing packaged resource references: {', '.join(missing_resources[:5])}")
    elif mentioned:
        f.append(f"All {len(mentioned)} packaged resource references resolve")
    return {
        "name": "Portability", "id": "portability",
        "score": min(s, 5), "max": 5, "weight": 0.5, "findings": f,
    }


def score_conciseness(body: str) -> dict:
    """Body conciseness (0-5, weight 0.5)."""
    s, f, lines = 5, [], body.splitlines()
    headings = [re.match(r"^#{1,6}\s+(.+)", ln).group(1).strip()  # type: ignore[union-attr]
                for ln in lines if re.match(r"^#{1,6}\s+", ln)]
    counts: dict[str, int] = {}
    for h in headings:
        k = h.lower()
        counts[k] = counts.get(k, 0) + 1
    dups = {h: c for h, c in counts.items() if c > 1}
    if dups:
        s -= 2
        for h, c in dups.items():
            f.append(f"Duplicate heading: '{h}' appears {c} times")
    else:
        f.append("No duplicate headings")
    non_empty = [ln.strip() for ln in lines if ln.strip()]
    streak = 1
    for i in range(1, len(non_empty)):
        if non_empty[i] == non_empty[i - 1] and len(non_empty[i]) > 10:
            streak += 1
            if streak >= 3:
                s -= 3
                f.append("Repeated consecutive paragraphs detected")
                break
        else:
            streak = 1
    else:
        f.append("No repeated paragraphs")
    return {"name": "Conciseness", "id": "conciseness", "score": max(s, 0), "max": 5, "weight": 0.5, "findings": f}


def score_canonical_vocabulary(body: str) -> dict:
    """Canonical vocabulary quality (0-5, weight 0.5)."""
    s, f = 0, []
    section = _canonical_vocabulary_section(body)
    if not section:
        f.append("No dedicated canonical vocabulary section found")
        return {
            "name": "Canonical Vocabulary", "id": "canonical-vocabulary",
            "score": 0, "max": 5, "weight": 0.5, "findings": f,
        }
    s += 1
    f.append("Dedicated canonical vocabulary section found")

    if re.search(r"use these exactly|canonical terms|canonical vocabulary", section, re.I):
        s += 1
        f.append("Section marks terms as canonical")
    else:
        f.append("Section does not explicitly mark terms as canonical")

    quoted_terms = re.findall(r'"([^"\n]{2,80})"', section)
    bullet_terms = re.findall(r"^\s*[-*]\s+([^:\n]{2,80})(?::|$)", section, re.M)
    table_terms = re.findall(r"^\|\s*`?([^|`\n]{2,80})`?\s*\|", section, re.M)
    term_count = len({term.strip().lower() for term in quoted_terms + bullet_terms + table_terms})
    if term_count >= 3:
        s += 1
        f.append(f"Defines {term_count} canonical term entries")
    else:
        f.append(f"Defines only {term_count} canonical term entries; prefer >= 3")

    category_lines = re.findall(r"^\s*[-*]\s+[^:\n]{2,80}:\s+.+", section, re.M)
    table_rows = [
        line for line in section.splitlines()
        if line.strip().startswith("|") and not re.match(r"^\|\s*[-:\s|]+\|?$", line.strip())
    ]
    if len(category_lines) >= 2 or len(table_rows) >= 3:
        s += 1
        f.append("Vocabulary is grouped into categories or table rows")
    else:
        f.append("Vocabulary is not grouped into multiple categories")

    if not re.search(r"\b(todo|tbd|placeholder|example term)\b", section, re.I) and len(section.strip()) >= 80:
        s += 1
        f.append("Vocabulary section is non-placeholder content")
    else:
        f.append("Vocabulary section appears placeholder or too thin")

    return {
        "name": "Canonical Vocabulary", "id": "canonical-vocabulary",
        "score": min(s, 5), "max": 5, "weight": 0.5, "findings": f,
    }


def score_evaluation_coverage(dir_path: Path, body: str) -> dict:
    """Eval manifest coverage and quality (0-10, weight 1.0)."""
    s, f = 0, []
    evals_path = dir_path / "evals" / "evals.json"
    if not evals_path.is_file():
        f.append("No evals/evals.json manifest found")
        return {
            "name": "Evaluation Coverage", "id": "evaluation-coverage",
            "score": 0, "max": 10, "weight": 1.0, "findings": f,
        }
    s += 1
    f.append("evals/evals.json manifest found")

    try:
        data = json.loads(evals_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        f.append(f"Eval manifest could not be parsed: {exc}")
        return {
            "name": "Evaluation Coverage", "id": "evaluation-coverage",
            "score": s, "max": 10, "weight": 1.0, "findings": f,
        }

    evals = data.get("evals")
    if isinstance(data, dict) and isinstance(evals, list):
        s += 1
        f.append(f"Eval manifest parses with {len(evals)} case(s)")
    else:
        f.append("Eval manifest must be an object with an evals array")
        evals = []

    if data.get("skill_name") == dir_path.name:
        s += 1
        f.append("skill_name matches directory name")
    else:
        f.append(f"skill_name does not match directory name ({dir_path.name})")

    ids = [case.get("id") for case in evals if isinstance(case, dict)]
    valid_ids = [
        case_id for case_id in ids
        if isinstance(case_id, str) and re.match(r"^[a-z0-9][a-z0-9-]*$", case_id)
    ]
    if len(valid_ids) == len(ids) and len(set(valid_ids)) == len(valid_ids) and valid_ids:
        s += 1
        f.append("Eval ids are stable, unique kebab-case strings")
    else:
        f.append("Eval ids must be present, unique, and kebab-case")

    required_fields = ("id", "prompt", "expected_output")
    cases_with_core = [
        case for case in evals
        if isinstance(case, dict)
        and all(isinstance(case.get(field), str) and case.get(field).strip() for field in required_fields)
    ]
    if evals and len(cases_with_core) == len(evals):
        s += 1
        f.append("All evals include id, prompt, and expected_output")
    else:
        f.append("One or more evals are missing id, prompt, or expected_output")

    cases_with_assertions = [
        case for case in evals
        if isinstance(case, dict)
        and isinstance(case.get("assertions"), list)
        and any(isinstance(item, str) and item.strip() for item in case.get("assertions", []))
    ]
    if evals and len(cases_with_assertions) == len(evals):
        s += 1
        f.append("All evals include objective assertions")
    else:
        f.append("One or more evals lack objective assertions")

    combined = "\n".join(
        " ".join(str(case.get(key, "")) for key in ("id", "prompt", "expected_output", "assertions"))
        for case in evals if isinstance(case, dict)
    ).lower()
    coverage_checks = [
        ("explicit invocation", r"/[a-z0-9-]+\s+\w+|explicit"),
        ("implicit trigger", r"implicit|natural[- ]language|trigger"),
        ("negative control", r"negative[- ]control|should not trigger|does not trigger"),
        ("scope refusal or malformed input", r"scope[- ]refusal|malformed|invalid|refuses?|not for"),
    ]
    for label, pattern in coverage_checks:
        if re.search(pattern, combined):
            s += 1
            f.append(f"Covers {label}")
        else:
            f.append(f"Missing {label} eval coverage")

    actions = _dispatch_action_labels(body)
    if len(actions) >= 4:
        uncovered = []
        for action in actions:
            tokens = [
                tok for tok in re.findall(r"[a-z0-9]+", action)
                if tok not in {"auto", "redirect", "refuse"}
            ]
            if tokens and not all(tok in combined for tok in tokens[:3]):
                uncovered.append(action)
        if uncovered:
            s = max(s - 1, 0)
            f.append(f"Dispatch actions without obvious eval coverage: {', '.join(uncovered[:5])}")
        else:
            f.append("All dispatch actions have obvious eval coverage")

    return {
        "name": "Evaluation Coverage", "id": "evaluation-coverage",
        "score": min(s, 10), "max": 10, "weight": 1.0, "findings": f,
    }


def score_validation_contract(fm: dict, body: str, dir_path: Path) -> dict:
    """Validation proof contract quality (0-10, weight 1.0)."""
    s, f = 0, []
    reference_text = []
    refs_dir = dir_path / "references"
    if refs_dir.is_dir():
        for ref in sorted(refs_dir.glob("*.md")):
            text = _read(ref)
            if text:
                reference_text.append(text)
    corpus = "\n".join([body, *reference_text]).lower()
    has_evals = (dir_path / "evals" / "evals.json").is_file()
    has_hooks = bool(fm.get("hooks"))
    distributable = bool(fm.get("license")) or isinstance(fm.get("metadata"), dict)

    if "wagents validate" in corpus:
        s += 2
        f.append("Validation contract includes wagents validate")
    else:
        f.append("Missing wagents validate proof command")

    if re.search(r"audit\.py\s+skills/(?:<name>|[a-z0-9-]+|.+?)/?", corpus):
        s += 2
        f.append("Validation contract includes audit.py against a skill path")
    else:
        f.append("Missing audit.py skill-path proof command")

    if has_evals:
        if "wagents eval validate" in corpus:
            s += 1
            f.append("Validation contract includes wagents eval validate")
        else:
            f.append("Missing wagents eval validate despite eval manifest")
    else:
        s += 1
        f.append("Eval validation not required because no eval manifest exists")

    if distributable:
        if re.search(r"(wagents package|package\.py).+--dry-run|--dry-run.+(wagents package|package\.py)", corpus):
            s += 1
            f.append("Validation contract includes package dry-run")
        else:
            f.append("Missing package dry-run for distributable skill")
    else:
        s += 1
        f.append("Package dry-run not required for non-distributable skill")

    if has_hooks:
        if "wagents hooks validate" in corpus:
            s += 1
            f.append("Validation contract includes wagents hooks validate")
        else:
            f.append("Missing wagents hooks validate despite hooks config")
    else:
        s += 1
        f.append("Hook validation not required because hooks are not configured")

    legacy_inject_flag = "--" + "inject"
    if legacy_inject_flag not in corpus:
        s += 1
        f.append("No stale legacy progress audit flag found")
    else:
        f.append("Stale legacy progress audit flag found")

    if re.search(r"completion criteria|before declaring|declaring .*complete|must pass|zero errors", corpus):
        s += 1
        f.append("Completion criteria are explicit")
    else:
        f.append("Missing explicit completion criteria")

    if re.search(r"pytest|pnpm|npm test|test(?:s)?\s+pass|smoke", corpus):
        s += 1
        f.append("Validation contract includes a test or smoke-check surface")
    else:
        f.append("Missing test or smoke-check validation surface")

    return {
        "name": "Validation Contract", "id": "validation-contract",
        "score": min(s, 10), "max": 10, "weight": 1.0, "findings": f,
    }


# ---------------------------------------------------------------------------
# Dimension improvement suggestions
# ---------------------------------------------------------------------------

_DIMENSION_SUGGESTIONS: dict[str, list[str]] = {
    "frontmatter": [
        'Add "license" field (e.g., MIT)',
        'Add "metadata.author" field',
        'Add "metadata.version" field',
        "Ensure name matches directory name",
    ],
    "description": [
        'Add "NOT for" clause (+3)',
        'Add "Use when" trigger (+3)',
        "Include action verbs (+4)",
        "Aim for 50-200 chars length (+6)",
    ],
    "dispatch-table": [
        "Add $ARGUMENTS routing table (+4)",
        "Include >= 3 rows (+3)",
        "Add empty-args handler row (+3)",
    ],
    "body-structure": [
        "Add >= 3 ## sections (+5)",
        "Add >= 2 ### sub-sections (+3)",
        "Keep body <= 500 lines (+4)",
    ],
    "pattern-coverage": [
        "Add missing applicable patterns or mark them out of scope in the skill design",
    ],
    "references": [
        "Create references/ directory with index table (+3)",
        "Ensure no orphan or missing reference files (+4)",
    ],
    "critical-rules": [
        'Add "Critical Rules" heading (+3)',
        "Include >= 5 numbered rules (+4)",
        "Use imperative verbs in rules (+3)",
    ],
    "scripts": [
        "Add scripts/ directory with .py files (+1)",
        "Use argparse in scripts (+1)",
        "Add JSON output with json.dump (+1)",
    ],
    "portability": [
        "Add license field (+1)",
        "Add metadata.author (+1)",
        "Add metadata.version (+1)",
        "Remove absolute paths from body (+1)",
        "Remove @ import references (+1)",
    ],
    "conciseness": [
        "Remove duplicate headings (+2)",
        "Remove repeated content blocks (+3)",
    ],
    "canonical-vocabulary": [
        "Add a dedicated Canonical Vocabulary section",
        "Define >= 3 exact terms",
        'Include "use these exactly" guidance',
    ],
    "evaluation-coverage": [
        "Add evals/evals.json with stable case ids",
        "Cover explicit invocation, implicit trigger, and negative control cases",
        "Add scope-refusal or malformed-input coverage",
    ],
    "validation-contract": [
        "Add wagents validate and audit.py proof commands",
        "Add wagents eval validate when evals exist",
        "Add package dry-run and hooks validation where applicable",
    ],
}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def audit_skill(path: str) -> dict:
    """Audit a single skill directory and return a scored report."""
    try:
        dp = Path(path).resolve()
        skill_md = dp / "SKILL.md"
        empty = {
            "skill": dp.name, "path": str(dp) + "/", "score": 0, "max": 100,
            "grade": "F", "dimensions": [], "bonus": 0, "patterns_found": [],
            "patterns_suggested": PATTERN_NAMES[:],
            "patterns_not_applicable": [],
            "meta": {"lines": 0, "refs": 0, "scripts": 0},
        }
        if not skill_md.is_file():
            _warn(f"SKILL.md not found in {dp}")
            return {**empty, "error": "SKILL.md not found"}
        content = _read(skill_md)
        if content is None:
            _warn(f"Cannot read {skill_md}")
            return {**empty, "error": "Cannot read SKILL.md"}

        fm, body = parse_frontmatter(content)
        dims = [
            score_frontmatter(fm, dp.name),
            score_description(fm),
            score_dispatch_table(body),
            score_body_structure(body),
            score_pattern_coverage(body, dp, fm),
            score_references(dp, body),
            score_critical_rules(body),
            score_scripts(dp),
            score_portability(fm, body, dp),
            score_conciseness(body),
            score_canonical_vocabulary(body),
            score_evaluation_coverage(dp, body),
            score_validation_contract(fm, body, dp),
        ]
        tw = sum(d["score"] * d["weight"] for d in dims)
        mw = sum(d["max"] * d["weight"] for d in dims)
        norm = (tw / mw * 100) if mw > 0 else 0
        final = max(0, min(round(norm), 100))
        pf = dims[4].pop("_found", [])
        ps = dims[4].pop("_suggested", [])
        pna = dims[4].pop("_not_applicable", [])
        rd = dp / "references"
        sd = dp / "scripts"
        return {
            "skill": dp.name, "path": str(dp) + "/", "score": final, "max": 100,
            "grade": _grade(final), "dimensions": dims, "bonus": 0,
            "patterns_found": pf, "patterns_suggested": ps, "patterns_not_applicable": pna,
            "meta": {
                "lines": len(body.splitlines()),
                "refs": len([
                    p for p in rd.iterdir()
                    if p.is_file() and not p.name.startswith(".")
                ]) if rd.is_dir() else 0,
                "scripts": len(list(sd.glob("*.py"))) if sd.is_dir() else 0,
            },
        }
    except Exception as exc:
        return {
            "skill": Path(path).resolve().name,
            "path": str(Path(path).resolve()) + "/",
            "score": 0, "max": 100, "grade": "F",
            "dimensions": [], "bonus": 0,
            "patterns_found": [], "patterns_suggested": PATTERN_NAMES[:], "patterns_not_applicable": [],
            "meta": {"lines": 0, "refs": 0, "scripts": 0},
            "error": str(exc),
        }


def audit_all(skills_dir: str) -> list[dict]:
    """Audit all skills and return comparative rankings sorted by score."""
    sp = Path(skills_dir).resolve()
    if not sp.is_dir():
        _warn(f"Skills directory not found: {sp}")
        return []
    results = [
        audit_skill(str(d)) for d in sorted(sp.iterdir())
        if d.is_dir() and (d / "SKILL.md").is_file()
    ]
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Table formatters (plain text)
# ---------------------------------------------------------------------------

def format_table(results: list[dict]) -> str:
    """Format audit results as a human-readable summary table."""
    out = ["Skill Quality Report", "=" * 20, ""]
    hdr = f"{'Skill':<22} {'Score':>7}  {'Grade':>5}  {'Lines':>5}  {'Refs':>4}  {'Scripts':>7}  {'Patterns':>8}"
    out.append(hdr)
    out.append("\u2500" * len(hdr))
    for r in results:
        m = r.get("meta", {})
        pc = len(r.get("patterns_found", []))
        applicable = pc + len(r.get("patterns_suggested", []))
        sc = f"{r['score']}/{r['max']}"
        out.append(
            f"{r['skill']:<22} {sc:>7}  {r['grade']:>5}  "
            f"{m.get('lines', 0):>5}  {m.get('refs', 0):>4}  "
            f"{m.get('scripts', 0):>7}  {pc:>3}/{applicable:<3}"
        )
    out.append("")
    out.append(f"Total skills audited: {len(results)}")
    if results:
        out.append(f"Average score: {sum(r['score'] for r in results) / len(results):.1f}")
    return "\n".join(out)


def format_single_table(result: dict) -> str:
    """Format a single audit result as a detailed table."""
    grade = result["grade"]
    status = GRADE_STATUS.get(grade, "")
    out = [f"Skill Audit: {result['skill']}", "=" * 40]
    out.append(f"Score: {result['score']}/{result['max']}  Grade: {grade}  ({status})")
    if result.get("error"):
        out.append(f"Error: {result['error']}")
        return "\n".join(out)
    out.append("")
    out.append(f"{'Dimension':<28} {'Score':>7}  {'Wt':>4}  {'Weighted':>14}")
    out.append("\u2500" * 58)
    for d in result.get("dimensions", []):
        weighted_score = d["score"] * d["weight"]
        weighted_max = d["max"] * d["weight"]
        out.append(
            f"{d['name']:<28} {d['score']:>2}/{d['max']:<3}  "
            f"\u00d7{d['weight']:<3.1f}  "
            f"\u2192  {weighted_score:>5.1f}/{weighted_max:.1f}"
        )
        for finding in d.get("findings", []):
            out.append(f"  {finding}")
        # Per-dimension improvement suggestions for non-perfect scores
        if d["score"] < d["max"]:
            suggestions = _DIMENSION_SUGGESTIONS.get(d["id"], [])
            if suggestions:
                tips = ", ".join(suggestions[:3])
                out.append(f"  \u2192 {tips}")
    out.append("")
    m = result.get("meta", {})
    out.append(f"Lines: {m.get('lines', 0)}  Refs: {m.get('refs', 0)}  Scripts: {m.get('scripts', 0)}")
    pf = result.get("patterns_found", [])
    ps = result.get("patterns_suggested", [])
    pna = result.get("patterns_not_applicable", [])
    out.append(f"Patterns: {len(pf)}/{len(pf) + len(ps)} applicable ({len(PATTERN_NAMES)} in catalog)")
    if pf:
        out.append(f"  Found: {', '.join(pf)}")
    if ps:
        out.append(f"  Suggested: {', '.join(ps[:5])}")
    if pna:
        out.append(f"  Not applicable: {', '.join(pna[:5])}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Rich formatters (colored terminal output)
# ---------------------------------------------------------------------------

def _score_color(score: int, max_score: int) -> str:
    """Return a Rich color name based on score ratio."""
    if max_score == 0:
        return "white"
    ratio = score / max_score
    if ratio >= 0.9:
        return "green"
    if ratio >= 0.7:
        return "cyan"
    if ratio >= 0.5:
        return "yellow"
    return "red"


def _score_bar(score: int, max_score: int, width: int = 10) -> str:
    """Return a text-based bar representing the score."""
    if max_score == 0:
        return " " * width
    filled = round(score / max_score * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def format_rich_single(result: dict) -> None:
    """Format a single audit result using Rich for colored terminal output."""
    console = Console()
    grade = result["grade"]
    status = GRADE_STATUS.get(grade, "")
    grade_color = GRADE_COLORS.get(grade, "white")

    # Header panel
    title_text = Text()
    title_text.append(f"Skill Audit: {result['skill']}  ", style="bold")
    title_text.append(f"Grade: {grade}", style=f"bold {grade_color}")
    title_text.append(f"  ({status})", style=grade_color)
    title_text.append(f"  Score: {result['score']}/{result['max']}")
    console.print(Panel(title_text, border_style=grade_color))

    if result.get("error"):
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    # Dimension table
    table = RichTable(title="Scoring Dimensions", show_lines=False)
    table.add_column("Dimension", style="bold", min_width=26)
    table.add_column("Score", justify="right", min_width=7)
    table.add_column("Bar", min_width=12)
    table.add_column("Wt", justify="right", min_width=4)
    table.add_column("Weighted", justify="right", min_width=14)

    for d in result.get("dimensions", []):
        color = _score_color(d["score"], d["max"])
        bar = _score_bar(d["score"], d["max"])
        weighted_score = d["score"] * d["weight"]
        weighted_max = d["max"] * d["weight"]
        table.add_row(
            d["name"],
            f"[{color}]{d['score']}/{d['max']}[/{color}]",
            f"[{color}]{bar}[/{color}]",
            f"\u00d7{d['weight']:.1f}",
            f"[{color}]{weighted_score:.1f}/{weighted_max:.1f}[/{color}]",
        )

    console.print(table)

    # Findings and suggestions
    for d in result.get("dimensions", []):
        if d.get("findings"):
            console.print(f"\n[bold]{d['name']}[/bold]")
            for finding in d["findings"]:
                if finding.startswith("  [+]"):
                    console.print(f"  [green]\u2713[/green] {finding.strip().lstrip('[+] ')}")
                elif "MISSING" in finding or "No " in finding[:4]:
                    console.print(f"  [red]\u2717[/red] {finding}")
                else:
                    console.print(f"  [dim]\u2022[/dim] {finding}")
            if d["score"] < d["max"]:
                suggestions = _DIMENSION_SUGGESTIONS.get(d["id"], [])
                if suggestions:
                    tips = ", ".join(suggestions[:3])
                    console.print(f"  [yellow]\u2192 {tips}[/yellow]")

    # Pattern coverage
    console.print()
    pf = result.get("patterns_found", [])
    ps = result.get("patterns_suggested", [])
    pna = result.get("patterns_not_applicable", [])
    patterns_text = Text("Patterns: ")
    patterns_text.append(f"{len(pf)}/{len(pf) + len(ps)} applicable", style="bold")
    patterns_text.append(f"  ({len(PATTERN_NAMES)} in catalog)", style="dim")
    console.print(patterns_text)
    for p in PATTERN_NAMES:
        if p in pf:
            console.print(f"  [green]\u2713[/green] {p}")
        elif p in pna:
            console.print(f"  [dim]-[/dim] {p} [dim](not applicable)[/dim]")
        else:
            console.print(f"  [red]\u2717[/red] {p}")

    # Meta
    m = result.get("meta", {})
    console.print(f"\nLines: {m.get('lines', 0)}  Refs: {m.get('refs', 0)}  Scripts: {m.get('scripts', 0)}")


def format_rich_table(results: list[dict]) -> None:
    """Format audit results as a Rich table for colored terminal output."""
    console = Console()
    console.print("[bold]Skill Quality Report[/bold]\n")

    table = RichTable(show_lines=False)
    table.add_column("Skill", style="bold", min_width=22)
    table.add_column("Score", justify="right", min_width=7)
    table.add_column("Grade", justify="center", min_width=5)
    table.add_column("Status", min_width=16)
    table.add_column("Lines", justify="right", min_width=5)
    table.add_column("Refs", justify="right", min_width=4)
    table.add_column("Scripts", justify="right", min_width=7)
    table.add_column("Patterns", justify="right", min_width=8)

    for r in results:
        m = r.get("meta", {})
        pc = len(r.get("patterns_found", []))
        applicable = pc + len(r.get("patterns_suggested", []))
        grade = r["grade"]
        grade_color = GRADE_COLORS.get(grade, "white")
        status = GRADE_STATUS.get(grade, "")
        table.add_row(
            r["skill"],
            f"{r['score']}/{r['max']}",
            f"[{grade_color}]{grade}[/{grade_color}]",
            f"[{grade_color}]{status}[/{grade_color}]",
            str(m.get("lines", 0)),
            str(m.get("refs", 0)),
            str(m.get("scripts", 0)),
            f"{pc}/{applicable}",
        )

    console.print(table)
    console.print(f"\nTotal skills audited: {len(results)}")
    if results:
        avg = sum(r["score"] for r in results) / len(results)
        console.print(f"Average score: {avg:.1f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Audit skill quality")
    parser.add_argument("path", nargs="?", help="Path to skill directory")
    parser.add_argument("--all", action="store_true", help="Audit all skills")
    parser.add_argument("--format", choices=["json", "table"], default="json",
                        dest="output_format")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 1 if any skill scores below B (75)")
    args = parser.parse_args()

    if not args.path and not args.all:
        parser.error("Provide a skill path or use --all")

    if args.path and args.all:
        parser.error("Cannot use both a path and --all; choose one")

    if args.all:
        script_dir = Path(__file__).resolve().parent
        skills_dir = script_dir.parent.parent  # skills/skill-creator/scripts -> skills/
        if not skills_dir.is_dir():
            skills_dir = Path.cwd() / "skills"
        results = audit_all(str(skills_dir))
        if args.output_format == "table":
            if _RICH and sys.stdout.isatty():
                format_rich_table(results)
            else:
                print(format_table(results))
        else:
            json.dump(results, sys.stdout, indent=2)
            sys.stdout.write("\n")
        if args.strict:
            failing = [r for r in results if r["score"] < 75]
            if failing:
                names = ", ".join(r["skill"] for r in failing)
                _warn(f"Strict mode: {len(failing)} skill(s) below B (75): {names}")
                sys.exit(1)
    else:
        result = audit_skill(args.path)
        if args.output_format == "table":
            if _RICH and sys.stdout.isatty():
                format_rich_single(result)
            else:
                print(format_single_table(result))
        else:
            json.dump(result, sys.stdout, indent=2)
            sys.stdout.write("\n")
        if args.strict and result["score"] < 75:
            _warn(f"Strict mode: {result['skill']} scored {result['score']} (below B threshold of 75)")
            sys.exit(1)


if __name__ == "__main__":
    main()
